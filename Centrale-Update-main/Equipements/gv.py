"""
equipements/gv.py
=================

Classe GenerateurVapeur — côté primaire uniquement.
*
Hypothèses (document Equations_V2) :
- Débit constant entrée/sortie : m_dot_1e_gv = m_dot_1s_gv = m_dot_1_gv
- Fluide incompressible (rho constant).
- GV parfaitement agité : état interne = état de sortie.
- Q_1e_gv (puissance échangée vers le secondaire) est une ENTRÉE
  fournie par le couplage avec le côté secondaire du GV.

Équations modélisées :
- Eq énergie   : rho_1,gv * V_1,gv * dh_1s,gv/dt
                 = ṁ_1,gv * (h_1e,gv - h_1s,gv) - Q_1e,gv - ṁ_1,gv*g*H_1,gv
- Eq QdM       : P_1e,gv - P_1s,gv
                 = Kg,gv * ṁ²/(2*rho*S²) + (H_1,gv/S_1,gv)*dṁ/dt
"""

from Equipements.base import Equipement


class GenerateurVapeur(Equipement):
    """GV — côté primaire du circuit 1."""

    def __init__(self, nom,
                 V=11.0, S=0.20, H=4.0,
                 rho=720.0, Kg=3.0, g=9.81):
        super().__init__(nom)

        # --- Paramètres géométriques (constants) ---
        self.V   = V      # volume eau primaire dans le GV   (m^3)
        self.S   = S      # section de passage               (m^2)
        self.H   = H      # hauteur du faisceau              (m)
        self.rho = rho    # masse volumique eau primaire     (kg/m^3)  ~720 à 310°C
        self.Kg  = Kg     # coeff. pertes de charge          (sans dim.)
        self.g   = g      # gravité                          (m/s^2)

        # --- État dynamique — valeurs nominales Paluel ---
        self.h_1s_gv     = 1.30e6   # enthalpie sortie primaire    (J/kg)
        self.P_1s_gv     = 153.5e5  # pression sortie primaire     (Pa)
        self.m_dot_1_gv  = 4700.0   # débit primaire traversant    (kg/s)
        self.m_dot_prev  = 4700.0   # débit du pas précédent       (pour dṁ/dt)
        self.Q_1e_gv     = 966e6    # puissance cédée au secondaire (W)

    # ------------------------------------------------------------------
    def step(self, dt, entrees):
        """Avance l'état du GV primaire de dt secondes.

        Entrées attendues :
            h_1e_gv    : enthalpie entrée primaire    (J/kg)  -- venue cœur
            P_1e_gv    : pression  entrée primaire    (Pa)    -- venue cœur
            m_dot_1_gv : débit primaire               (kg/s)  -- venue cœur / pompe
            Q_1e_gv    : puissance échangée secondaire(W)     -- venue couplage GV2
        """
        h_e    = entrees['h_1e_gv']
        P_e    = entrees['P_1e_gv']
        m_dot  = entrees['m_dot_1_gv']
        Q_exch = entrees['Q_1e_gv']

        # --- Équation énergie (Euler explicite) ---
        # rho * V * dh/dt = ṁ*(h_e - h_s) - Q_1e,gv - ṁ*g*H
        dh_dt = (
            m_dot * (h_e - self.h_1s_gv)
            - Q_exch
            - m_dot * self.g * self.H
        ) / (self.rho * self.V)
        self.h_1s_gv = self.h_1s_gv + dt * dh_dt

        # --- Équation quantité de mouvement ---
        # P_e - P_s = Kg*ṁ²/(2*rho*S²) + (H/S)*dṁ/dt
        dm_dot_dt     = (m_dot - self.m_dot_prev) / dt
        pertes_charge = self.Kg * m_dot**2 / (2 * self.rho * self.S**2)
        inertie       = (self.H / self.S) * dm_dot_dt
        self.P_1s_gv  = P_e - pertes_charge - inertie

        # Mémorisation
        self.m_dot_prev = m_dot
        self.m_dot_1_gv = m_dot
        self.Q_1e_gv    = Q_exch

        return {
            'h_1s_gv':    self.h_1s_gv,
            'P_1s_gv':    self.P_1s_gv,
            'm_dot_1_gv': self.m_dot_1_gv,
        }

    # ------------------------------------------------------------------
    def get_state(self):
        return {
            'nom':        self.nom,
            'h_1s_gv':    self.h_1s_gv,    # J/kg
            'P_1s_gv':    self.P_1s_gv,    # Pa
            'm_dot_1_gv': self.m_dot_1_gv, # kg/s
            'Q_1e_gv':    self.Q_1e_gv,    # W
        }


# ======================================================================
# TEST AUTONOME (python gv.py)
# ======================================================================
if __name__ == '__main__':

    gv = GenerateurVapeur(nom='GV-1')

    # Conditions nominales Paluel (circuit primaire)
    entrees_nominales = {
        'h_1e_gv':    1.55e6,   # sortie cœur          (J/kg)
        'P_1e_gv':    155.0e5,  # pression avant GV     (Pa)
        'm_dot_1_gv': 4700.0,   # débit primaire        (kg/s)
        'Q_1e_gv':    966e6,    # puissance échangée    (W)
    }

    dt = 1.0   # pas de temps (s)
    N  = 200   # nombre de pas

    print(f"{'t(s)':>6}  {'h_1s_gv (kJ/kg)':>18}  {'P_1s_gv (bar)':>14}  {'m_dot (kg/s)':>13}")
    print("-" * 60)

    for i in range(N):
        t = i * dt
        sorties = gv.step(dt, entrees_nominales)
        gv.archive(t)

        if i % 20 == 0:
            print(
                f"{t:6.0f}  "
                f"{sorties['h_1s_gv']/1e3:18.2f}  "
                f"{sorties['P_1s_gv']/1e5:14.4f}  "
                f"{sorties['m_dot_1_gv']:13.1f}"
            )

    print("\nÉtat final :")
    for k, v in gv.get_state().items():
        print(f"  {k}: {v}")