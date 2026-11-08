"""
scenarios/simu_coeur_perturbation.py
====================================
Perturbation du cœur : perte brutale de débit d'entrée (-50%) à t=30 s.
On observe enthalpie, pression et température (entrée/sortie), pour
comparaison avec le régime nominal (situation 1).
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

# ============================================================
DUREE, DT   = 60.0, 0.05
T_PERTURB   = 30.0       # instant de la perte de débit (s)
DEBIT_NOM   = 26104.0    # débit nominal (kg/s)
DEBIT_CHUTE = 0.5        # facteur de chute (50 % du nominal)
# ============================================================

coeur = Coeur('coeur')
N = int(DUREE / DT)
t_h, h_s, P_s, T_s, mdot_l = [], [], [], [], []

h_e = 1241e3 / 1e3                       # enthalpie entrée (kJ/kg)
P_e = 155.0                              # pression entrée (bar)
T_e = T_Ph(155e5, 1241e3) - 273.15       # température entrée (°C)

t = 0.0
for i in range(N):
    # Perte brutale de débit à T_PERTURB
    m = DEBIT_NOM * (DEBIT_CHUTE if t >= T_PERTURB else 1.0)
    ENTREES = {'h_1e_c': 1241e3, 'P_1e_c': 155e5, 'm_dot_1_c': m, 'Qf': 3800e6}
    coeur.step(DT, ENTREES)
    t_h.append(t)
    h_s.append(coeur.h_1s_c / 1e3)
    P_s.append(coeur.P_1s_c / 1e5)
    mdot_l.append(m / 1000)              # en ×10³ kg/s
    try:
        T_s.append(T_Ph(coeur.P_1s_c, coeur.h_1s_c) - 273.15)
    except Exception:
        T_s.append(float('nan'))
    t += DT

fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
fig.suptitle("Perturbation du cœur — perte brutale de débit (−50%) à t = 30 s (projet 3NC)",
             fontsize=13, fontweight='bold', y=0.985)

axs[0].plot(t_h, mdot_l, 'purple', lw=2)
axs[0].axvline(T_PERTURB, color='gray', ls=':', lw=1.2)
axs[0].set_ylabel("Débit\nṁ (×10³ kg/s)", fontsize=11)
axs[0].set_title("Perturbation imposée : débit d'entrée du cœur", fontsize=11)
axs[0].grid(True, alpha=0.4)

axs[1].axhline(h_e, color='b', ls='--', lw=1.3, label="Entrée (h₁ₑ,c)")
axs[1].plot(t_h, h_s, 'b-', lw=1.8, label="Sortie (h₁ₛ,c)")
axs[1].axvline(T_PERTURB, color='gray', ls=':', lw=1.2)
axs[1].set_ylabel("Enthalpie\nh (kJ/kg)", fontsize=11)
axs[1].set_title("Enthalpie d'entrée et de sortie", fontsize=11)
axs[1].grid(True, alpha=0.4); axs[1].legend(loc='center right')

axs[2].axhline(P_e, color='g', ls='--', lw=1.3, label="Entrée (P₁ₑ,c)")
axs[2].plot(t_h, P_s, 'g-', lw=1.8, label="Sortie (P₁ₛ,c)")
axs[2].axvline(T_PERTURB, color='gray', ls=':', lw=1.2)
axs[2].set_ylabel("Pression\nP (bar)", fontsize=11)
axs[2].set_title("Pression d'entrée et de sortie (noter le pic inertiel à t=30 s)", fontsize=11)
axs[2].grid(True, alpha=0.4); axs[2].legend(loc='center right')

axs[3].axhline(T_e, color='r', ls='--', lw=1.3, label="Entrée (T₁ₑ,c)")
axs[3].plot(t_h, T_s, 'r-', lw=1.8, label="Sortie (T₁ₛ,c)")
axs[3].axhline(T_sat(155e5) - 273.15, color='orange', ls=':', lw=1.5,
               label=f"T_sat ({T_sat(155e5)-273.15:.0f}°C)")
axs[3].axvline(T_PERTURB, color='gray', ls=':', lw=1.2)
axs[3].set_ylabel("Température\nT (°C)", fontsize=11)
axs[3].set_xlabel("Temps (s)", fontsize=11)
axs[3].set_title("Température d'entrée et de sortie (via tables IAPWS-IF97)", fontsize=11)
axs[3].grid(True, alpha=0.4); axs[3].legend(loc='center right')

try:
    logo = mpimg.imread('logo_3nc.png')
    axl = fig.add_axes([0.80, 0.004, 0.13, 0.05], anchor='SE', zorder=10)
    axl.imshow(logo); axl.axis('off')
except Exception:
    pass

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig('resultats/coeur_perturbation.png', dpi=130)
plt.show()