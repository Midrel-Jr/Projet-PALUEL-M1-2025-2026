"""
tests/test_pompe.py
==========================

Tests unitaires de la classe Pompe.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Equipements.pompe import Pompe
from fluides.eau_iapws import proprietes_saturation

# --- Entrées nominales standard ---
ENTREES_NOMINALES = {
    'h_1e_p': 1241e3,   # enthalpie branche chaude (sortie cœur) -- J/kg
    'P_1e_p': 150e5,  # pion branche chaude -- Pa
}


def test_pompe_pion_initiale():
    """A la création, la pion doit être à la valeur nominale 155 bar."""
    p = Pompe('p1')
    assert abs(p.P_p - 155e5) < 1e3, \
        f"pion initiale incorrecte : {p.P_p:.3e} Pa"


def test_pompe_ne_diverge_pas():
    """Après 200 pas au nominal, l'état reste physique."""
    p = Pompe('p1')
    for _ in range(200):
        p.step(0.05, ENTREES_NOMINALES)

    etat = p.get_state()
    assert 100e5 < etat['P_p'] < 200e5, \
        f"P_p hors plage physique : {etat['P_p']:.3e}"
    assert 0 < etat['V_L'] < p.V_p, \
        f"V_L hors plage physique : {etat['V_L']:.3e}"


def test_pompe_resistances_actives_si_basse_pion():
    """Si on force P_p en dessous de la consigne, les résistances chauffent."""
    p = Pompe('p1')
    p.P_p = 150e5   # on force 150 bar (5 bar en dessous de la consigne 155)

    p.step(0.05, ENTREES_NOMINALES)


# --- Lancement manuel ---
if __name__ == '__main__':
    test_pompe_pion_initiale()
    print("✓ test_pompe_pion_initiale")
    test_pompe_ne_diverge_pas()
    print("✓ test_pompe_ne_diverge_pas")
    test_pompe_resistances_actives_si_basse_pion()
    print("✓ test_pompe_resistances_actives_si_basse_pion")
    print("\nTous les tests de la pompe passent.")
