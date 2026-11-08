"""Module pompe : classe de base pour les pompes du circuit primaire

Ce module comporte les équations de conservation de la masse et de l'énergie pour une pompe du circuit primaire.
Ces équations seront aussi valables pour les pompes du circuit secondaire en s'assurant de modifier les puissances, débits, paramètres du fluide caloporteur si nécessaire.

Hypothèses :
 H1 : La température du fluide caloporteur est uniforme à l'entrée et à la sortie de la pompe, elle ne dépend donc que du temps T(x,y,z,t)=T(t)
 H2 : L'écoulement se fait seulement selon l'axe de la pompe
 H3 : Il n'y a pas de production volumique de chaleur dans la pompe
 H4 : La pompe est adiabatique, il n'y a pas de transfert de chaleur entre la pompe et l'extérieur
 H6 : Le fluide caloporteur est incompressible, sa masse volumique est constante et sa valeur sera celle de l'eau à la température et pression d'entrée de la pompe
 H7 : La pompe est un système fermé, il n'y a pas de masse qui entre ou qui sort de la pompe en dehors du fluide caloporteur
"""

from Equipements.base import Equipement
from fluides.eau_iapws import proprietes_saturation

from parametres.dataclasses import PompeConfig


class Pompe(Equipement):
    """Classe de base pour les pompes du circuit primaire."""

    def __init__(self, nom="p1", config: PompeConfig = PompeConfig()):

        super().__init__(nom)

        self.config = config

        # --- Paramètres géométriques ---
        self.V_p = config.V_p
        self.S_ep = config.S_ep
        self.S_sp = config.S_sp
        self.H_p = config.H_p
        self.Kg_p = config.Kg_p

        # --- Paramètres actionneurs ---
        self.W_p = config.W_p
        self.g = config.g
        self.dotQ_p = config.dotQ_p
        self.rho_p = config.rho_p
        self.T_1e_p = config.T_1e_p
        self.H_mp = config.H_mp

        # --- Pression d'entrée nominale ---
        self.P_1e_p = config.P_1e_p

        # --- État dynamique nominal ---
        self.m_dot_1s_p = config.m_dot_1e_p

        # Enthalpie d'entrée : liquide saturé h_L à la pression d'entrée
        try:
            rho_L, rho_V, h_L, h_V, *_ = proprietes_saturation(self.P_1e_p)
            self.h_1e_p = h_L
        except Exception:
            self.h_1e_p = config.h_1e_p

        self.h_1s_p = self.h_1e_p + self.g * self.H_mp

        # Variation de pression nominale (Pa)
        self.varP = self.H_mp * self.g * self.rho_p

        # Pression de sortie nominale (Pa)
        self.P_1s_p = self.P_1e_p + self.varP

    def step(self, dt, entrees) -> dict:
        """Avance l'état de la pompe de dt secondes.

        Entrées attendues :
            m_dot_1e_p : débit massique d'entrée (kg/s)
            h_1e_p     : enthalpie d'entrée      (J/kg)
            P_1e_p     : pression d'entrée       (Pa)
        """

        # --- Entrées (avec valeurs nominales par défaut si absentes) ---
        h_1e_p = entrees.get('h_1e_p', self.h_1e_p)
        P_1e_p = entrees.get('P_1e_p', self.P_1e_p)

        # --- La pompe IMPOSE son débit nominal ---
        m_dot_1e_p = self.config.m_dot_1e_p
        m_dot_1s_p = m_dot_1e_p
        self.m_dot_1s_p = m_dot_1s_p

        # --- Conservation de l'énergie ---
        # h_1s = h_1e + apport mécanique (W_p/ṁ) + terme cinétique de Bernoulli
        v_e = m_dot_1e_p / (self.rho_p * self.S_ep)  # vitesse entrée (m/s)
        v_s = m_dot_1s_p / (self.rho_p * self.S_sp)  # vitesse sortie (m/s)
        terme_cinetique = (v_e ** 2 - v_s ** 2) / 2  # J/kg
        h_1s_p = h_1e_p + self.W_p / m_dot_1e_p + terme_cinetique
        self.h_1s_p = h_1s_p

        # --- Variation de pression (H6, H7) ---
        self.varP = self.H_mp * self.g * self.rho_p

        # --- Pression de sortie ---
        self.P_1s_p = P_1e_p + self.varP

        return {
            'm_dot_1s_p': self.m_dot_1s_p,
            'h_1s_p':     self.h_1s_p,
            'varP':       self.varP,
            'P_1s_p':     self.P_1s_p,
        }

    def get_state(self) -> dict:
        return {
            'nom':        self.nom,
            'h_1s_p':     self.h_1s_p,      # J/kg
            'P_1s_p':     self.P_1s_p,      # Pa
            'm_dot_1s_p': self.m_dot_1s_p,  # kg/s
            'W_p':        self.W_p,         # W
        }