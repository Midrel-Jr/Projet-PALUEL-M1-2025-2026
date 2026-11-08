"""
tests/test_turbine_hp.py
========================
Tests unitaires de la classe TurbineHP.
Méthode : on instancie une turbine HP avec les paramètres nominaux de Paluel,
on lui donne des entrées nominales, et on vérifie que les sorties
ont des propriétés physiques correctes (pas des valeurs exactes,
juste les ordres de grandeur et les signes).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Equipements.turbine_hp import TurbineHP

# --- Entrées nominales standard (réutilisées dans tous les tests) ---
ENTREES_NOMINALES = {
    'm_dot_2e_TB': 1500.0,    # débit entrant corps TB        [kg/s]  -- égal au débit nominal TH
    'Omega_D':     0.0,        # vanne dump fermée             [-]
    'N':           1500.0,     # vitesse nominale              [tr/min]
    'Q_e':         1300e6,     # puissance élec. nominale      [W]
    'Q_ec':        1300e6,     # consigne puissance nominale   [W]
    'accel_TH':    False,      # accéléromètre non déclenché
}


def test_th_debit_positif_au_nominal():
    """Au régime nominal, le débit vapeur entrant corps TH doit être positif."""
    th = TurbineHP('th1')
    s = th.step(0.05, ENTREES_NOMINALES)
    assert s['m_dot_2e_TH'] > 0, \
        f"m_dot_2e_TH devrait être positif, valeur : {s['m_dot_2e_TH']:.1f}"


def test_th_couple_positif_au_nominal():
    """Au régime nominal, le couple corps TH doit être strictement positif."""
    th = TurbineHP('th1')
    s = th.step(0.05, ENTREES_NOMINALES)
    assert s['C_TH'] > 0, \
        f"C_TH devrait être positif, valeur : {s['C_TH']:.3e}"


def test_th_pression_nominale():
    """À l'équilibre, la pression P_2s_gv doit rester proche de la valeur nominale (6.9 MPa)."""
    th = TurbineHP('th1')
    # On converge vers l'équilibre en 200 pas
    for _ in range(200):
        th.step(0.05, ENTREES_NOMINALES)
    etat = th.get_state()
    assert 3e6 < etat['P_2s_gv'] < 15e6, \
        f"P_2s_gv hors plage physique : {etat['P_2s_gv']:.3e} Pa"


def test_th_vanne_ouverte_au_nominal():
    """Sans accéléromètre et à la puissance consigne, la vanne TH doit rester à 1."""
    th = TurbineHP('th1')
    s = th.step(0.05, ENTREES_NOMINALES)
    # Au nominal Q_e == Q_ec et N == N0 → écarts nuls → Omega_TH stable à 1.0
    assert 0.9 <= s['Omega_TH'] <= 1.0, \
        f"Omega_TH devrait être proche de 1 au nominal : {s['Omega_TH']:.4f}"


def test_th_accel_ferme_vanne():
    """En mode accéléromètre, la vanne TH doit se fermer progressivement (eq. 39)."""
    th = TurbineHP('th1')
    entrees_accel = dict(ENTREES_NOMINALES)
    entrees_accel['accel_TH'] = True
    omega_initial = th.Omega_TH
    for _ in range(50):
        th.step(0.05, entrees_accel)
    assert th.Omega_TH < omega_initial, \
        "L'accéléromètre TH devrait fermer la vanne (Omega_TH doit baisser)"
    assert th.Omega_TH >= 0.0, \
        "Omega_TH ne doit pas devenir négatif"


def test_th_dump_ferme_sans_consigne():
    """Sans consigne dump (Omega_D = 0), le débit de contournement doit être nul."""
    th = TurbineHP('th1')
    s = th.step(0.05, ENTREES_NOMINALES)
    assert s['m_dot_2e_D'] == 0.0, \
        f"m_dot_2e_D devrait être nul sans ouverture dump : {s['m_dot_2e_D']:.1f}"


def test_th_dump_ouvert_augmente_debit_total():
    """Avec dump ouvert, le débit total au surchauffeur m_dot_2s_gv doit augmenter."""
    th_ref  = TurbineHP('th_ref')
    th_dump = TurbineHP('th_dump')

    entrees_dump = dict(ENTREES_NOMINALES)
    entrees_dump['Omega_D'] = 0.5   # 50% d'ouverture dump

    s_ref  = th_ref.step(0.05, ENTREES_NOMINALES)
    s_dump = th_dump.step(0.05, entrees_dump)

    assert s_dump['m_dot_2s_gv'] > s_ref['m_dot_2s_gv'], \
        "Avec dump ouvert, m_dot_2s_gv devrait être supérieur au cas sans dump"


def test_th_ne_diverge_pas():
    """Après 200 pas au nominal, l'état reste dans des valeurs physiques."""
    th = TurbineHP('th1')
    for _ in range(200):
        th.step(0.05, ENTREES_NOMINALES)
    etat = th.get_state()
    assert 1e6 < etat['P_2s_gv'] < 20e6, \
        f"P_2s_gv hors plage physique : {etat['P_2s_gv']:.3e} Pa"
    assert etat['C_TH'] > 0, \
        f"C_TH devrait rester positif : {etat['C_TH']:.3e} N·m"
    assert 0.0 <= etat['Omega_TH'] <= 1.0, \
        f"Omega_TH hors plage [0,1] : {etat['Omega_TH']:.4f}"


def test_th_souspuissance_ferme_vanne():
    """Si Q_e < Q_ec (sous-puissance), la régulation doit fermer la vanne TH.

    Convention (eq. 29) :
        Omega_TH_dot = K_reg · [(Q_e - Q_ec) + écart_vitesse]
    Si Q_e < Q_ec  →  (Q_e - Q_ec) < 0  →  dOmega/dt < 0  →  fermeture.
    """
    th = TurbineHP('th1')
    entrees_sous = dict(ENTREES_NOMINALES)
    entrees_sous['Q_e']  = 1200e6   # 100 MW de moins que la consigne
    entrees_sous['Q_ec'] = 1300e6
    omega_initial = th.Omega_TH
    for _ in range(20):
        th.step(0.05, entrees_sous)
    assert th.Omega_TH < omega_initial, \
        "Une sous-puissance devrait faire fermer la vanne TH par la régulation"


# --- Lancement manuel si on n'utilise pas pytest ---
if __name__ == '__main__':
    test_th_debit_positif_au_nominal()
    print("✓ test_th_debit_positif_au_nominal")
    test_th_couple_positif_au_nominal()
    print("✓ test_th_couple_positif_au_nominal")
    test_th_pression_nominale()
    print("✓ test_th_pression_nominale")
    test_th_vanne_ouverte_au_nominal()
    print("✓ test_th_vanne_ouverte_au_nominal")
    test_th_accel_ferme_vanne()
    print("✓ test_th_accel_ferme_vanne")
    test_th_dump_ferme_sans_consigne()
    print("✓ test_th_dump_ferme_sans_consigne")
    test_th_dump_ouvert_augmente_debit_total()
    print("✓ test_th_dump_ouvert_augmente_debit_total")
    test_th_ne_diverge_pas()
    print("✓ test_th_ne_diverge_pas")
    test_th_souspuissance_ferme_vanne()
    print("✓ test_th_souspuissance_ferme_vanne")
    print("\nTous les tests de la turbine HP passent.")
