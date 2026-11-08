"""
equipements/turbo_alternateur.py
================================

Classe TurboAlternateur — Arbre commun + alternateur.

Source principale  : Delfosse, C. — ULiège, 1979 — Chapitre 5
Source de notation : Rapport Relaxation 3NC, Université de Rouen Normandie, 2026
                     (§5.2, §5.4.5, §5.5.5, §5.6.5, §5.6.7, Table 5)

Rôle dans la chaîne de conversion :
    TurbineHP ──► TurbineBP ──► TurboAlternateur ──► Réseau électrique

Hypothèses (Rapport §5.5.5) :
- Un seul arbre rigide relie TH, TB et le rotor de l'alternateur.
- Réseau infini : la fréquence impose N = N⁰ = 1500 tr/min → dN/dt = 0.
- Ilotage : N évolue par la loi des masses tournantes (Rapport §5.6.7, éq. 38).

Équations dimensionnelles implémentées (Rapport §5.6.7, éq. 38 / Table 5) :

    Couple utile       : C_u = C_{TH} + C_{TB} − K_f · N
                         (Rapport éq. 38)

    Puissance élec.    : Q_e = k_e · C_u · N     avec k_e = 2π/60
                         (Rapport §5.6.5 — puissance alternateur)

    Couple auxiliaires : C_a = C⁰_a · (1 + 0.8 · (N − N⁰)/N⁰)
                         (linéarisé — Rapport §5.5.5)

    Dynamique vitesse  : τ_J · dN/dt = C_u − C_a    (ilotage)
                         dN/dt = 0                   (réseau infini)

Paramètres numériques (Rapport Table 5 — valeurs Paluel) :
    K'_{HP}  = 0.215     fraction couple corps HP           (−)
    K'_{BP}  = 0.785     fraction couple corps BP           (−)
    K'_f     = 0.005     coefficient frottement réduit      (−)
    N⁰       = 1500      vitesse nominale                   (tr/min)
    Q⁰_e     = 1300      puissance électrique nominale      (MW)

Convention de notation (Rapport §5.2, §5.4.5) :
    C_{TH}   : couple mécanique corps TH                    (N·m)
    C_{TB}   : couple mécanique corps TB                    (N·m)
    C_u      : couple utile total sur l'arbre               (N·m)
    C_a      : couple absorbé par les auxiliaires           (N·m)
    N        : vitesse de rotation turbo-alternateur         (tr/min)
    Q_e      : puissance électrique générée                 (W)
    K_f      : coefficient de frottement                    (N·m·min/tr)
    τ_J      : constante d'inertie du groupe                (s)

Auteur : Équipe 3NC (Solenn, Godwin, Midrel) — Université de Rouen Normandie
"""

import math
from Equipements.base import Equipement


class TurboAlternateur(Equipement):
    """Arbre + alternateur — interface mécanique/électrique.

    Variables d'état internes :
        N    : vitesse de rotation — N                       (tr/min)

    Variables algébriques recalculées à chaque pas :
        C_u  : couple utile total sur l'arbre — C_u         (N·m)
        C_a  : couple auxiliaires — C_a                     (N·m)
        Q_e  : puissance électrique générée — Q_e           (W)
    """

    def __init__(
        self,
        nom,
        # --- Paramètres physiques (Rapport Table 5) ---
        tau_J      = 8.5,     # τ_J     — constante d'inertie du groupe      (s)
        K_prime_f  = 0.005,   # K'_f    — coefficient frottement réduit      (−)
        f_aux      = 0.03,    # f_{aux} — fraction puissance aux. au nominal (−)
        n_aux      = 0.8,     # n_{aux} — exposant loi auxiliaires           (−)
        # --- Valeurs nominales Paluel (Rapport §5.7, Table 3) ---
        N0         = 1500.0,  # N⁰      — vitesse nominale 50 Hz             (tr/min)
        Q0_e_MW    = 1300.0,  # Q⁰_e    — puissance électrique nominale      (MW)
    ):
        super().__init__(nom)

        self.tau_J     = tau_J
        self.K_prime_f = K_prime_f
        self.f_aux     = f_aux
        self.n_aux     = n_aux
        self.N0        = N0
        self.Q0_e      = Q0_e_MW * 1e6   # (W)

        # Constante de conversion couple–puissance : Q_e = k_e · C_u · N
        # k_e = 2π/60  (conversion tr/min → rad/s)
        self.k_e = 2.0 * math.pi / 60.0  # (rad·s⁻¹ / (tr·min⁻¹))

        # Couple utile nominal : C⁰_u = Q⁰_e / (k_e · N⁰)
        self.C0_u = Q0_e_MW * 1e6 / (self.k_e * N0)   # (N·m)

        # Coefficient de frottement dimensionnel :
        # K'_f = K_f · N⁰ / C⁰_u  →  K_f = K'_f · C⁰_u / N⁰
        self.K_f = K_prime_f * self.C0_u / N0          # (N·m·min/tr)

        # Couple auxiliaires nominal : C⁰_a = f_{aux} · C⁰_u
        self.C0_a = f_aux * self.C0_u                  # (N·m)

        # Coefficient linéarisé des auxiliaires (Rapport §5.5.5) :
        # C_a = C⁰_a · (1 + n_{aux} · (N − N⁰)/N⁰)
        # soit : C_a = C⁰_a + (C⁰_a · n_{aux} / N⁰) · (N − N⁰)
        self.coeff_aux = self.C0_a * n_aux / N0        # (N·m·min/tr)

        # --- État dynamique initial (régime nominal Paluel) ---
        self.N             = N0                 # N        (tr/min)
        self.reseau_infini = True

        # Variables algébriques (mises à jour dans step)
        self.C_u = self.C0_u                   # C_u      (N·m)
        self.C_a = self.C0_a                   # C_a      (N·m)
        self.Q_e = Q0_e_MW * 1e6              # Q_e      (W)

    # ------------------------------------------------------------------
    def step(self, dt, entrees):
        """Avance l'état du turbo-alternateur de dt secondes.

        Entrées attendues (Rapport §5.6.7) :
            C_TH          : C_{TH} — couple corps TH         (N·m)  — depuis TurbineHP
            C_TB          : C_{TB} — couple corps TB         (N·m)  — depuis TurbineBP
            reseau_infini : True = groupe synchrone réseau   (bool) — depuis protection
        """
        C_TH               = entrees['C_TH']
        C_TB               = entrees['C_TB']
        self.reseau_infini = entrees['reseau_infini']

        # ── Couple utile (Rapport éq. 38) ─────────────────────────────────────
        # C_u = C_{TH} + C_{TB} − K_f · N
        self.C_u = C_TH + C_TB - self.K_f * self.N

        # ── Puissance électrique (Rapport §5.6.5) ─────────────────────────────
        # Q_e = k_e · C_u · N    avec k_e = 2π/60
        self.Q_e = max(0.0, self.k_e * self.C_u * self.N)

        # ── Couple auxiliaires (Rapport §5.5.5 — linéarisé, n_{aux} = 0.8) ───
        # C_a = C⁰_a + coeff_aux · (N − N⁰)
        self.C_a = self.C0_a + self.coeff_aux * (self.N - self.N0)

        # ── Dynamique de vitesse ───────────────────────────────────────────────
        if self.reseau_infini:
            # Réseau infini : groupe synchrone → N imposée à N⁰, dN/dt = 0
            self.N = self.N0
        else:
            # Ilotage : loi des masses tournantes (Rapport §5.6.7, éq. 38)
            # τ_J · dN/dt = C_u − C_a
            dN_dt  = (self.C_u - self.C_a) / self.tau_J   # (tr/min/s)
            self.N = max(0.0, self.N + dt * dN_dt)

        return {
            'N':   self.N,    # N    (tr/min)
            'C_u': self.C_u,  # C_u  (N·m)
            'C_a': self.C_a,  # C_a  (N·m)
            'Q_e': self.Q_e,  # Q_e  (W)
        }

    # ------------------------------------------------------------------
    def get_state(self):
        return {
            'nom':           self.nom,
            'N':             self.N,            # N        (tr/min)
            'C_u':           self.C_u,          # C_u      (N·m)
            'C_a':           self.C_a,          # C_a      (N·m)
            'Q_e':           self.Q_e,          # Q_e      (W)
            'Q_e_MW':        self.Q_e / 1e6,    # Q_e      (MW)
            'reseau_infini': self.reseau_infini,
        }
