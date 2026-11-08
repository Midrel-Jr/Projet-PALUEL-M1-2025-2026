"""
moteur/reseau.py
================
Câblage du circuit primaire couplé (J7).

Le pressuriseur est exécuté EN PREMIER : il calcule la pression de
référence du primaire (155 bar) et l'impose à l'entrée de la pompe.
Les autres équipements se calent sur cette référence.

Ordre : Pressuriseur -> Pompe -> Coeur -> GV (boucle fermée).
"""


def reseau_primaire():
    return [
        {
            'equipement': 'pressuriseur',
            'entrees': {'P_1s_c': 'primaire.coeur_sortie.P'},
            'sorties': {
                'P_press': 'pressuriseur.interne.P',
                'm_surge': 'pressuriseur.interne.m_surge',
            },
        },
        {
            'equipement': 'pompe',
            'entrees': {
                'h_1e_p':     'primaire.gv_sortie.h',
                'P_1e_p':     'pressuriseur.interne.P',
                'm_dot_1e_p': 'primaire.gv_sortie.m_dot',
            },
            'sorties': {
                'h_1s_p':     'primaire.pompe_sortie.h',
                'P_1s_p':     'primaire.pompe_sortie.P',
                'm_dot_1s_p': 'primaire.pompe_sortie.m_dot',
            },
        },
        {
            'equipement': 'coeur',
            'entrees': {
                'h_1e_c':    'primaire.pompe_sortie.h',
                'P_1e_c':    'primaire.pompe_sortie.P',
                'm_dot_1_c': 'primaire.pompe_sortie.m_dot',
                'Qf':        'controle.Qf',
            },
            'sorties': {
                'h_1s_c':    'primaire.coeur_sortie.h',
                'P_1s_c':    'primaire.coeur_sortie.P',
                'm_dot_1_c': 'primaire.coeur_sortie.m_dot',
            },
        },
        {
            'equipement': 'gv',
            'entrees': {
                'h_1e_gv':    'primaire.coeur_sortie.h',
                'P_1e_gv':    'primaire.coeur_sortie.P',
                'm_dot_1_gv': 'primaire.coeur_sortie.m_dot',
            },
            'sorties': {
                'h_1s_gv':    'primaire.gv_sortie.h',
                'P_1s_gv':    'primaire.gv_sortie.P',
                'm_dot_1_gv': 'primaire.gv_sortie.m_dot',
            },
        },
    ]