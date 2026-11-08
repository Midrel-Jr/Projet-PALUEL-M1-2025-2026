"""
scenarios/simu_coeur.py
=======================

Fait tourner le cœur seul sur une durée donnée et trace
l'évolution de h_1s_c et P_1s_c en fonction du temps.

Utile pour observer la dynamique en isolation, avant l'assemblage
complet du primaire.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

from Equipements.coeur import Coeur


# ============================================================
# PARAMETRES DE SIMULATION (modifiables a la main)
# ============================================================
DUREE = 60.0     # duree totale simulee (s) -- change ici
DT    = 0.05     # pas de temps (s)

# Entrees nominales du coeur (constantes pour ce scenario)
ENTREES = {
    'h_1e_c':    1.40e6,    # J/kg
    'P_1e_c':    155e5,     # Pa
    'm_dot_1_c': 4700.0,    # kg/s
    'Qf':        3800e6,    # W
}
# ============================================================


# --- 1. Creer le coeur ---
coeur = Coeur('coeur1', V=20.0, S=4.0, H=4.5, Kg=10.0)

# --- 2. Boucle de simulation ---
N_pas = int(DUREE / DT)

t_hist     = []
h_hist     = []
P_hist     = []

t = 0.0
for i in range(N_pas):
    #Faire baisser le debit a partir de t = 30s
    entrees_courantes = dict(ENTREES)
    if t > 30.0:
        # Transition progressive sur 5 secondes
        if t < 35.0:
        # Interpolation lineaire entre 4700 et 3500 sur 5 s
            entrees_courantes['m_dot_1_c'] = 4700.0 - (4700 - 3500) * (t - 30.0) / 5.0
        else:
            entrees_courantes['m_dot_1_c'] = 3500.0
    coeur.step(DT, entrees_courantes)

    t_hist.append(t)
    h_hist.append(coeur.h_1s_c / 1e6)   # conversion en MJ/kg pour lisibilite
    P_hist.append(coeur.P_1s_c / 1e5)   # conversion en bar

    t = t + DT

# --- 3. Tracer les courbes ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

ax1.plot(t_hist, h_hist, 'r-', linewidth=1.5)
ax1.set_ylabel('h_1s_c (MJ/kg)')
ax1.set_title(f'Evolution du coeur sur {DUREE} s -- Qf = {ENTREES["Qf"]/1e6:.0f} MW')
ax1.grid(True)

ax2.plot(t_hist, P_hist, 'b-', linewidth=1.5)
ax2.set_ylabel('P_1s_c (bar)')
ax2.set_xlabel('temps (s)')
ax2.grid(True)

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
plt.savefig('./resultats/simu_coeur.png', dpi=150)
print(f"Courbe sauvegardee dans ./resultats/simu_coeur.png")

plt.show()