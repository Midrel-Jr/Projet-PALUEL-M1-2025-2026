import sys
import os
from math import sqrt
from dataclasses import asdict
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Equipements.pompe import Pompe
from parametres.dataclasses import PompeConfig

# ============================================================
# PARAMETRES DE SIMULATION
# ============================================================
DUREE =500.0     # (s)
DT    = 0.005    # (s)

# Entrées nominales
ENTREES_NOMINALES = PompeConfig()
W_pompe = ENTREES_NOMINALES.W_p  
M_DOT_NOMINAL = PompeConfig.m_dot_1e_p

# --- NOUVEAUX PARAMETRES PHYSIQUES ---
V_systeme = 2.0       # Volume du tronçon de tuyauterie (m3)
Beta = 2e9            # Bulk modulus de l'eau (Pa) - compressibilité
P_ext = 1e5           # Pression extérieure (atmosphérique) (Pa)
Cd = 0.67             # Coefficient sans dim peut ê changé en fonction de la géomêtrie
Surface_breche_max = 2e-4  # Taille maximale de la brèche (m2) calculé pour un diamètre de 5 mm
# ============================================================

pompe = Pompe('pompe1')
N_pas = int(DUREE / DT)

# Historiques pour les graphiques
t_hist = []
h_hist = []
P_hist = []
m_dot_utile_hist = []
m_dot_fuite_hist = []

# Conditions initiales de l'équa-diff
t = 0.0
P_1s_p = PompeConfig.P_1e_p  # On commence à la pression nominale (Pa)

for i in range(N_pas):
    entrees_courantes = asdict(ENTREES_NOMINALES)
    rho = PompeConfig.rho_p
    
    if t >= 5.0:
        # 1. Évolution linéaire de la surface de la brèche (s'ouvre en 10 secondes) si on veut modifier la rapidité on change /10 par le temps en s
        facteur_ouverture = min(1.0, (t - 5.0) / 10.0)
        A_breche = Surface_breche_max * facteur_ouverture
        
        # 2. Débit de fuite dépendant de la PRESSION COURANTE P(t)
        if P_1s_p > P_ext:
            dot_m_1fuite_p = Cd * A_breche * sqrt(2 * rho * (P_1s_p - P_ext))
        else:
            dot_m_1fuite_p = 0.0
            
        # 3. ÉQUATION DIFFÉRENTIELLE (Résolution par la méthode d'Euler)
        # dP/dt = (Beta / (V * rho)) * (m_dot_in - m_dot_out)
        dot_m_1s_p = M_DOT_NOMINAL - dot_m_1fuite_p
        dot_m_1s_p = max(0.0, dot_m_1s_p) # Sécurité anti-débit négatif
        
        # Calcul de la dérivée d'Euler
        
        unbalance = M_DOT_NOMINAL - (dot_m_1s_p + dot_m_1fuite_p) 
        
        # Ici, on applique une baisse de pression proportionnelle à la perte de masse par la fuite :
        dP_dt = (Beta / (V_systeme * rho)) * (dot_m_1s_p) 
        
        P_1s_p = P_1s_p + dP_dt * DT
        P_1s_p = max(P_ext, P_1s_p) # La pression de sortie minimum est limité par la pression atmosphérique = équilibre

        
        #   Conservation de l'énergie :
        h_sortie_fuite = PompeConfig.h_1e_p + (W_pompe / dot_m_1s_p)
        entrees_courantes['h_1e_p'] = h_sortie_fuite
        entrees_courantes['m_dot_1s_p'] = dot_m_1s_p
        '''elif t >= 250.0 : #On image que la fuite est colmatée à t=250s soit au bout de 4min5s

        #On garde le débit final de la pompe
        dot_m_1s_p = dot_m_1s_p

        dP_dt = (Beta / (V_systeme * rho)) * (dot_m_1s_p)

        P_1s_p = P_1s_p + dP_dt * DT
        P_1s_p = max(P_ext, P_1s_p)

        h_sortie_fuite = PompeConfig.h_1e_p + (W_pompe / dot_m_1s_p)
        entrees_courantes['h_1e_p'] = h_sortie_fuite
        entrees_courantes['m_dot_1s_p'] = dot_m_1s_p'''
    
    else :
        dot_m_1fuite_p = 0.0
        dot_m_1s_p = M_DOT_NOMINAL
        entrees_courantes['m_dot_1s_p'] = M_DOT_NOMINAL
        entrees_courantes['h_1e_p'] = PompeConfig.h_1e_p + W_pompe / M_DOT_NOMINAL

    
    if 'P_1e_p' in entrees_courantes:
        entrees_courantes['P_1e_p'] = P_1s_p
        
    pompe.step(DT, entrees_courantes)

    #On sauvegarde les valeurs 
    t_hist.append(t)
    h_hist.append(entrees_courantes['h_1e_p'] * 1e-6)  # MJ/kg
    m_dot_utile_hist.append(dot_m_1s_p)     #kg/s
    m_dot_fuite_hist.append(dot_m_1fuite_p)     #kg/s
    P_hist.append(P_1s_p * 1e-5)                   # Bar

    t += DT

# ============================================================
# TRACÉ DES COURBES
# ============================================================
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 9), sharex=True)

# Graphe 1 : Débits Utile = va dans le coeur et fuite = va à l'exterrieur
ax1.plot(t_hist, m_dot_utile_hist, 'g-', label='Débit utile (vers cœur)')
ax1.plot(t_hist, m_dot_fuite_hist, 'r--', label='Débit de fuite')
ax1.set_ylabel('Débits (kg/s)')
ax1.set_title(f'Simulation Fuite Dynamique (Couplage Pression/Débit)')
ax1.legend()
ax1.grid(True)

# Graphe 2 : Pression interne de la pompe
ax3.plot(t_hist, P_hist, 'b-', linewidth=1.5)
ax3.set_ylabel('Pression Pompe (bar)')
ax3.set_xlabel('Temps (s)')
ax3.grid(True)

# Graphe 3 : Enthalpie de sortie de la pompe 
ax2.plot(t_hist, h_hist, 'm-', linewidth=1.5)
ax2.set_ylabel('Enthalpie h (MJ/kg)')
ax2.grid(True)

plt.tight_layout()
os.makedirs('resultats', exist_ok=True)
plt.savefig('resultats/simu_fuite_pompe.png', dpi=150)
print(f"Courbe de fuite sauvegardée dans ./resultats/Fuite_pression_pompe.png")