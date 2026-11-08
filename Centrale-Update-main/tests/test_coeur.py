"""
tests/test_coeur.py
===================

Tests unitaires de la classe Coeur.

Méthode : on instancie un cœur avec les paramètres nominaux de Paluel,
on lui donne des entrées nominales, et on vérifie que les sorties
ont des propriétés physiques correctes (pas des valeurs exactes,
juste les ordres de grandeur et les signes).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Equipements.coeur import Coeur


# --- Entrées nominales standard (réutilisées dans tous les tests) ---
ENTREES_NOMINALES = {
    'h_1e_c':    1.40e6,    # enthalpie entrée (J/kg) -- eau "froide" sortie GV
    'P_1e_c':    155e5,     # pression entrée (Pa) -- 155 bar
    'm_dot_1_c': 4700.0,    # débit massique (kg/s) -- valeur Paluel
    'Qf':        3800e6,    # puissance fission (W) -- 3800 MW
}


def test_coeur_chauffe_au_nominal():
    """Au régime nominal, le cœur doit chauffer l'eau qui le traverse."""
    c = Coeur('coeur1', V=20.0, S=4.0, H=4.5)
    s = c.step(0.05, ENTREES_NOMINALES)

    assert s['h_1s_c'] > ENTREES_NOMINALES['h_1e_c'], \
        "h_1s_c devrait être supérieur à h_1e_c (le cœur chauffe)"


def test_coeur_perte_de_charge():
    """La pression de sortie doit être inférieure à la pression d'entrée."""
    c = Coeur('coeur1', V=20.0, S=4.0, H=4.5)
    s = c.step(0.05, ENTREES_NOMINALES)

    assert s['P_1s_c'] < ENTREES_NOMINALES['P_1e_c'], \
        "P_1s_c devrait être < P_1e_c (perte de charge)"


def test_coeur_conserve_le_debit():
    """Le débit qui sort égale le débit qui entre (conservation de masse)."""
    c = Coeur('coeur1', V=20.0, S=4.0, H=4.5)
    s = c.step(0.05, ENTREES_NOMINALES)

    assert s['m_dot_1_c'] == ENTREES_NOMINALES['m_dot_1_c'], \
        "Le débit traverse le cœur sans modification"


def test_coeur_ne_diverge_pas():
    """Après 200 pas au nominal, l'état reste dans des valeurs physiques."""
    c = Coeur('coeur1', V=20.0, S=4.0, H=4.5)
    for _ in range(200):
        c.step(0.05, ENTREES_NOMINALES)

    etat = c.get_state()
    assert 1.0e6 < etat['h_1s_c'] < 3.0e6, \
        f"h_1s_c hors plage physique : {etat['h_1s_c']:.3e}"
    assert 100e5 < etat['P_1s_c'] < 200e5, \
        f"P_1s_c hors plage physique : {etat['P_1s_c']:.3e}"


def test_coeur_sans_chauffe_refroidit():
    """Si Qf = 0, l'enthalpie de sortie doit baisser au fil du temps."""
    c = Coeur('coeur1', V=20.0, S=4.0, H=4.5)
    h_initial = c.h_1s_c

    entrees_sans_qf = dict(ENTREES_NOMINALES)
    entrees_sans_qf['Qf'] = 0.0   # on coupe les barres

    for _ in range(100):
        c.step(0.05, entrees_sans_qf)

    assert c.h_1s_c < h_initial, \
        "Sans Qf, l'enthalpie devrait baisser (eau qui se refroidit)"


# --- Lancement manuel si on n'utilise pas pytest ---
if __name__ == '__main__':
    test_coeur_chauffe_au_nominal()
    print("✓ test_coeur_chauffe_au_nominal")
    test_coeur_perte_de_charge()
    print("✓ test_coeur_perte_de_charge")
    test_coeur_conserve_le_debit()
    print("✓ test_coeur_conserve_le_debit")
    test_coeur_ne_diverge_pas()
    print("✓ test_coeur_ne_diverge_pas")
    test_coeur_sans_chauffe_refroidit()
    print("✓ test_coeur_sans_chauffe_refroidit")
    print("\nTous les tests du cœur passent.")