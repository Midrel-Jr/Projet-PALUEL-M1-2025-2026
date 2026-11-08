"""
scenarios/simu_pompe.py
=======================

Scénario de défaillance : Fuite majeure sur la pompe à t = 30s.
Observe l'impact de la perte de débit et de l'augmentation de l'enthalpie
d'entrée sur le comportement du cœur.

Mettre les numéro des équations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

from Equipements.pompe import Pompe
from parametres.dataclasses import PompeConfig
from dataclasses import asdict
from math import sqrt


# ============================================================
# PARAMETRES DE SIMULATION
# ============================================================
DUREE = 60.0     # durée totale simulée (s)
DT    = 0.05     # pas de temps (s)

# Entrées nominales (avant la fuite)
ENTREES_NOMINALES = PompeConfig()

# Paramètres de la pompe pour calculer l'échauffement par friction
W_pompe = 7e6  # Puissance mécanique estimée de la pompe 
# ============================================================


# Création de la pompe
pompe = Pompe('pompe1')

# Boucle de simulation
N_pas = int(DUREE / DT)

t_hist     = []
h_hist     = []
P_hist     = []
m_dot_hist = []  # Pour suivre l'évolution du débit sur le graphique

t = 0.0
for i in range(N_pas):
    # On part des conditions nominales
    entrees_courantes = asdict(ENTREES_NOMINALES)
    
    if t >= 30.0:
        # 1. Effet de la fuite : Le débit utile qui va vers le cœur chute à 3200 kg/s
        DEBIT_FUITE = 0.67*2e-5*sqrt(2 * PompeConfig.rho_p * (PompeConfig.P_1e_p - 10e5))*(t-30.0)
        entrees_courantes['m_dot_1e_p'] = entrees_courantes['m_dot_1e_p'] - DEBIT_FUITE
        # 2. Effet thermodynamique : La pompe dissipe son énergie dans moins de débit.
        # L'enthalpie en sortie de pompe (qui est l'entrée du cœur) augmente.
        # Delta_h = W_pompe / m_dot
        h_sortie_fuite = PompeConfig.h_1e_p +  (PompeConfig.W_p /(entrees_courantes['m_dot_1e_p']))
        entrees_courantes['h_1e_p'] = h_sortie_fuite
    else:
        entrees_courantes['m_dot_1e_p'] =PompeConfig.m_dot_1e_p
        entrees_courantes['h_1e_p'] = PompeConfig.h_1e_p + PompeConfig.W_p/PompeConfig.m_dot_1e_p
    # Avancement de la simulation
    pompe.step(DT, entrees_courantes)

    # Sauvegarde de l'historique
    t_hist.append(t)
    h_hist.append(entrees_courantes['h_1e_p']*1e-3)   # Conversion en MJ/kg
    m_dot_hist.append(entrees_courantes['m_dot_1e_p'])

    t = t + DT

# --- 3. Tracer les courbes ---
# Ajout d'un 3ème graphique pour bien visualiser la chute de débit
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)

# Graphique 1 : Débit massique ( visualise la fuite )
ax1.plot(t_hist, m_dot_hist, 'g-', linewidth=1.5)
ax1.set_ylabel('Débit m_dot (kg/s)')
ax1.set_title(f'Scénario de FUITE POMPE à t=30s (W_p = {ENTREES_NOMINALES.W_p/1e6:.0f} MW)')
ax1.grid(True)

# Graphique 2 : Enthalpie de sortie du cœur ( effet "coup de massue" )
ax2.plot(t_hist, h_hist, 'r-', linewidth=1.5)
ax2.set_ylabel('h_1s_p (MJ/kg)')
ax2.grid(True)

# Graphique 3 : Pression en bar
'''ax3.plot(t_hist, P_hist, 'b-', linewidth=1.5)
ax3.set_ylabel('P_p (bar)')
ax3.set_xlabel('Temps (s)')
ax3.grid(True)'''

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
os.makedirs('resultats', exist_ok=True)
plt.savefig('resultats/simu_fuite_pompe.png', dpi=150)
print(f"Courbe de fuite sauvegardée dans ./resultats/simu_fuite_pompe.png")

plt.show()