"""
equipements/turbine_bp.py
=========================

Classe TurbineBP — Corps basse pression du circuit secondaire.

Source principale  : Delfosse, C. — ULiège, 1979 — Chapitre 4
Source de notation : Rapport Relaxation 3NC, Université de Rouen Normandie, 2026
                     (§5.2, §5.4.5, §5.5.5, §5.6.5, Table 5)

Hypothèses de modélisation (Rapport §5.5.5) :
- H1 : Le débit massique de vapeur traversant la vanne TB est proportionnel
        à son taux d'ouverture Ω_{TB} et à la pression amont P_{2e,TB}.
        (linéarisation au nominal)
- H2 : Le corps TB est modélisé par un système du 1er ordre reliant le débit
        massique entrant ṁ_{2e,TB} au couple mécanique C_{TB} produit.
- H6 : La vanne TB est normalement à PLEINE OUVERTURE (Ω_{TB} = 1).
        Elle ne se ferme que lors d'un transitoire rapide (ilotage) sous
        l'action de l'accéléromètre, avec la constante de temps T_{Ω,BP}.
        Elle ne sert PAS à moduler la charge.

Équations dimensionnelles implémentées (Rapport §5.6.5, éq. 37 et 39 / Table 5) :

    Débit corps TB      : ṁ_{2e,TB} = K_{TB} · Ω_{TB} · P_{2e,TB}
                          (Rapport §5.6.5 — débit vapeur corps TB)

    Couple corps TB     : τ_{TB} · dC_{TB}/dt = K'_{BP} · ṁ_{2e,TB} − C_{TB}
                          (Rapport éq. 37)

    Vanne normale       : Ω_{TB} = 1  →  dΩ_{TB}/dt = 0
                          (Rapport §5.5.5 — H6)

    Fermeture accel.    : T_{Ω,BP} · dΩ_{TB}/dt = −Ω_{TB}
                          (Rapport éq. 39)

Paramètres numériques (Rapport Table 5 — valeurs Paluel) :
    K'_{BP}    = 0.785       fraction couple corps BP            (−)
    τ_{TB}     = 0.25  s     constante de temps couple TB        (s)
    T_{Ω,BP}   = 0.1   s     constante de temps fermeture vanne  (s)

Valeurs nominales Paluel (Rapport §5.7, Table 3) :
    N⁰         = 1500  tr/min
    Q⁰_e       = 1300  MW
    ṁ⁰_{2s,gv} = 1500  kg/s   débit total vapeur nominal au surchauffeur
    P⁰_{2e,TB} = 1.2×10⁶ Pa   pression nominale entrée corps TB

Convention de notation (Rapport §5.2, §5.4.5) :
    Indice TB / BP : Turbine Basse Pression
    2              : Circuit secondaire (vapeur)
    e / s          : entrée / sortie de l'équipement
    Ω_{TB}         : ouverture relative de la vanne TB      (−)
    C_{TB}         : couple mécanique fourni par le corps TB (N·m)

Auteur : Équipe 3NC (Solenn, Godwin, Midrel) — Université de Rouen Normandie
"""

import math
from Equipements.base import Equipement


class TurbineBP(Equipement):
    """Corps basse pression TB — circuit secondaire vapeur.

    Variables d'état internes :
        C_TB    : couple mécanique corps TB                  (N·m)
        Omega_TB: ouverture relative vanne TB — Ω_{TB}       (−)  ∈ [0, 1]

    Variables algébriques recalculées à chaque pas :
        m_dot_2e_TB : débit massique vapeur entrée corps TB — ṁ_{2e,TB}  (kg/s)
    """

    def __init__(
        self,
        nom,
        # --- Paramètres (Rapport Table 5) ---
        K_prime_BP   = 0.785,   # K'_{BP}   — fraction couple corps BP          (−)
        tau_TB       = 0.25,    # τ_{TB}    — constante de temps couple TB       (s)
        T_Omega_BP   = 0.1,     # T_{Ω,BP}  — constante de temps fermeture vanne (s)
        # --- Valeurs nominales Paluel (Rapport §5.7, Table 3) ---
        N0           = 1500.0,  # N⁰        — vitesse nominale                  (tr/min)
        Q0_e_MW      = 1300.0,  # Q⁰_e      — puissance électrique nominale     (MW)
        m_dot_2s_gv0 = 1500.0,  # ṁ⁰_{2s,gv}— débit total vapeur nominal       (kg/s)
        P_2e_TB0     = 1.2e6,   # P⁰_{2e,TB}— pression nominale entrée corps TB (Pa)
    ):
        super().__init__(nom)

        # --- Paramètres physiques ---
        self.K_prime_BP   = K_prime_BP
        self.tau_TB       = tau_TB
        self.T_Omega_BP   = T_Omega_BP
        self.N0           = N0
        self.Q0_e         = Q0_e_MW * 1e6   # (W)
        self.m_dot_2s_gv0 = m_dot_2s_gv0
        self.P_2e_TB0     = P_2e_TB0

        # Couple nominal corps TB : C⁰_{TB} = K'_{BP} · Q⁰_e / ω⁰
        # avec ω⁰ = 2π·N⁰/60
        omega0        = 2.0 * math.pi * N0 / 60.0
        self.C0_TB    = K_prime_BP * Q0_e_MW * 1e6 / omega0   # (N·m)

        # Coefficient de débit vanne TB :
        # ṁ_{2e,TB} = K_{TB} · Ω_{TB} · P_{2e,TB}
        # Au nominal Ω_{TB}=1 → K_{TB} = ṁ⁰_{2s,gv} / P⁰_{2e,TB}
        self.K_TB     = m_dot_2s_gv0 / P_2e_TB0               # (kg·s⁻¹·Pa⁻¹)

        # Constante de proportionnalité couple/débit :
        # τ_{TB}·dC_{TB}/dt = K_couple_TB · ṁ_{2e,TB} − C_{TB}
        # avec K_couple_TB = C⁰_{TB} / ṁ⁰_{2s,gv}
        self.K_couple_TB = self.C0_TB / m_dot_2s_gv0          # (N·m·s/kg)

        # --- État dynamique initial (régime nominal Paluel) ---
        self.C_TB       = self.C0_TB   # C_{TB}    — couple corps TB   (N·m)
        self.Omega_TB   = 1.0          # Ω_{TB}    — vanne TB ouverte  (−)

        # Variable algébrique
        self.m_dot_2e_TB = m_dot_2s_gv0  # ṁ_{2e,TB}  (kg/s)

    # ------------------------------------------------------------------
    def step(self, dt, entrees):
        """Avance l'état du corps BP de dt secondes.

        Entrées attendues (Rapport §5.6.5) :
            P_2e_TB  : P_{2e,TB} — pression entrée corps TB      (Pa)   — depuis SS/TH
            accel_TB : déclenchement accéléromètre TB             (bool) — depuis protection
        """
        P_2e_TB  = entrees['P_2e_TB']
        accel_TB = entrees['accel_TB']

        # ── Débit vapeur corps TB (Rapport §5.6.5) ────────────────────────────
        # ṁ_{2e,TB} = K_{TB} · Ω_{TB} · P_{2e,TB}
        self.m_dot_2e_TB = self.K_TB * self.Omega_TB * max(P_2e_TB, 0.0)

        # ── Couple corps TB (Rapport éq. 37 — système 1er ordre) ──────────────
        # τ_{TB} · dC_{TB}/dt = K'_{BP} · ṁ_{2e,TB} − C_{TB}
        # Note : K'_{BP} · ṁ_{2e,TB} ≡ K_couple_TB · ṁ_{2e,TB} (même constante)
        dC_TB_dt = (self.K_couple_TB * self.m_dot_2e_TB - self.C_TB) / self.tau_TB
        self.C_TB = max(0.0, self.C_TB + dt * dC_TB_dt)

        # ── Vanne TB (Rapport éq. 39) ──────────────────────────────────────────
        if accel_TB:
            # Mode accéléromètre : fermeture exponentielle rapide
            # T_{Ω,BP} · dΩ_{TB}/dt = −Ω_{TB}
            dOmega_TB_dt  = -self.Omega_TB / self.T_Omega_BP
            self.Omega_TB = float(max(0.0, self.Omega_TB + dt * dOmega_TB_dt))
        else:
            # Fonctionnement normal : vanne TB toujours à 100% (H6)
            # dΩ_{TB}/dt = 0
            self.Omega_TB = 1.0

        return {
            'C_TB':        self.C_TB,        # C_{TB}     (N·m)
            'Omega_TB':    self.Omega_TB,    # Ω_{TB}     (−)
            'm_dot_2e_TB': self.m_dot_2e_TB, # ṁ_{2e,TB}  (kg/s)
        }

    # ------------------------------------------------------------------
    def get_state(self):
        return {
            'nom':         self.nom,
            'C_TB':        self.C_TB,        # C_{TB}     (N·m)
            'Omega_TB':    self.Omega_TB,    # Ω_{TB}     (−)
            'm_dot_2e_TB': self.m_dot_2e_TB, # ṁ_{2e,TB}  (kg/s)
        }
