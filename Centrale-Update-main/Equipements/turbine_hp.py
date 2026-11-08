"""
equipements/turbine_hp.py
=========================

Classe TurbineHP — Corps haute pression du circuit secondaire.

Source principale : Delfosse, C. — ULiège, 1979 — Chapitre 4
Source de notation : Equations_V2, Université de Rouen Normandie, 2026

Hypothèses de modélisation :
- H1 : Le débit massique traversant une vanne est proportionnel à son
        ouverture et à la pression amont (linéarisation autour du nominal).
- H2 : Le corps TH est un système du 1er ordre reliant le débit massique
        entrant au couple mécanique produit (inertie thermique de la vapeur).
- H4 : La vanne TH est régulée proportionnellement sur deux canaux :
        écart de puissance électrique et écart de vitesse (statisme).
- H5 : En mode accéléromètre, la vanne TH se ferme exponentiellement
        avec la constante de temps tau_Omega_TH (eq. 39).
- H8 : La chute d'enthalpie spécifique (h2e_TH - h2s_TH) dans TH est supposée
        constante autour du nominal → couple proportionnel au débit massique.

Équations dimensionnelles implémentées (Equations_V2 §5.5.5 et §5.5.6) :

    Débit TH      : m_dot_2e_TH = K_TH · Omega_TH · P_2s_gv
    Débit dump    : m_dot_2e_D  = K_D  · Omega_D  · P_2s_gv
    Débit total   : m_dot_2s_gv = m_dot_2e_TH + m_dot_2e_D
    Pression      : dP_2s_gv/dt = (1/tau_P) · (m_dot_2e_TH - m_dot_2e_TB)   (eq. dimensionnelle)
    Couple TH     : tau_TH · dC_TH/dt = K_TH · m_dot_2e_TH - C_TH           (eq. 36)
    Régulation    : dOmega_TH/dt = K_reg · [(Q_e - Q_e,c)
                                   + (Q0_C / (s · N0)) · (N - N0)]            (eq. 29)
    Accéléromètre : tau_Omega_TH · dOmega_TH/dt = -Omega_TH                  (eq. 39)

Paramètres numériques (Equations_V2 Table 1) :
    K'_TH        = 0.215  (fraction couple TH sur couple total)
    K'_TB        = 0.785  (fraction couple TB)
    tau_TH = tau_TB = 0.25 s (constante de temps corps)
    K'_f         = 0.005  (frottement réduit)
    K'_D         = 0.85   (contournement 85% débit nominal)
    s            = 0.05   (statisme 5%)
    tau_Omega_TH = 0.5 s  (fermeture vanne TH par accéléromètre)
    1/tau_P      = 0.25 s⁻¹  → tau_P = 4 s

Valeurs nominales Paluel (1300 MW, 50 Hz) :
    N0              = 1500  tr/min
    Q0_e            = 1300  MW
    P_2s_gv0        = 69.0  bar  ≈ 6.9e6 Pa  (pression surchauffeur nominale)
    m_dot_2s_gv0    = 1500  kg/s (débit total vapeur nominal)

Convention de notation (Equations_V2 §5.1) :
    Indice TH : Turbine Haute Pression
    Indice TB : Turbine Basse Pression
    2         : Circuit secondaire (vapeur)
    e / s     : entrée / sortie de l'équipement
    D         : Contournement (dump)

Auteur : Équipe 3NC (Solenn, Godwin, Midrel) — Université de Rouen Normandie
"""

from Equipements.base import Equipement


class TurbineHP(Equipement):
    """Corps haute pression TH — circuit secondaire vapeur.

    Variables d'état internes :
        P_2s_gv   : pression au surchauffeur (sortie GV, entrée TH)  (Pa)
        C_TH      : couple mécanique corps TH                         (N·m)
        Omega_TH  : ouverture relative vanne TH                       (-)  ∈ [0, 1]

    Variables algébriques recalculées à chaque pas :
        m_dot_2e_TH : débit massique vapeur entrant corps TH          (kg/s)
        m_dot_2e_D  : débit massique contournement dump               (kg/s)
        m_dot_2s_gv : débit total sortant du surchauffeur             (kg/s)
    """

    def __init__(
        self,
        nom,
        # --- Coefficients adimensionnés (Equations_V2 Table 1) ---
        K_prime_TH       = 0.215,   # fraction couple corps TH                  [-]
        tau_TH           = 0.25,    # constante de temps couple TH              [s]
        K_prime_D        = 0.85,    # coefficient débit dump (85% nominal)      [-]
        s                = 0.05,    # statisme de la régulation                 [-]
        K_prime_f        = 0.005,   # coefficient de frottement réduit          [-]
        tau_Omega_TH     = 0.5,     # constante de temps fermeture vanne TH     [s]
        inv_tau_P        = 0.25,    # inverse constante de temps pression       [s⁻¹]
        K_reg            = 5.0,     # gain du régulateur                        [s⁻¹·MW⁻¹]
        # --- Valeurs nominales Paluel ---
        N0               = 1500.0,  # vitesse nominale                          [tr/min]
        Q0_e_MW          = 1300.0,  # puissance électrique nominale             [MW]
        m_dot_2s_gv0     = 1500.0,  # débit total vapeur nominal                [kg/s]
        P_2s_gv0         = 6.9e6,   # pression surchauffeur nominale            [Pa]
    ):
        super().__init__(nom)

        # --- Paramètres physiques stockés ---
        self.K_prime_TH   = K_prime_TH
        self.tau_TH       = tau_TH
        self.K_prime_D    = K_prime_D
        self.s            = s
        self.K_prime_f    = K_prime_f
        self.tau_Omega_TH = tau_Omega_TH
        self.inv_tau_P    = inv_tau_P      # 1/tau_P  [s⁻¹]
        self.K_reg        = K_reg
        self.N0           = N0
        self.Q0_e         = Q0_e_MW * 1e6  # [W]
        self.m_dot_2s_gv0 = m_dot_2s_gv0
        self.P_2s_gv0     = P_2s_gv0

        # Coefficient de débit vanne TH :
        # m_dot_2e_TH = K_TH · Omega_TH · P_2s_gv
        # Au nominal Omega_TH = 1 → K_TH = m_dot_2s_gv0 / P_2s_gv0
        self.K_TH = m_dot_2s_gv0 / P_2s_gv0          # [kg·s⁻¹·Pa⁻¹]

        # Couple nominal corps TH :
        # C0_TH = K'_TH · C0_u  avec C0_u = Q0_e / omega0
        # omega0 = 2*pi*N0/60
        omega0 = 2.0 * 3.141592653589793 * N0 / 60.0
        self.C0_TH = K_prime_TH * Q0_e_MW * 1e6 / omega0   # [N·m]
        self.C0_u  = Q0_e_MW * 1e6 / omega0                 # [N·m]

        # Constante dimensionnelle couple TH (eq. 36) :
        # tau_TH · dC_TH/dt = K_couple_TH · m_dot_2e_TH - C_TH
        self.K_couple_TH = self.C0_TH / m_dot_2s_gv0        # [N·m·s/kg]

        # --- État dynamique initial (régime nominal Paluel) ---
        self.P_2s_gv   = P_2s_gv0      # pression surchauffeur          [Pa]
        self.C_TH      = self.C0_TH    # couple corps TH                [N·m]
        self.Omega_TH  = 1.0           # vanne TH pleine ouverture      [-]
        self.Omega_D   = 0.0           # vanne dump fermée              [-]

        # Variables algébriques (mises à jour dans step)
        self.m_dot_2e_TH = m_dot_2s_gv0   # [kg/s]
        self.m_dot_2e_D  = 0.0            # [kg/s]
        self.m_dot_2s_gv = m_dot_2s_gv0   # [kg/s]

    # ------------------------------------------------------------------
    def step(self, dt, entrees):
        """Avance l'état du corps TH de dt secondes.

        Entrées attendues :
            m_dot_2e_TB : débit vapeur entrant corps TB     [kg/s]  — depuis TurbineBP
            Omega_D     : consigne ouverture dump           [-]     — depuis protection
            N           : vitesse rotation turbo-alt.       [tr/min]— depuis TurboAlternateur
            Q_e         : puissance élec. instantanée       [W]     — depuis TurboAlternateur
            Q_ec        : puissance élec. de consigne       [W]     — depuis opérateur/régul.
            accel_TH    : déclenchement accéléromètre TH    [bool]  — depuis protection
        """
        m_dot_2e_TB = entrees['m_dot_2e_TB']
        Omega_D     = float(max(0.0, min(1.0, entrees['Omega_D'])))
        N           = entrees['N']
        Q_e         = entrees['Q_e']
        Q_ec        = entrees['Q_ec']
        accel_TH    = entrees['accel_TH']

        # Mémorisation consigne dump
        self.Omega_D = Omega_D

        # ── Débit vapeur entrant corps TH ──────────────────────────────────
        # m_dot_2e_TH = K_TH · Omega_TH · P_2s_gv
        self.m_dot_2e_TH = self.K_TH * self.Omega_TH * self.P_2s_gv

        # ── Débit contournement dump ────────────────────────────────────────
        # m_dot_2e_D = K'_D · K_TH · Omega_D · P_2s_gv
        # K'_D = 0.85 : le dump peut évacuer 85% du débit nominal
        self.m_dot_2e_D = self.K_prime_D * self.K_TH * Omega_D * self.P_2s_gv

        # ── Débit total sortant du surchauffeur ────────────────────────────
        # m_dot_2s_gv = m_dot_2e_TH + m_dot_2e_D
        self.m_dot_2s_gv = self.m_dot_2e_TH + self.m_dot_2e_D

        # ── Pression surchauffeur (eq. dimensionnelle, Equations_V2 §5.5.5) ─
        # dP_2s_gv/dt = (1/tau_P) · (m_dot_2e_TH - m_dot_2e_TB)
        # tau_P = 4 s → 1/tau_P = 0.25 s⁻¹
        dP_dt       = self.inv_tau_P * (self.m_dot_2e_TH - m_dot_2e_TB)
        self.P_2s_gv = max(1e3, self.P_2s_gv + dt * dP_dt)

        # ── Couple corps TH (eq. 36, 1er ordre) ───────────────────────────
        # tau_TH · dC_TH/dt = K_couple_TH · m_dot_2e_TH - C_TH
        dC_TH_dt  = (self.K_couple_TH * self.m_dot_2e_TH - self.C_TH) / self.tau_TH
        self.C_TH = max(0.0, self.C_TH + dt * dC_TH_dt)

        # ── Vanne TH (eq. 29 et eq. 39) ───────────────────────────────────
        if accel_TH:
            # Mode accéléromètre : fermeture exponentielle (eq. 39)
            # tau_Omega_TH · dOmega_TH/dt = -Omega_TH
            dO_dt = -self.Omega_TH / self.tau_Omega_TH
        else:
            # Mode régulation proportionnelle (eq. 29)
            # Omega_TH_dot = K_reg · [(Q_e - Q_ec) + (Q0_C/(s·N0))·(N - N0)]
            # Q0_C = Q0_e au nominal
            ecart_puissance = Q_e - Q_ec
            ecart_vitesse   = (self.Q0_e / (self.s * self.N0)) * (N - self.N0)
            dO_dt = self.K_reg * (ecart_puissance + ecart_vitesse)

        self.Omega_TH = float(max(0.0, min(1.0, self.Omega_TH + dt * dO_dt)))

        return {
            'P_2s_gv':      self.P_2s_gv,     # Pa   — pression surchauffeur
            'C_TH':         self.C_TH,         # N·m  — couple corps TH
            'Omega_TH':     self.Omega_TH,     # [-]  — ouverture vanne TH
            'm_dot_2e_TH':  self.m_dot_2e_TH, # kg/s — débit entrant corps TH
            'm_dot_2e_D':   self.m_dot_2e_D,  # kg/s — débit contournement dump
            'm_dot_2s_gv':  self.m_dot_2s_gv, # kg/s — débit total surchauffeur
        }

    # ------------------------------------------------------------------
    def get_state(self):
        return {
            'nom':           self.nom,
            'P_2s_gv':       self.P_2s_gv,          # Pa
            'P_2s_gv_bar':   self.P_2s_gv / 1e5,    # bar  (lecture humaine)
            'C_TH':          self.C_TH,              # N·m
            'Omega_TH':      self.Omega_TH,          # [-]
            'Omega_D':       self.Omega_D,           # [-]
            'm_dot_2e_TH':   self.m_dot_2e_TH,      # kg/s
            'm_dot_2e_D':    self.m_dot_2e_D,        # kg/s
            'm_dot_2s_gv':   self.m_dot_2s_gv,      # kg/s
        }
