"""
scenarios/simu_pompe.py
=======================

Fait tourner la pompe seule sur une durée donnée et trace
l'évolution de h_1s_c et P_1s_c en fonction du temps.

Utile pour observer la dynamique en isolation, avant l'assemblage
complet du primaire.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

from Equipements.pompe import Pompe
from parametres.dataclasses import PompeConfig
from dataclasses import asdict

# ============================================================
# PARAMETRES DE SIMULATION (modifiables a la main)
# ============================================================
DUREE = 60.0     # duree totale simulee (s) -- change ici
DT    = 0.05     # pas de temps (s)

# Entrees nominales de la pompe (constantes pour ce scenario)

ENTREES = PompeConfig()
# ============================================================

# --- 1. Creer la pompe ---
pompe = Pompe('pompe1')

# --- 2. Boucle de simulation ---
N_pas = int(DUREE / DT)

t_hist     = []
mdot_hist     = []
P_hist     = []

t = 0.0

CONFIG = PompeConfig()


for i in range(N_pas):
    # copie propre de la config
    entrees_courantes = asdict(CONFIG)

    # variation du debit à partir de t = 30s
    if t > 30.0:
        entrees_courantes['m_dot_p'] = CONFIG.m_dot_1e_p-CONFIG.m_dot_1e_p*0.01*(t-30)
    else:
        entrees_courantes['m_dot_p'] = CONFIG.m_dot_1e_p
    pompe.step(DT, entrees_courantes)

    t_hist.append(t)
    mdot_hist.append(pompe.m_dot_1s_p)   # kg/s
    P_hist.append(pompe.H_p / 1e5)      # bar corrige

    t = t + DT


# --- 3. Tracer les courbes ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

ax1.plot(t_hist, mdot_hist, 'r-', linewidth=1.5)
ax1.set_ylabel('m_dot_p (kg/s)')

ax1.set_title(f'Evolution de la pompe sur {DUREE} s -- W_p = {CONFIG.W_p / 1e6:.0f} MW')

ax1.grid(True)

ax2.plot(t_hist, P_hist, 'b-', linewidth=1.5)
ax2.set_ylabel('P_p (bar)')
ax2.set_xlabel('temps (s)')
ax2.grid(True)

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
plt.savefig('./resultats/simu_pompe.png', dpi=150)
print("Courbe sauvegardee dans ./resultats/simu_pompe.png")

plt.show()