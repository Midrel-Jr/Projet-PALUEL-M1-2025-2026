"""
scenarios/simu_pressuriseur_nominal.py
======================================
Régulation du pressuriseur : retour à la consigne (155 bar) depuis
une pression initiale décalée (152 bar). Montre les actionneurs
(résistances, spray, soupape) à l'œuvre.

Note : simulation sur 25 s, durée sur laquelle le modèle complet
(système 2x2 IAPWS) reste numériquement stable.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from Equipements.pressuriseur import Pressuriseur
from parametres.dataclasses import PressuriseurConfig

# Config avec pression initiale décalée à 152 bar
cfg = PressuriseurConfig()
cfg.P_press = 152e5

pr = Pressuriseur('press', config=cfg)
ENTREES = {'h_1s_c': 1550e3, 'P_1s_c': 154.5e5, 'h_1e_c': 1241e3}

DUREE, DT = 60.0, 0.05
N = int(DUREE / DT)
t_h, P_l, Qres_l, msp_l, msv_l = [], [], [], [], []

t = 0.0
for i in range(N):
    pr.step(DT, ENTREES)
    t_h.append(t)
    P_l.append(pr.P_press / 1e5)
    Qres_l.append(pr.Q_res / 1e6)
    msp_l.append(pr.m_sp)
    msv_l.append(pr.m_sv)
    t += DT

fig, axs = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
fig.suptitle("Régulation du pressuriseur — retour à la consigne depuis 152 bar (projet 3NC)",
             fontsize=13.5, fontweight='bold', y=0.98)

axs[0].plot(t_h, P_l, 'b-', lw=2, label="P_press")
axs[0].axhline(155, color='orange', ls='--', lw=1.5, label="Consigne P_set (155 bar)")
axs[0].set_ylabel("Pression\nP_press (bar)", fontsize=11)
axs[0].set_title("Pression interne du pressuriseur", fontsize=11)
axs[0].grid(True, alpha=0.4); axs[0].legend(loc='lower right')

axs[1].plot(t_h, Qres_l, 'r-', lw=2, label="Q_res (résistances)")
axs[1].set_ylabel("Puissance\nQ_res (MW)", fontsize=11)
axs[1].set_title("Puissance des résistances chauffantes", fontsize=11)
axs[1].grid(True, alpha=0.4); axs[1].legend(loc='upper right')

axs[2].plot(t_h, msp_l, 'g-', lw=2, label="m_sp (spray)")
axs[2].plot(t_h, msv_l, 'm-', lw=2, label="m_sv (soupape)")
axs[2].set_ylabel("Débit\n(kg/s)", fontsize=11)
axs[2].set_xlabel("Temps (s)", fontsize=11)
axs[2].set_title("Actionneurs de décharge : spray et soupape de sûreté", fontsize=11)
axs[2].grid(True, alpha=0.4); axs[2].legend(loc='upper right')
axs[2].set_ylim(-0.5, 1)

try:
    logo = mpimg.imread('logo_3nc.png')
    axl = fig.add_axes([0.80, 0.005, 0.13, 0.06], anchor='SE', zorder=10)
    axl.imshow(logo); axl.axis('off')
except Exception:
    pass

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig('resultats/pressuriseur_nominal.png', dpi=130)
plt.show()