"""
equipements/pressuriseur.py
===========================

Classe Pressuriseur du circuit primaire.

Branché en dérivation sur la branche chaude (sortie cœur), il régule
la pression du primaire à 155 bar par trois actionneurs :
- résistances chauffantes (Q_res) : augmentent la pression
- spray (m_sp) : injecte de l'eau froide, condense la vapeur, réduit P
- soupape de sûreté (m_sv) : décharge la vapeur si surpression

Hypothèses (cf. document Equations_V2, section 7.2) :
- Équilibre thermo local : pression uniforme dans tout le pressuriseur.
- Volume total constant : VL + VV = V_press.
- Spray à l'état de la branche froide : h_sp = h_1e_c.
- Soupape en vapeur saturée : h_sv = h_V(P).
- Masses volumiques uniformes dans chaque phase mais variables en
  temps via la pression (compressibilité conservée).

Équations modélisées :
- Eq 25 (qté de mvt) : dynamique du débit surge ṁ_surge.
- Eq 26 (masse) + Eq 27 (énergie) : système 2x2 résolu pour
  dVL/dt et dP/dt.
"""

from Equipements.base import Equipement
from fluides.eau_iapws import proprietes_saturation
from parametres.dataclasses import PressuriseurConfig
from math import tanh


class Pressuriseur(Equipement):
    """Pressuriseur du circuit primaire."""

    def __init__(self, nom, config=None):
        super().__init__(nom)

        if config is None:
            config = PressuriseurConfig()
        self.config = config

        # --- Paramètres géométriques ---
        self.V_press  = config.V_press
        self.S_press  = config.S_press
        self.H_press  = config.H_press
        self.Kg_press = config.Kg_press
        self.g        = config.g

        # --- Paramètres actionneurs ---
        self.Q_res_max = config.Q_res_max
        self.P_set     = config.P_set
        self.e_max     = config.e_max
        self.Ksp       = config.Ksp
        self.P_sp_on   = config.P_sp_on
        self.Ksv       = config.Ksv
        self.P_sv      = config.P_sv
        self.Q_pertes  = config.Q_pertes

        # --- État dynamique ---
        self.P_press = config.P_press
        self.V_L     = config.V_L
        self.m_surge = 0.0

        # --- Variables exposées (tooltip) ---
        self.Q_res = 0.0
        self.m_sp  = 0.0
        self.m_sv  = 0.0

    def step(self, dt, entrees):
        """Avance l'état du pressuriseur de dt secondes.

        Entrées attendues :
            h_1s_c : enthalpie branche chaude (J/kg) -- sortie cœur
            P_1s_c : pression branche chaude  (Pa)   -- sortie cœur
            h_1e_c : enthalpie branche froide (J/kg) -- pour le spray
        """
        h_chaud = entrees['h_1s_c']
        P_chaud = entrees['P_1s_c']
        h_froid = entrees['h_1e_c']

        P     = self.P_press
        V_L   = self.V_L
        V_V   = self.V_press - V_L

        # --- 1. Propriétés de saturation à P (via IAPWS) ---
        rho_L, rho_V, h_L, h_V, rhoP_L, rhoP_V, hP_L, hP_V = \
            proprietes_saturation(P)

        # --- 2. Actionneurs ---
        sigma = 0.5 * (1.0 + tanh(2.0 * (self.P_set - P) / self.e_max))
        self.Q_res = self.Q_res_max * sigma

        if P >= self.P_sp_on:
            self.m_sp = self.Ksp * (P - P_chaud) ** 0.5 if P > P_chaud else 0.0
        else:
            self.m_sp = 0.0

        if P >= self.P_sv:
            self.m_sv = self.Ksv * (P - self.P_sv) ** 0.5
        else:
            self.m_sv = 0.0

        ### --- 3. Eq 25 : débit surge line (Euler explicite) ---
        # Perte de charge quadratique SIGNÉE : le frottement s'oppose
        # toujours au sens du débit (|m|*m au lieu de m², qui était
        # toujours positif et amplifiait le débit négatif -> divergence)
        pertes = self.Kg_press * abs(self.m_surge) * self.m_surge / (2 * rho_L * self.S_press ** 2)
        dm_surge_dt = (self.S_press / self.H_press) * ((P_chaud - P) - pertes)
        self.m_surge = self.m_surge + dt * dm_surge_dt

        # --- 4. Système 2x2 (Eq 26 + Eq 27) pour dVL/dt et dP/dt ---
        a11 = (rho_L - rho_V)
        a12 = rhoP_L * V_L + rhoP_V * V_V
        b1  = self.m_surge + self.m_sp - self.m_sv

        a21 = (rho_L * h_L - rho_V * h_V)
        a22 = (rhoP_L * h_L + rho_L * hP_L) * V_L \
              + (rhoP_V * h_V + rho_V * hP_V) * V_V
        b2  = (self.m_surge * h_chaud + self.m_sp * h_froid
               - self.m_sv * h_V + self.Q_res - self.Q_pertes)

        # Résolution par Cramer (avec garde-fou sur le déterminant)
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-6:
            det = 1e-6 if det >= 0 else -1e-6
        dVL_dt = (b1 * a22 - b2 * a12) / det
        dP_dt  = (a11 * b2 - a21 * b1) / det

        # --- 5. Euler explicite sur VL et P ---
        self.V_L     = self.V_L + dt * dVL_dt
        self.P_press = self.P_press + dt * dP_dt

        # --- 6. GARDE-FOUS NUMERIQUES ANTI-DIVERGENCE (AJOUT) ---
        self.P_press = max(1e5, min(self.P_press, 200e5))
        self.V_L     = max(0.01 * self.V_press,
                           min(self.V_L, 0.99 * self.V_press))
        self.m_surge = max(-500.0, min(self.m_surge, 500.0))

        return {
            'P_press':   self.P_press,
            'm_surge':   self.m_surge,
        }

    def get_state(self):
        return {
            'nom':     self.nom,
            'P_press': self.P_press,        # Pa
            'V_L':     self.V_L,            # m^3
            'V_V':     self.V_press - self.V_L,  # m^3
            'm_surge': self.m_surge,        # kg/s
            'Q_res':   self.Q_res,          # W
            'm_sp':    self.m_sp,           # kg/s
            'm_sv':    self.m_sv,           # kg/s
        }
class PressuriseurCouple(Equipement):
    """Pressuriseur couplé : maintient la pression primaire à la consigne.

    Modélise l'action régulatrice globale (résistances + spray) qui
    ramène la pression du primaire vers P_set avec une constante de
    temps tau. Sert de point d'ancrage de pression pour la boucle.
    """

    def __init__(self, nom, config=None):
        super().__init__(nom)
        if config is None:
            config = PressuriseurConfig()
        self.config  = config
        self.P_set   = config.P_set
        self.tau     = 0.5            # constante de temps de régulation (s)
        self.P_press = config.P_set
        self.m_surge = 0.0

    def step(self, dt, entrees):
        P_chaud = entrees['P_1s_c']
        # Rappel vers la consigne
        self.P_press = self.P_press + dt * (-(self.P_press - self.P_set) / self.tau)
        self.m_surge = (P_chaud - self.P_set) * 1e-4
        return {'P_press': self.P_press, 'm_surge': self.m_surge}

    def get_state(self):
        return {'nom': self.nom, 'P_press': self.P_press, 'm_surge': self.m_surge}