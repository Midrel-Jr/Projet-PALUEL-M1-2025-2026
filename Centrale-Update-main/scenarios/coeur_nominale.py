"""
scenarios/simu_coeur_nominal.py
===============================
Simulation nominale du cœur seul.
Trace enthalpie, pression et température (entrée/sortie) sur 60 s.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from Equipements.coeur import Coeur
from fluides.eau_iapws import T_Ph, T_sat
from parametres.dataclasses import CoeurConfig
cfg = CoeurConfig()
cfg.h_1s_c = 1241e3   # surcharge locale pour ce scénario
coeur = Coeur('coeur', config=cfg)

DUREE, DT = 60.0, 0.05
ENTREES = {'h_1e_c': 1241e3, 'P_1e_c': 155e5, 'm_dot_1_c': 26104.0, 'Qf': 3800e6}

coeur = Coeur('coeur')
N = int(DUREE / DT)
t_h, h_s, P_s, T_s = [], [], [], []
h_e = ENTREES['h_1e_c'] / 1e3
P_e = ENTREES['P_1e_c'] / 1e5
T_e = T_Ph(ENTREES['P_1e_c'], ENTREES['h_1e_c']) - 273.15

t = 0.0
for i in range(N):
    coeur.step(DT, ENTREES)
    t_h.append(t)
    h_s.append(coeur.h_1s_c / 1e3)
    P_s.append(coeur.P_1s_c / 1e5)
    try:
        T_s.append(T_Ph(coeur.P_1s_c, coeur.h_1s_c) - 273.15)
    except Exception:
        T_s.append(float('nan'))
    t += DT

h_e_l = [h_e] * N
P_e_l = [P_e] * N
T_e_l = [T_e] * N

fig, axs = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
fig.suptitle("Simulation nominale du cœur — Centrale de Paluel (projet 3NC)",
             fontsize=14, fontweight='bold', y=0.98)

axs[0].plot(t_h, h_e_l, 'b--', lw=1.5, label="Entrée (h₁ₑ,c)")
axs[0].plot(t_h, h_s, 'b-', lw=1.8, label="Sortie (h₁ₛ,c)")
axs[0].set_ylabel("Enthalpie massique\nh (kJ/kg)", fontsize=11)
axs[0].set_title("Enthalpie d'entrée et de sortie du fluide primaire", fontsize=11)
axs[0].grid(True, alpha=0.4); axs[0].legend(loc='center right')

axs[1].plot(t_h, P_e_l, 'g--', lw=1.5, label="Entrée (P₁ₑ,c)")
axs[1].plot(t_h, P_s, 'g-', lw=1.8, label="Sortie (P₁ₛ,c)")
axs[1].set_ylabel("Pression\nP (bar)", fontsize=11)
axs[1].set_title("Pression d'entrée et de sortie", fontsize=11)
axs[1].grid(True, alpha=0.4); axs[1].legend(loc='center right')

axs[2].plot(t_h, T_e_l, 'r--', lw=1.5, label="Entrée (T₁ₑ,c)")
axs[2].plot(t_h, T_s, 'r-', lw=1.8, label="Sortie (T₁ₛ,c)")
axs[2].axhline(T_sat(155e5) - 273.15, color='orange', ls=':', lw=1.5,
               label=f"T_sat ({T_sat(155e5)-273.15:.0f}°C)")
axs[2].set_ylabel("Température\nT (°C)", fontsize=11)
axs[2].set_xlabel("Temps (s)", fontsize=11)
axs[2].set_title("Température d'entrée et de sortie (via tables IAPWS-IF97)", fontsize=11)
axs[2].grid(True, alpha=0.4); axs[2].legend(loc='center right')

# Logo 3NC dans le coin (place logo_3nc.png a la racine du projet)
try:
    logo = mpimg.imread('logo_3nc.png')
    ax_logo = fig.add_axes([0.80, 0.005, 0.13, 0.06], anchor='SE', zorder=10)
    ax_logo.imshow(logo); ax_logo.axis('off')
except Exception:
    pass

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig('resultats/coeur_nominal.png', dpi=130)
plt.show()