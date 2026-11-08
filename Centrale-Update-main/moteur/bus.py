"""
moteur/bus.py
=============

Bus de données partagé entre tous les équipements du circuit.

Le bus est un dictionnaire central qui contient l'état de toutes les
connexions entre équipements. À chaque pas de temps, chaque équipement
LIT les clés qui le concernent en entrée, calcule, et ÉCRIT ses sorties.

CONVENTION DE NOMMAGE DES CLÉS
------------------------------
    <circuit>.<noeud>.<grandeur>

  - <circuit>  : 'primaire', 'secondaire', 'controle', 'pressuriseur'
  - <noeud>    : 'pompe_sortie', 'coeur_sortie', 'gv_sortie', ...
  - <grandeur> : P (Pa), h (J/kg), m_dot (kg/s)

Toutes les valeurs sont en unités SI strictes.
"""


def bus_initial_nominal():
    """Renvoie le dictionnaire du bus initialisé au régime nominal de Paluel.

    Ces valeurs servent de point de départ cohérent pour la boucle
    fermée du primaire (au premier pas, la pompe lit ces valeurs avant
    que le GV n'ait tourné).

    Retour
    ------
    dict
        Bus initial, prêt à être utilisé par le simulateur.
    """
    return {
        # ---------------- CIRCUIT PRIMAIRE ----------------
        # Sortie pompe (entrée cœur)
        'primaire.pompe_sortie.h':      1.40e6,    # J/kg
        'primaire.pompe_sortie.P':      155e5,     # Pa
        'primaire.pompe_sortie.m_dot':  26104.0,    # kg/s

        # Sortie cœur (entrée GV + lecture pressuriseur)
        'primaire.coeur_sortie.h':      1.55e6,    # J/kg
        'primaire.coeur_sortie.P':      154.5e5,   # Pa
        'primaire.coeur_sortie.m_dot':  26104.0,    # kg/s

        # Sortie GV (entrée pompe -- boucle fermée)
        'primaire.gv_sortie.h':         1.32e6,    # J/kg
        'primaire.gv_sortie.P':         154.0e5,   # Pa
        'primaire.gv_sortie.m_dot':     26104.0,    # kg/s

        # ---------------- CONSIGNES DE CONTROLE -----------
        # ---------------- CONSIGNES DE CONTROLE -----------
        'controle.Qf':                  3800e6,    # W (puissance fission)
        'controle.Q_1gv':               3800e6,    # W (chaleur exportée GV)

        # ---------------- PRESSURISEUR (dérivation) -------
        # Clés isolées : écrites par le pressuriseur, lues par personne
        # d'autre. Initialisées pour éviter une KeyError à l'archivage.
        'pressuriseur.interne.P':       155e5,     # Pa
        'pressuriseur.interne.m_surge': 0.0,       # kg/s
    }