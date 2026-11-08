"""
tests/test_pressuriseur.py
==========================

Tests unitaires de la classe Pressuriseur.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Equipements.pressuriseur import Pressuriseur


# --- Entrées nominales standard ---
ENTREES_NOMINALES = {
    'h_1s_c': 1.55e6,   # enthalpie branche chaude (sortie cœur) -- J/kg
    'P_1s_c': 154.5e5,  # pression branche chaude -- Pa
    'h_1e_c': 1.40e6,   # enthalpie branche froide (pour spray) -- J/kg
}


def test_pressuriseur_pression_initiale():
    """A la création, la pression doit être à la valeur nominale 155 bar."""
    pr = Pressuriseur('press1', V_press=40.0, S_press=0.05, H_press=10.0)
    assert abs(pr.P_press - 155e5) < 1e3, \
        f"Pression initiale incorrecte : {pr.P_press:.3e} Pa"


def test_pressuriseur_volume_conservation():
    """Le volume total (liquide + vapeur) doit rester constant."""
    pr = Pressuriseur('press1', V_press=40.0, S_press=0.05, H_press=10.0)
    pr.step(0.05, ENTREES_NOMINALES)

    V_total = pr.V_L + (pr.V_press - pr.V_L)
    assert abs(V_total - pr.V_press) < 1e-6, \
        "Volume total non conservé"


def test_pressuriseur_actionneurs_au_nominal():
    """Au nominal (P proche de 155 bar), spray et soupape doivent être inactifs."""
    pr = Pressuriseur('press1', V_press=40.0, S_press=0.05, H_press=10.0)
    pr.step(0.05, ENTREES_NOMINALES)

    assert pr.m_sp == 0.0, "Spray ne devrait pas être actif au nominal"
    assert pr.m_sv == 0.0, "Soupape ne devrait pas être ouverte au nominal"


def test_pressuriseur_ne_diverge_pas():
    """Après 200 pas au nominal, l'état reste physique."""
    pr = Pressuriseur('press1', V_press=40.0, S_press=0.05, H_press=10.0)
    for _ in range(200):
        pr.step(0.05, ENTREES_NOMINALES)

    etat = pr.get_state()
    assert 100e5 < etat['P_press'] < 200e5, \
        f"P_press hors plage physique : {etat['P_press']:.3e}"
    assert 0 < etat['V_L'] < pr.V_press, \
        f"V_L hors plage physique : {etat['V_L']:.3e}"


def test_pressuriseur_resistances_actives_si_basse_pression():
    """Si on force P_press en dessous de la consigne, les résistances chauffent."""
    pr = Pressuriseur('press1', V_press=40.0, S_press=0.05, H_press=10.0)
    pr.P_press = 150e5   # on force 150 bar (5 bar en dessous de la consigne 155)

    pr.step(0.05, ENTREES_NOMINALES)

    assert pr.Q_res > 0.5 * pr.Q_res_max, \
        f"Résistances devraient chauffer fort : Q_res = {pr.Q_res:.2e}"


# --- Lancement manuel ---
if __name__ == '__main__':
    test_pressuriseur_pression_initiale()
    print("✓ test_pressuriseur_pression_initiale")
    test_pressuriseur_volume_conservation()
    print("✓ test_pressuriseur_volume_conservation")
    test_pressuriseur_actionneurs_au_nominal()
    print("✓ test_pressuriseur_actionneurs_au_nominal")
    test_pressuriseur_ne_diverge_pas()
    print("✓ test_pressuriseur_ne_diverge_pas")
    test_pressuriseur_resistances_actives_si_basse_pression()
    print("✓ test_pressuriseur_resistances_actives_si_basse_pression")
    print("\nTous les tests du pressuriseur passent.")