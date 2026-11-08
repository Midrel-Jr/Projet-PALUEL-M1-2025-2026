#bibliothèque iapws
"""
fluides/eau_iapws.py
====================

Wrapper autour de la bibliothèque `iapws` (formulation IAPWS-IF97).

Fournit des fonctions simples qui acceptent et renvoient des valeurs
en unités SI strictes (Pa, K, J/kg, kg/m^3), conformément à la
convention du projet (cf. equipements/base.py).

La bibliothèque `iapws` travaille en interne avec :
  - P en MPa  (on divise par 1e6 en entrée)
  - h en kJ/kg (on multiplie par 1e3 en sortie)

Ce module masque ces conversions au reste du projet.
"""

from iapws import IAPWS97


def h_PT(P, T):
    """Enthalpie spécifique de l'eau liquide à (P, T).

    Paramètres
    ----------
    P : float -- pression (Pa)
    T : float -- température (K)

    Retour
    ------
    float -- enthalpie spécifique (J/kg)
    """
    fluide = IAPWS97(P=P / 1e6, T=T)
    return fluide.h * 1e3


def rho_PT(P, T):
    """Masse volumique de l'eau liquide à (P, T).

    Paramètres
    ----------
    P : float -- pression (Pa)
    T : float -- température (K)

    Retour
    ------
    float -- masse volumique (kg/m^3)
    """
    fluide = IAPWS97(P=P / 1e6, T=T)
    return fluide.rho


def T_sat(P):
    """Température de saturation à la pression P.

    Paramètres
    ----------
    P : float -- pression (Pa)

    Retour
    ------
    float -- température de saturation (K)
    """
    liq = IAPWS97(P=P / 1e6, x=0.0)
    return liq.T


def proprietes_saturation(P, dP=1e3):
    """Propriétés de saturation à la pression P, avec dérivées par rapport à P.

    Utilisée par le pressuriseur et le GV pour modéliser la
    coexistence des phases liquide saturée / vapeur saturée.

    Les dérivées (rhoP_L, rhoP_V, hP_L, hP_V) sont calculées par
    différence finie centrée autour de P, avec un pas dP par défaut
    de 1000 Pa (compromis précision / robustesse numérique).

    Paramètres
    ----------
    P : float -- pression de saturation (Pa)
    dP : float -- pas pour la différence finie (Pa, défaut 1e3)

    Retour
    ------
    tuple de 8 floats :
        rho_L  : masse volumique liquide saturé      (kg/m^3)
        rho_V  : masse volumique vapeur saturée      (kg/m^3)
        h_L    : enthalpie liquide saturé            (J/kg)
        h_V    : enthalpie vapeur saturée            (J/kg)
        rhoP_L : drho_L/dP                           (kg/m^3 / Pa)
        rhoP_V : drho_V/dP                           (kg/m^3 / Pa)
        hP_L   : dh_L/dP                             (J/kg / Pa)
        hP_V   : dh_V/dP                             (J/kg / Pa)
    """
    # Valeurs en P
    liq = IAPWS97(P=P / 1e6, x=0.0)
    vap = IAPWS97(P=P / 1e6, x=1.0)
    rho_L = liq.rho
    rho_V = vap.rho
    h_L   = liq.h * 1e3
    h_V   = vap.h * 1e3

    # Valeurs en P + dP (pour différence finie)
    liq_p = IAPWS97(P=(P + dP) / 1e6, x=0.0)
    vap_p = IAPWS97(P=(P + dP) / 1e6, x=1.0)

    # Valeurs en P - dP
    liq_m = IAPWS97(P=(P - dP) / 1e6, x=0.0)
    vap_m = IAPWS97(P=(P - dP) / 1e6, x=1.0)

    # Dérivées par différence finie centrée : (f(P+dP) - f(P-dP)) / (2*dP)
    rhoP_L = (liq_p.rho - liq_m.rho) / (2 * dP)
    rhoP_V = (vap_p.rho - vap_m.rho) / (2 * dP)
    hP_L   = (liq_p.h - liq_m.h) * 1e3 / (2 * dP)
    hP_V   = (vap_p.h - vap_m.h) * 1e3 / (2 * dP)

    return rho_L, rho_V, h_L, h_V, rhoP_L, rhoP_V, hP_L, hP_V

def T_Ph(P, h):
    """Température de l'eau à partir de la pression et de l'enthalpie.

    Paramètres
    ----------
    P : float -- pression (Pa)
    h : float -- enthalpie (J/kg)

    Retour
    ------
    float -- température (K)
    """
    fluide = IAPWS97(P=P / 1e6, h=h / 1e3)
    return fluide.T
