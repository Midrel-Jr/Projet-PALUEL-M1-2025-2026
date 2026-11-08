"""
scenarios/simu_gv.py
====================
Fait tourner le GV (côté primaire) seul sur une durée donnée et trace
l'évolution de h_1s_gv et P_1s_gv en fonction du temps.
Utile pour observer la dynamique en isolation, avant l'assemblage
complet du primaire.

Les entrées sont celles qui arriveraient du cœur et du couplage
secondaire dans un circuit complet.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
from Equipements.gv import GenerateurVapeur

# ============================================================
# PARAMETRES DE SIMULATION (modifiables a la main)
# ============================================================
DUREE = 60.0     # duree totale simulee (s) -- change ici
DT    = 0.05     # pas de temps (s)

# Entrees nominales du GV (constantes pour ce scenario)
# Ces valeurs correspondent aux sorties nominales du coeur Paluel
ENTREES = {
    'h_1e_gv':    1.55e6,   # enthalpie entree primaire (J/kg) -- sortie coeur
    'P_1e_gv':    155.0e5,  # pression entree primaire  (Pa)   -- 155 bar
    'm_dot_1_gv': 4700.0,   # debit primaire            (kg/s)
    'Q_1e_gv':    966e6,    # puissance cedee secondaire(W)
}

# ============================================================
# --- 1. Creer le GV ---
gv = GenerateurVapeur('GV-1', V=11.0, S=0.20, H=4.0, rho=720.0, Kg=3.0)

# --- 2. Boucle de simulation ---
N_pas = int(DUREE / DT)

t_hist = []
h_hist = []
P_hist = []

t = 0.0

for i in range(N_pas):
    # Perturbation : faire baisser le debit a partir de t = 30 s
    # (meme scenario que simu_coeur pour faciliter la comparaison)
    entrees_courantes = dict(ENTREES)
    if t > 30.0:
        if t < 35.0:
            # Interpolation lineaire entre 4700 et 3500 sur 5 s
            entrees_courantes['m_dot_1_gv'] = 4700.0 - (4700 - 3500) * (t - 30.0) / 5.0
        else:
            entrees_courantes['m_dot_1_gv'] = 3500.0

    gv.step(DT, entrees_courantes)

    t_hist.append(t)
    h_hist.append(gv.h_1s_gv / 1e6)   # MJ/kg
    P_hist.append(gv.P_1s_gv / 1e5)   # bar

    t = t + DT

# --- 3. Tracer les courbes ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

ax1.plot(t_hist, h_hist, 'r-', linewidth=1.5)
ax1.set_ylabel('h_1s_gv (MJ/kg)')
ax1.set_title(
    f'Evolution du GV primaire sur {DUREE} s'
    f' -- Q_echange = {ENTREES["Q_1e_gv"]/1e6:.0f} MW'
)
ax1.grid(True)

ax2.plot(t_hist, P_hist, 'b-', linewidth=1.5)
ax2.set_ylabel('P_1s_gv (bar)')
ax2.set_xlabel('temps (s)')
ax2.grid(True)

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
os.makedirs('resultats', exist_ok=True)
plt.savefig('resultats/simu_gv.png', dpi=150)
print("Courbe sauvegardee dans resultats/simu_gv.png")
plt.show()
