"""
tests/test_turbine_bp.py
========================

Tests unitaires de la classe TurbineBP.

Notations conformes au Rapport Relaxation 3NC (§5.4.5, §5.6.5, Table 5) :
    P_{2e,TB}  : pression entrée corps TB
    ṁ_{2e,TB}  : débit massique vapeur entrée corps TB
    C_{TB}     : couple mécanique corps TB
    Ω_{TB}     : ouverture relative vanne TB
    T_{Ω,BP}   : constante de temps fermeture vanne TB (= 0.1 s)
    T_{Ω,HP}   : constante de temps fermeture vanne TH (= 0.5 s)

Méthode : on instancie une turbine BP avec les paramètres nominaux de Paluel,
on lui donne des entrées nominales, et on vérifie que les sorties ont des
propriétés physiques correctes (ordres de grandeur et signes).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Equipements.turbine_bp import TurbineBP

# --- Entrées nominales standard (Rapport §5.7, Table 3) ---
ENTREES_NOMINALES = {
    'P_2e_TB':  1.2e6,   # P_{2e,TB} — pression nominale entrée corps TB  (Pa)
    'accel_TB': False,   # accéléromètre non déclenché
}


def test_tb_debit_positif_au_nominal():
    """Au régime nominal, le débit ṁ_{2e,TB} doit être strictement positif."""
    tb = TurbineBP('TB')
    s = tb.step(0.05, ENTREES_NOMINALES)
    assert s['m_dot_2e_TB'] > 0, \
        f"m_dot_2e_TB devrait être positif : {s['m_dot_2e_TB']:.1f} kg/s"


def test_tb_couple_positif_au_nominal():
    """Au régime nominal, le couple C_{TB} doit être strictement positif."""
    tb = TurbineBP('TB')
    s = tb.step(0.05, ENTREES_NOMINALES)
    assert s['C_TB'] > 0, \
        f"C_TB devrait être positif : {s['C_TB']:.3e} N·m"


def test_tb_vanne_ouverte_sans_accel():
    """Sans accéléromètre, Ω_{TB} doit rester à pleine ouverture (1.0)."""
    tb = TurbineBP('TB')
    s = tb.step(0.05, ENTREES_NOMINALES)
    assert s['Omega_TB'] == 1.0, \
        f"Omega_TB devrait être 1.0 sans accéléromètre : {s['Omega_TB']:.4f}"


def test_tb_accel_ferme_vanne():
    """En mode accéléromètre, Ω_{TB} doit se fermer progressivement."""
    tb = TurbineBP('TB')
    entrees_accel = dict(ENTREES_NOMINALES)
    entrees_accel['accel_TB'] = True
    Omega_initial = tb.Omega_TB
    for _ in range(50):
        tb.step(0.05, entrees_accel)
    assert tb.Omega_TB < Omega_initial, \
        "L'accéléromètre TB devrait fermer Ω_{TB} (doit baisser)"
    assert tb.Omega_TB >= 0.0, \
        "Ω_{TB} ne doit pas devenir négatif"


def test_tb_accel_plus_rapide_que_th():
    """La fermeture vanne TB (T_{Ω,BP}=0.1s) doit être plus rapide que TH (T_{Ω,HP}=0.5s).

    Rapport Table 5 : T_{Ω,BP} = 0.1 s < T_{Ω,HP} = 0.5 s.
    Après 0.5 s (10 pas de 0.05 s), Ω_{TB} doit être plus fermé que Ω_{TH}.
    """
    from Equipements.turbine_hp import TurbineHP

    tb = TurbineBP('TB')
    th = TurbineHP('TH')

    entrees_accel_tb = dict(ENTREES_NOMINALES)
    entrees_accel_tb['accel_TB'] = True

    entrees_accel_th = {
        'm_dot_2e_TB': 1500.0, 'Omega_D': 0.0, 'N': 1500.0,
        'Q_e': 1300e6, 'Q_ec': 1300e6, 'accel_TH': True,
    }

    # 10 pas de 0.05 s = 0.5 s
    for _ in range(10):
        tb.step(0.05, entrees_accel_tb)
        th.step(0.05, entrees_accel_th)

    assert tb.Omega_TB < th.Omega_TH, \
        "Ω_{TB} (T_{Ω,BP}=0.1s) devrait être plus fermé que Ω_{TH} (T_{Ω,HP}=0.5s) après 0.5s"


def test_tb_pression_nulle_donne_debit_nul():
    """Si P_{2e,TB} = 0, le débit ṁ_{2e,TB} doit être nul."""
    tb = TurbineBP('TB')
    entrees_p0 = dict(ENTREES_NOMINALES)
    entrees_p0['P_2e_TB'] = 0.0
    s = tb.step(0.05, entrees_p0)
    assert s['m_dot_2e_TB'] == 0.0, \
        f"m_dot_2e_TB devrait être nul si P_2e_TB = 0 : {s['m_dot_2e_TB']:.3f}"


def test_tb_debit_proportionnel_pression():
    """Le débit ṁ_{2e,TB} doit augmenter quand P_{2e,TB} augmente (Ω_{TB} = 1)."""
    tb_bas  = TurbineBP('TB_bas')
    tb_haut = TurbineBP('TB_haut')

    entrees_bas  = dict(ENTREES_NOMINALES); entrees_bas['P_2e_TB']  = 0.8e6
    entrees_haut = dict(ENTREES_NOMINALES); entrees_haut['P_2e_TB'] = 1.6e6

    s_bas  = tb_bas.step(0.05, entrees_bas)
    s_haut = tb_haut.step(0.05, entrees_haut)

    assert s_haut['m_dot_2e_TB'] > s_bas['m_dot_2e_TB'], \
        "ṁ_{2e,TB} doit être plus élevé à P_{2e,TB} plus haute"


def test_tb_ne_diverge_pas():
    """Après 200 pas au nominal, l'état reste dans des valeurs physiques."""
    tb = TurbineBP('TB')
    for _ in range(200):
        tb.step(0.05, ENTREES_NOMINALES)
    etat = tb.get_state()
    assert etat['C_TB'] > 0, \
        f"C_TB devrait rester positif : {etat['C_TB']:.3e} N·m"
    assert etat['m_dot_2e_TB'] > 0, \
        f"m_dot_2e_TB devrait rester positif : {etat['m_dot_2e_TB']:.1f} kg/s"
    assert 0.0 <= etat['Omega_TB'] <= 1.0, \
        f"Omega_TB hors plage [0,1] : {etat['Omega_TB']:.4f}"


def test_tb_reouverture_apres_accel():
    """Après accéléromètre, Ω_{TB} doit revenir à 1.0 dès que accel_TB repasse False."""
    tb = TurbineBP('TB')

    # Phase fermeture : 20 pas avec accéléromètre
    entrees_accel = dict(ENTREES_NOMINALES); entrees_accel['accel_TB'] = True
    for _ in range(20):
        tb.step(0.05, entrees_accel)
    assert tb.Omega_TB < 1.0, "Ω_{TB} devrait s'être partiellement fermé"

    # Phase réouverture : 1 seul pas sans accéléromètre → doit repasser à 1.0
    s = tb.step(0.05, ENTREES_NOMINALES)
    assert s['Omega_TB'] == 1.0, \
        "Sans accéléromètre, Ω_{TB} doit immédiatement revenir à 1.0 (H6)"


# --- Lancement manuel si on n'utilise pas pytest ---
if __name__ == '__main__':
    test_tb_debit_positif_au_nominal()
    print("✓ test_tb_debit_positif_au_nominal")
    test_tb_couple_positif_au_nominal()
    print("✓ test_tb_couple_positif_au_nominal")
    test_tb_vanne_ouverte_sans_accel()
    print("✓ test_tb_vanne_ouverte_sans_accel")
    test_tb_accel_ferme_vanne()
    print("✓ test_tb_accel_ferme_vanne")
    test_tb_accel_plus_rapide_que_th()
    print("✓ test_tb_accel_plus_rapide_que_th")
    test_tb_pression_nulle_donne_debit_nul()
    print("✓ test_tb_pression_nulle_donne_debit_nul")
    test_tb_debit_proportionnel_pression()
    print("✓ test_tb_debit_proportionnel_pression")
    test_tb_ne_diverge_pas()
    print("✓ test_tb_ne_diverge_pas")
    test_tb_reouverture_apres_accel()
    print("✓ test_tb_reouverture_apres_accel")
    print("\nTous les tests de la turbine BP passent.")
