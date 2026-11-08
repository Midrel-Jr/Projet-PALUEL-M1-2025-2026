"""
tests/test_gv.py
================

Tests unitaires de la classe GenerateurVapeur (côté primaire).

Méthode : on instancie un GV avec les paramètres nominaux de Paluel,
on lui donne des entrées nominales, et on vérifie que les sorties
ont des propriétés physiques correctes (pas des valeurs exactes,
juste les ordres de grandeur et les signes).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Equipements.gv import GenerateurVapeur


# --- Entrées nominales standard (réutilisées dans tous les tests) ---
ENTREES_NOMINALES = {
    'h_1e_gv':    1.55e6,   # enthalpie entrée (J/kg) -- eau chaude sortie cœur
    'P_1e_gv':    155.0e5,  # pression entrée (Pa)    -- 155 bar
    'm_dot_1_gv': 4700.0,   # débit massique (kg/s)   -- valeur Paluel
    'Q_1e_gv':    966e6,    # puissance échangée (W)  -- cédée au secondaire
}


def test_gv_refroidit_au_nominal():
    """Au régime nominal, le GV doit refroidir l'eau primaire qui le traverse."""
    gv = GenerateurVapeur('gv1', V=11.0, S=0.20, H=4.0)
    s = gv.step(0.05, ENTREES_NOMINALES)

    assert s['h_1s_gv'] < ENTREES_NOMINALES['h_1e_gv'], \
        "h_1s_gv devrait être inférieur à h_1e_gv (le GV refroidit)"


def test_gv_perte_de_charge():
    """La pression de sortie doit être inférieure à la pression d'entrée."""
    gv = GenerateurVapeur('gv1', V=11.0, S=0.20, H=4.0)
    s = gv.step(0.05, ENTREES_NOMINALES)

    assert s['P_1s_gv'] < ENTREES_NOMINALES['P_1e_gv'], \
        "P_1s_gv devrait être < P_1e_gv (perte de charge)"


def test_gv_conserve_le_debit():
    """Le débit qui sort égale le débit qui entre (conservation de masse)."""
    gv = GenerateurVapeur('gv1', V=11.0, S=0.20, H=4.0)
    s = gv.step(0.05, ENTREES_NOMINALES)

    assert s['m_dot_1_gv'] == ENTREES_NOMINALES['m_dot_1_gv'], \
        "Le débit traverse le GV sans modification"


def test_gv_ne_diverge_pas():
    """Après 200 pas au nominal, l'état reste dans des valeurs physiques."""
    gv = GenerateurVapeur('gv1', V=11.0, S=0.20, H=4.0)
    for _ in range(200):
        gv.step(0.05, ENTREES_NOMINALES)

    etat = gv.get_state()
    assert 1.0e6 < etat['h_1s_gv'] < 3.0e6, \
        f"h_1s_gv hors plage physique : {etat['h_1s_gv']:.3e}"
    assert 100e5 < etat['P_1s_gv'] < 200e5, \
        f"P_1s_gv hors plage physique : {etat['P_1s_gv']:.3e}"


def test_gv_sans_echange_ne_refroidit_plus():
    """Si Q_1e_gv = 0, l'enthalpie de sortie doit monter (plus d'échange)."""
    gv = GenerateurVapeur('gv1', V=11.0, S=0.20, H=4.0)
    h_initial = gv.h_1s_gv

    entrees_sans_echange = dict(ENTREES_NOMINALES)
    entrees_sans_echange['Q_1e_gv'] = 0.0   # on coupe l'échange secondaire

    for _ in range(100):
        gv.step(0.05, entrees_sans_echange)

    assert gv.h_1s_gv > h_initial, \
        "Sans échange, l'enthalpie devrait monter (eau qui se réchauffe)"


# --- Lancement manuel si on n'utilise pas pytest ---
if __name__ == '__main__':
    test_gv_refroidit_au_nominal()
    print("✓ test_gv_refroidit_au_nominal")
    test_gv_perte_de_charge()
    print("✓ test_gv_perte_de_charge")
    test_gv_conserve_le_debit()
    print("✓ test_gv_conserve_le_debit")
    test_gv_ne_diverge_pas()
    print("✓ test_gv_ne_diverge_pas")
    test_gv_sans_echange_ne_refroidit_plus()
    print("✓ test_gv_sans_echange_ne_refroidit_plus")
    print("\nTous les tests du GV passent.")
