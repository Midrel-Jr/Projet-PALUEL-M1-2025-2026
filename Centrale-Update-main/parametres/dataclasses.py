from dataclasses import dataclass

@dataclass
class PompeConfig:
    V_p: float = 40.0 # Volume total de la pompe, Volume interne occupé par le fluide
    S_ep: float = 0.486 # Section d’entrée de la pompe
    S_sp: float = 0.385 # Section de sortie de la pompe
    H_p: float = 3.0 # Hauteur géométrique de la pompe
    Kg_p: float = 3.0  # Coefficiant de perte de charge (sans dim.)
    W_p: float = 7e6       # W (puissance résistances installée)
    g: float = 9.81       # m/s^2 (accélération de la pesanteur)
    dotQ_p: float = 29.6   # m^3/s (débit volumique nominal)
    rho_p: float = 882  # kg/m^3 (masse volumique
    T_1e_p: float = 548.0  # K (température d'entrée nominale)
    H_mp: float = 100.0     # mCe (hauteur manométrique nominale)
    P_1e_p: float = 150e5      # Pa (pression d'entrée nominale)
    h_1e_p: float = 1241e3     # J/kg (enthalpie d'entrée nominale)
    m_dot_1e_p: float = 26104.0 # kg/s (débit massique d'entrée nominale)
@dataclass
class CoeurConfig:
    V_c: float = 20.0       # m^3 (volume interne du cœur occupé par le fluide)
    S_c: float = 4.0        # m^2 (section de passage du fluide)
    H_c: float = 4.5        # m (hauteur géométrique du cœur)
    Kg_c: float = 2.5       # Coefficient de perte de charge (sans dim.)
    rho_c: float = 720.0    # kg/m^3 (masse volumique eau ~310°C/155 bar)
    g: float = 9.81         # m/s^2 (accélération de la pesanteur)
    h_1e_c: float = 1241e3  # J/kg (enthalpie d'entrée nominale = sortie pompe)
    P_1e_c: float = 155e5   # Pa (pression d'entrée nominale)
    m_dot_1_c: float = 26104.0  # kg/s (débit massique nominal)
    h_1s_c: float = 1241e3  # J/kg (enthalpie de sortie nominale)
    P_1s_c: float = 154.5e5 # Pa (pression de sortie nominale)
    Qf: float = 3800e6      # W (puissance fission nominale)
@dataclass
class GVConfig:
    V_gv: float = 15.0      # m^3 (volume primaire dans le GV)
    S_gv: float = 4.0       # m^2 (section de passage primaire)
    H_gv: float = 10.0      # m (hauteur géométrique du GV)
    Kg_gv: float = 3.0      # Coefficient de perte de charge (sans dim.)
    rho_gv: float = 720.0   # kg/m^3 (masse volumique primaire)
    g: float = 9.81         # m/s^2 (accélération de la pesanteur)
    h_1e_gv: float = 1550e3 # J/kg (enthalpie d'entrée nominale = sortie cœur)
    P_1e_gv: float = 154.5e5  # Pa (pression d'entrée nominale)
    m_dot_1_gv: float = 26104.0  # kg/s (débit massique nominal)
    h_1s_gv: float = 1241e3 # J/kg (enthalpie de sortie nominale = entrée pompe)
    P_1s_gv: float = 154.0e5  # Pa (pression de sortie nominale)
@dataclass
class PressuriseurConfig:
    V_press: float = 40.0   # m^3 (volume total du pressuriseur)
    S_press: float = 0.05   # m^2 (section hydraulique de la surge line)
    H_press: float = 10.0   # m (longueur hydraulique de la surge line)
    Kg_press: float = 200.0 # Coefficient de perte de charge surge line (sans dim.)
    g: float = 9.81         # m/s^2 (accélération de la pesanteur)
    Q_res_max: float = 1.8e6  # W (puissance maximale des résistances)
    P_set: float = 155e5    # Pa (pression de consigne)
    e_max: float = 5e5      # Pa (plage de régulation des résistances)
    Ksp: float = 5e-3       # Coefficient de débit du spray
    P_sp_on: float = 156e5  # Pa (seuil d'enclenchement du spray)
    Ksv: float = 2e-3       # Coefficient de débit de la soupape
    P_sv: float = 165e5     # Pa (seuil d'ouverture de la soupape de sûreté)
    Q_pertes: float = 5e4   # W (pertes thermiques par la paroi)
    P_press: float = 155e5  # Pa (pression interne nominale)
    V_L: float = 24.0       # m^3 (volume liquide nominal ~60% du total)