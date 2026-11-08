"""
scenarios/simu_pressuriseur_derivation.py
=========================================
Situation 4 : pressuriseur en dérivation du cœur, comme dans une
centrale réelle. Le pressuriseur impose la pression à l'entrée du
cœur et doit maintenir l'eau primaire à l'état liquide malgré les
perturbations (variation de Qf, puis perte de débit).

Le pressuriseur utilisé est la version complète (Eq 25-27) avec la
correction de friction signée |ṁ|·ṁ qui assure la stabilité.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from math import tanh

from Equipements.coeur import Coeur
from parametres.dataclasses import CoeurConfig, PressuriseurConfig
from fluides.eau_iapws import proprietes_saturation, T_Ph, T_sat


class PressuriseurStable:
    """Pressuriseur complet (Eq 25-27) avec friction signée |ṁ|·ṁ."""
    def __init__(self, config=None):
        if config is None:
            config = PressuriseurConfig()
        self.V_press = config.V_press; self.S_press = config.S_press
        self.H_press = config.H_press; self.Kg_press = config.Kg_press
        self.Q_res_max = config.Q_res_max; self.P_set = config.P_set
        self.e_max = config.e_max; self.Ksp = config.Ksp
        self.P_sp_on = config.P_sp_on; self.Ksv = config.Ksv
        self.P_sv = config.P_sv; self.Q_pertes = config.Q_pertes
        self.P_press = config.P_press; self.V_L = config.V_L
        self.m_surge = 0.0; self.Q_res = 0.0; self.m_sp = 0.0; self.m_sv = 0.0

    def step(self, dt, h_chaud, P_chaud, h_froid):
        P = self.P_press; V_L = self.V_L; V_V = self.V_press - V_L
        rho_L, rho_V, h_L, h_V, rhoP_L, rhoP_V, hP_L, hP_V = proprietes_saturation(P)
        sigma = 0.5 * (1.0 + tanh(2.0 * (self.P_set - P) / self.e_max))
        self.Q_res = self.Q_res_max * sigma
        self.m_sp = self.Ksp * (P - P_chaud)**0.5 if (P >= self.P_sp_on and P > P_chaud) else 0.0
        self.m_sv = self.Ksv * (P - self.P_sv)**0.5 if P >= self.P_sv else 0.0
        # Friction SIGNÉE |ṁ|·ṁ (correction de stabilité)
        pertes = self.Kg_press * abs(self.m_surge) * self.m_surge / (2 * rho_L * self.S_press**2)
        dm = (self.S_press / self.H_press) * ((P_chaud - P) - pertes)
        self.m_surge = max(-500, min(self.m_surge + dt * dm, 500))
        a11 = rho_L - rho_V; a12 = rhoP_L * V_L + rhoP_V * V_V
        b1 = self.m_surge + self.m_sp - self.m_sv
        a21 = rho_L * h_L - rho_V * h_V
        a22 = (rhoP_L*h_L + rho_L*hP_L)*V_L + (rhoP_V*h_V + rho_V*hP_V)*V_V
        b2 = self.m_surge*h_chaud + self.m_sp*h_froid - self.m_sv*h_V + self.Q_res - self.Q_pertes
        det = a11*a22 - a12*a21
        if abs(det) < 1e-6: det = 1e-6 if det >= 0 else -1e-6
        dVL = (b1*a22 - b2*a12)/det; dP = (a11*b2 - a21*b1)/det
        self.V_L += dt*dVL; self.P_press += dt*dP
        self.P_press = max(1e5, min(self.P_press, 200e5))
        self.V_L = max(0.01*self.V_press, min(self.V_L, 0.99*self.V_press))


# ============================================================
DT, DUREE = 0.05, 120.0
DEBIT_NOM = 26104.0
# ============================================================

cfg_c = CoeurConfig(); cfg_c.h_1s_c = 1241e3
coeur = Coeur('coeur', config=cfg_c)
pr = PressuriseurStable()

N = int(DUREE / DT)
t_h, Qf_l, mdot_l = [], [], []
hsc, Psc, Tsc = [], [], []
Ppress, Qres, msp, msv = [], [], [], []
Tsat155 = T_sat(155e5) - 273.15

t = 0.0
for i in range(N):
    Qf = 3800e6
    if 30 <= t < 60:
        Qf = 3800e6 * 1.20          # +20 % de puissance entre 30 et 60 s
    m = DEBIT_NOM
    if t >= 90:
        m = DEBIT_NOM * 0.6          # -40 % de débit à partir de 90 s

    # Le pressuriseur impose sa pression à l'entrée du cœur
    coeur.step(DT, {'h_1e_c': 1241e3, 'P_1e_c': pr.P_press, 'm_dot_1_c': m, 'Qf': Qf})
    # Le pressuriseur lit la sortie du cœur
    pr.step(DT, coeur.h_1s_c, coeur.P_1s_c, 1241e3)

    t_h.append(t); Qf_l.append(Qf/1e6); mdot_l.append(m/1000)
    hsc.append(coeur.h_1s_c/1e3); Psc.append(coeur.P_1s_c/1e5)
    try:
        Tsc.append(T_Ph(coeur.P_1s_c, coeur.h_1s_c) - 273.15)
    except Exception:
        Tsc.append(float('nan'))
    Ppress.append(pr.P_press/1e5); Qres.append(pr.Q_res/1e6)
    msp.append(pr.m_sp); msv.append(pr.m_sv)
    t += DT

fig, axs = plt.subplots(5, 1, figsize=(11, 14), sharex=True)
fig.suptitle("Pressuriseur en dérivation du cœur — maintien de l'eau à l'état liquide sous perturbations (projet 3NC)",
             fontsize=12.5, fontweight='bold', y=0.99)

axs[0].plot(t_h, Qf_l, 'purple', lw=1.8)
ax0b = axs[0].twinx(); ax0b.plot(t_h, mdot_l, 'brown', lw=1.8)
axs[0].set_ylabel("Qf (MW)", color='purple', fontsize=10)
ax0b.set_ylabel("débit (×10³ kg/s)", color='brown', fontsize=10)
axs[0].set_title("Perturbations imposées : Qf (+20% à 30-60s) et débit (−40% à 90s)", fontsize=10.5)
axs[0].grid(True, alpha=0.4)
for x in [30, 60, 90]: axs[0].axvline(x, color='gray', ls=':', lw=1)

axs[1].plot(t_h, Tsc, 'r-', lw=1.8, label="T sortie cœur")
axs[1].axhline(Tsat155, color='orange', ls=':', lw=1.5, label=f"T_sat ({Tsat155:.0f}°C)")
axs[1].set_ylabel("Température\nT (°C)", fontsize=10)
axs[1].set_title("Température de sortie du cœur — doit rester sous T_sat (eau liquide)", fontsize=10.5)
axs[1].grid(True, alpha=0.4); axs[1].legend(loc='center right', fontsize=9)
for x in [30, 60, 90]: axs[1].axvline(x, color='gray', ls=':', lw=1)

axs[2].plot(t_h, hsc, 'b-', lw=1.8, label="h sortie cœur")
axs[2].set_ylabel("Enthalpie\nh (kJ/kg)", fontsize=10)
axs[2].set_title("Enthalpie de sortie du cœur", fontsize=10.5)
axs[2].grid(True, alpha=0.4); axs[2].legend(loc='center right', fontsize=9)
for x in [30, 60, 90]: axs[2].axvline(x, color='gray', ls=':', lw=1)

axs[3].plot(t_h, Ppress, 'k-', lw=1.8, label="P pressuriseur")
axs[3].plot(t_h, Psc, 'g-', lw=1.4, label="P sortie cœur")
axs[3].axhline(155, color='orange', ls=':', lw=1.2, label="Consigne 155 bar")
axs[3].set_ylabel("Pression\nP (bar)", fontsize=10)
axs[3].set_title("Pression : régulée par le pressuriseur", fontsize=10.5)
axs[3].grid(True, alpha=0.4); axs[3].legend(loc='center right', fontsize=9)
for x in [30, 60, 90]: axs[3].axvline(x, color='gray', ls=':', lw=1)

axs[4].plot(t_h, Qres, 'r-', lw=1.8, label="Q_res (MW)")
ax4b = axs[4].twinx()
ax4b.plot(t_h, msp, 'b-', lw=1.8, label="spray (kg/s)")
ax4b.plot(t_h, msv, 'm-', lw=1.8, label="soupape (kg/s)")
axs[4].set_ylabel("Q_res (MW)", color='r', fontsize=10)
ax4b.set_ylabel("débit (kg/s)", color='b', fontsize=10)
axs[4].set_xlabel("Temps (s)", fontsize=11)
axs[4].set_title("Éléments de contrôle du pressuriseur (résistances, spray, soupape)", fontsize=10.5)
axs[4].grid(True, alpha=0.4)
for x in [30, 60, 90]: axs[4].axvline(x, color='gray', ls=':', lw=1)
l1, la1 = axs[4].get_legend_handles_labels(); l2, la2 = ax4b.get_legend_handles_labels()
axs[4].legend(l1+l2, la1+la2, loc='center right', fontsize=9)

try:
    logo = mpimg.imread('logo_3nc.png')
    axl = fig.add_axes([0.81, 0.003, 0.12, 0.045], anchor='SE', zorder=10)
    axl.imshow(logo); axl.axis('off')
except Exception:
    pass

plt.tight_layout(rect=[0, 0.02, 1, 0.98])
plt.savefig('resultats/pressuriseur_derivation.png', dpi=125)
plt.show()