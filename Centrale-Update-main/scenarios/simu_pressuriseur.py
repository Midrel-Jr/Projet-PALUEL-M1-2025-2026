"""
scenarios/simu_pressuriseur.py
==============================

Fait tourner le pressuriseur seul sur une durée donnée et trace
l'évolution de P_press, V_L, et les actionneurs (Q_res, m_sp, m_sv)
en fonction du temps.

Permet d'observer la régulation de pression en isolation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

from Equipements.pressuriseur import Pressuriseur


# ============================================================
# PARAMETRES DE SIMULATION (modifiables a la main)
# ============================================================
DUREE = 60.0     # duree totale simulee (s)
DT    = 0.05     # pas de temps (s)

# Entrees nominales (par defaut, valeurs branche chaude nominales)
ENTREES = {
    'h_1s_c': 1.55e6,   # J/kg
    'P_1s_c': 154.5e5,  # Pa
    'h_1e_c': 1.40e6,   # J/kg
}
# ============================================================


# --- 1. Creer le pressuriseur ---
pr = Pressuriseur('press1', V_press=40.0, S_press=0.05, H_press=10.0)

# --- 2. Boucle de simulation avec perturbation ---
N_pas = int(DUREE / DT)

t_hist     = []
P_hist     = []
VL_hist    = []
Qres_hist  = []
msp_hist   = []
msv_hist   = []

t = 0.0
for i in range(N_pas):
    # Construire les entrees DE CE PAS DE TEMPS
    entrees_courantes = dict(ENTREES)

    # PERTURBATION : a t = 20 s, on baisse artificiellement la pression
    # de la branche chaude pour declencher une depressurisation
    if 20.0 < t < 25.0:
        entrees_courantes['P_1s_c'] = 150e5   # chute a 150 bar

    pr.step(DT, entrees_courantes)

    t_hist.append(t)
    P_hist.append(pr.P_press / 1e5)        # en bar
    VL_hist.append(pr.V_L)                  # en m^3
    Qres_hist.append(pr.Q_res / 1e6)       # en MW
    msp_hist.append(pr.m_sp)                # en kg/s
    msv_hist.append(pr.m_sv)                # en kg/s

    t = t + DT

# --- 3. Tracer les courbes ---
fig, axs = plt.subplots(4, 1, figsize=(10, 10), sharex=True)

axs[0].plot(t_hist, P_hist, 'b-', linewidth=1.5)
axs[0].axhline(155, color='gray', linestyle='--', label='consigne 155 bar')
axs[0].set_ylabel('P_press (bar)')
axs[0].set_title(f'Pressuriseur sur {DUREE} s -- perturbation a t=20s')
axs[0].grid(True); axs[0].legend()

axs[1].plot(t_hist, VL_hist, 'g-', linewidth=1.5)
axs[1].set_ylabel('V_L (m^3)')
axs[1].grid(True)

axs[2].plot(t_hist, Qres_hist, 'r-', linewidth=1.5, label='Q_res')
axs[2].set_ylabel('Q_res (MW)')
axs[2].grid(True); axs[2].legend()

axs[3].plot(t_hist, msp_hist, 'm-', linewidth=1.5, label='spray')
axs[3].plot(t_hist, msv_hist, 'k-', linewidth=1.5, label='soupape')
axs[3].set_ylabel('debit (kg/s)')
axs[3].set_xlabel('temps (s)')
axs[3].grid(True); axs[3].legend()

plt.tight_layout()
plt.savefig('resultats/simu_pressuriseur.png', dpi=150)
print(f"Courbe sauvegardee dans resultats/simu_pressuriseur.png")
plt.show()