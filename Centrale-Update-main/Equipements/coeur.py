"""
equipements/coeur.py
====================

Classe Coeur (cœur + cuve) du circuit primaire.

Hypothèses (cf. document Equations_V2, section 6.1) :
- Débit identique entrée/sortie : m_dot_1e_c = m_dot_1s_c = m_dot_1_c
- Ce débit est imposé par la pompe (et peut varier dans le temps).
- Fluide incompressible (rho constant).
- Cœur parfaitement agité : l'état interne = état de sortie.

Équations modélisées :
- Eq 24 (énergie) : dynamique de l'enthalpie de sortie h_1s_c.
- Eq 23 (quantité de mouvement) : pression de sortie, en gardant
  le terme inertiel (H/S) * dṁ/dt, calculé par différence finie.
"""
from Equipements.base import Equipement
from parametres.dataclasses import CoeurConfig   # adapte le chemin selon ton arborescence


class Coeur(Equipement):
    """Cœur + cuve du circuit primaire."""

    def __init__(self, nom, config=None):
        super().__init__(nom)

        # Si aucune config fournie, on prend les valeurs nominales par défaut
        if config is None:
            config = CoeurConfig()
        self.config = config

        # --- Paramètres géométriques (depuis la config) ---
        self.V   = config.V_c
        self.S   = config.S_c
        self.H   = config.H_c
        self.rho = config.rho_c
        self.Kg  = config.Kg_c
        self.g   = config.g

        # --- État dynamique (valeurs initiales depuis la config) ---
        self.h_1s_c     = config.h_1s_c
        self.m_dot_1_c  = config.m_dot_1_c
        self.m_dot_prev = config.m_dot_1_c
        self.P_1s_c     = config.P_1s_c
        self.Qf         = config.Qf

    def step(self, dt, entrees):
        """Avance l'état du cœur de dt secondes.

        Entrées attendues :
            h_1e_c    : enthalpie entrée    (J/kg)  -- venue pompe
            P_1e_c    : pression entrée     (Pa)    -- venue pompe
            m_dot_1_c : débit imposé        (kg/s)  -- venue pompe
            Qf        : puissance fission   (W)     -- consigne barres
        """
        h_e   = entrees['h_1e_c']
        P_e   = entrees['P_1e_c']
        m_dot = entrees['m_dot_1_c']
        Qf    = entrees['Qf']

        # --- Eq 24 : conservation de l'énergie (Euler explicite) ---
        # rho * V * dh/dt = ṁ * (h_e - h_s) + Qf - ṁ * g * H
        dh_dt = (m_dot * (h_e - self.h_1s_c) + Qf
                 - m_dot * self.g * self.H) / (self.rho * self.V)
        self.h_1s_c = self.h_1s_c + dt * dh_dt

        # --- Eq 23 : pression de sortie ---
        # P_e - P_s = Kg*ṁ²/(2*rho*S²) + (H/S)*dṁ/dt + rho*g*H
        dm_dot_dt = (m_dot - self.m_dot_prev) / dt
        pertes_charge  = self.Kg * m_dot**2 / (2 * self.rho * self.S**2)
        inertie        = (self.H / self.S) * dm_dot_dt
        hydrostatique  = self.rho * self.g * self.H
        delta_P = pertes_charge + inertie + hydrostatique
        self.P_1s_c = P_e - delta_P

        # Mémorisation
        self.m_dot_prev = m_dot
        self.m_dot_1_c  = m_dot
        self.Qf         = Qf

        return {
            'h_1s_c':    self.h_1s_c,
            'P_1s_c':    self.P_1s_c,
            'm_dot_1_c': self.m_dot_1_c,
        }

    def get_state(self):
        return {
            'nom':       self.nom,
            'h_1s_c':    self.h_1s_c,     # J/kg
            'P_1s_c':    self.P_1s_c,     # Pa
            'm_dot_1_c': self.m_dot_1_c,  # kg/s
            'Qf':        self.Qf,         # W
        }
