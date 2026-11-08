"""
tests/test_turbo_alternateur.py
================================

Tests unitaires de la classe TurboAlternateur.

Notations conformes au Rapport Relaxation 3NC (§5.4.5, §5.6.5, §5.6.7, Table 5) :
    C_{TH}   : couple mécanique corps TH        (N·m)
    C_{TB}   : couple mécanique corps TB        (N·m)
    C_u      : couple utile total sur l'arbre   (N·m)
    C_a      : couple absorbé par les auxiliaires (N·m)
    N        : vitesse de rotation              (tr/min)
    Q_e      : puissance électrique générée     (W)
    K'_{HP}  = 0.215   (Rapport Table 5)
    K'_{BP}  = 0.785   (Rapport Table 5)

Méthode : on instancie un turbo-alternateur avec les paramètres nominaux de Paluel,
on lui donne des entrées nominales, et on vérifie que les sorties ont des
propriétés physiques correctes (ordres de grandeur et signes).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math
from Equipements.turbo_alternateur import TurboAlternateur

# Couples nominaux Paluel (Rapport §5.6.7, Table 5)
# C⁰_u = Q⁰_e / ω⁰  avec ω⁰ = 2π·N⁰/60
_omega0 = 2.0 * math.pi * 1500.0 / 60.0
C0_u    = 1300e6 / _omega0      # C⁰_u ≈ 8.28×10⁶ N·m
C0_TH   = 0.215 * C0_u         # K'_{HP} = 0.215
C0_TB   = 0.785 * C0_u         # K'_{BP} = 0.785

# --- Entrées nominales standard ---
ENTREES_NOMINALES = {
    'C_TH':          C0_TH,  # C_{TH} nominal   (N·m)
    'C_TB':          C0_TB,  # C_{TB} nominal   (N·m)
    'reseau_infini':  True,
}


def test_ta_puissance_positive_au_nominal():
    """Au régime nominal, la puissance Q_e doit être strictement positive."""
    ta = TurboAlternateur('TA')
    s = ta.step(0.05, ENTREES_NOMINALES)
    assert s['Q_e'] > 0, \
        f"Q_e devrait être positif au nominal : {s['Q_e']:.3e} W"


def test_ta_puissance_ordre_grandeur():
    """Q_e doit être proche de Q⁰_e = 1300 MW (±20%)."""
    ta = TurboAlternateur('TA')
    s = ta.step(0.05, ENTREES_NOMINALES)
    assert 1040e6 < s['Q_e'] < 1560e6, \
        f"Q_e hors plage ±20% de 1300 MW : {s['Q_e']/1e6:.1f} MW"


def test_ta_vitesse_constante_reseau_infini():
    """En réseau infini, N doit rester figée à N⁰ = 1500 tr/min."""
    ta = TurboAlternateur('TA')
    for _ in range(200):
        ta.step(0.05, ENTREES_NOMINALES)
    assert ta.N == 1500.0, \
        f"N devrait rester à 1500 tr/min en réseau infini : {ta.N:.2f}"


def test_ta_ilotage_surcouple_accelere():
    """En ilotage avec C_{TH}+C_{TB} excédentaire, N doit augmenter."""
    ta = TurboAlternateur('TA')
    entrees_ilot = dict(ENTREES_NOMINALES)
    entrees_ilot['reseau_infini'] = False
    entrees_ilot['C_TH'] = C0_TH * 1.3
    entrees_ilot['C_TB'] = C0_TB * 1.3

    N_initial = ta.N
    for _ in range(20):
        ta.step(0.05, entrees_ilot)
    assert ta.N > N_initial, \
        "Un couple excédentaire en ilotage devrait accélérer le groupe (dN/dt > 0)"


def test_ta_ilotage_souscouple_decelere():
    """En ilotage avec C_{TH} = C_{TB} = 0 (turbines à l'arrêt), N doit diminuer."""
    ta = TurboAlternateur('TA')
    entrees_ilot = dict(ENTREES_NOMINALES)
    entrees_ilot['reseau_infini'] = False
    entrees_ilot['C_TH'] = 0.0
    entrees_ilot['C_TB'] = 0.0

    N_initial = ta.N
    for _ in range(20):
        ta.step(0.05, entrees_ilot)
    assert ta.N < N_initial, \
        "Avec C_{TH}=C_{TB}=0 en ilotage, N doit décroître (frottements + auxiliaires)"


def test_ta_vitesse_positive_ilotage():
    """N ne doit jamais devenir négative, même en ilotage long avec couple nul."""
    ta = TurboAlternateur('TA')
    entrees_ilot = dict(ENTREES_NOMINALES)
    entrees_ilot['reseau_infini'] = False
    entrees_ilot['C_TH'] = 0.0
    entrees_ilot['C_TB'] = 0.0
    for _ in range(500):
        ta.step(0.05, entrees_ilot)
    assert ta.N >= 0.0, \
        f"N ne doit pas devenir négative : {ta.N:.2f} tr/min"


def test_ta_couple_auxiliaires_croissant_avec_N():
    """C_a doit augmenter quand N augmente (linéarisation Rapport §5.5.5)."""
    ta_ref  = TurboAlternateur('TA_ref')
    ta_fast = TurboAlternateur('TA_fast')

    # Accélérer ta_fast en ilotage avec surcouple
    entrees_ilot = {'C_TH': C0_TH * 1.5, 'C_TB': C0_TB * 1.5, 'reseau_infini': False}
    for _ in range(30):
        ta_fast.step(0.05, entrees_ilot)

    ta_ref.step(0.05, ENTREES_NOMINALES)
    ta_fast.step(0.05, {'C_TH': C0_TH, 'C_TB': C0_TB, 'reseau_infini': False})

    assert ta_fast.C_a > ta_ref.C_a, \
        "C_a doit augmenter avec N (Rapport §5.5.5 — linéarisation auxiliaires)"


def test_ta_ne_diverge_pas():
    """Après 200 pas au nominal en réseau infini, l'état reste physique."""
    ta = TurboAlternateur('TA')
    for _ in range(200):
        ta.step(0.05, ENTREES_NOMINALES)
    etat = ta.get_state()
    assert etat['N'] == 1500.0, \
        f"N devrait rester à 1500 tr/min en réseau infini : {etat['N']:.2f}"
    assert etat['Q_e'] > 0, \
        f"Q_e devrait rester positif : {etat['Q_e']:.3e} W"
    assert etat['C_a'] > 0, \
        f"C_a devrait rester positif : {etat['C_a']:.3e} N·m"


def test_ta_couple_nul_donne_puissance_nulle():
    """Si C_{TH} = C_{TB} = 0, Q_e doit être clampée à 0 (frottements dominent)."""
    ta = TurboAlternateur('TA')
    entrees_vides = {'C_TH': 0.0, 'C_TB': 0.0, 'reseau_infini': True}
    s = ta.step(0.05, entrees_vides)
    assert s['Q_e'] == 0.0, \
        f"Q_e devrait être 0 (clampé) quand C_TH=C_TB=0 : {s['Q_e']:.3e} W"


# --- Lancement manuel si on n'utilise pas pytest ---
if __name__ == '__main__':
    test_ta_puissance_positive_au_nominal()
    print("✓ test_ta_puissance_positive_au_nominal")
    test_ta_puissance_ordre_grandeur()
    print("✓ test_ta_puissance_ordre_grandeur")
    test_ta_vitesse_constante_reseau_infini()
    print("✓ test_ta_vitesse_constante_reseau_infini")
    test_ta_ilotage_surcouple_accelere()
    print("✓ test_ta_ilotage_surcouple_accelere")
    test_ta_ilotage_souscouple_decelere()
    print("✓ test_ta_ilotage_souscouple_decelere")
    test_ta_vitesse_positive_ilotage()
    print("✓ test_ta_vitesse_positive_ilotage")
    test_ta_couple_auxiliaires_croissant_avec_N()
    print("✓ test_ta_couple_auxiliaires_croissant_avec_N")
    test_ta_ne_diverge_pas()
    print("✓ test_ta_ne_diverge_pas")
    test_ta_couple_nul_donne_puissance_nulle()
    print("✓ test_ta_couple_nul_donne_puissance_nulle")
    print("\nTous les tests du turbo-alternateur passent.")
