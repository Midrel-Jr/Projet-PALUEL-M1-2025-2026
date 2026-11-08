"""
scenarios/simu_pressuriseur_derivation.py
=========================================
Situation 4 : pressuriseur en dérivation du cœur (centrale réelle).
Le pressuriseur impose la pression à l'entrée du cœur et régule
activement autour de 155 bar pour garder l'eau liquide, malgré :
  - une hausse de puissance Qf (+20 %) entre t=40 et t=80 s,
  - une perte de débit (-40 %) à partir de t=110 s.

On observe les sorties du cœur (T, h) et le travail des actionneurs
du pressuriseur (résistances, spray, soupape).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from math import tanh

from Equipements.coeur import Coeur
from parametres.dataclasses import CoeurConfig, PressuriseurConfig
from fluides.eau_iapws import proprietes_saturation, T_Ph, T_sat


class PressuriseurRegule:
    """Pressuriseur couplé au cœur avec régulation active de la pression.

    - Résistances : chauffent sous la consigne, se coupent au-dessus.
    - Spray : s'enclenche dès que P dépasse la consigne (condense la
      vapeur, fait redescendre la pression).
    - Soupape : sécurité ultime (seuil 165 bar).
    - Couplage thermique : la dilatation du fluide chaud venant du
      cœur pousse la pression (terme k_couplage), ce qui rend les
      perturbations visibles sur la pression.
    """

    def __init__(self, config=None, S_press=0.3, k_couplage=0.006):
        if config is None:
            config = PressuriseurConfig()
        self.V_press = config.V_press
        self.S_press = S_press                 # surge line élargie (couplage)
        self.H_press = config.H_press
        self.Kg_press = config.Kg_press
        self.Q_res_max = config.Q_res_max
        self.P_set = config.P_set
        self.e_max = config.e_max
        self.Ksp = config.Ksp * 3              # spray renforcé
        self.Ksv = config.Ksv
        self.P_sv = config.P_sv
        self.Q_pertes = config.Q_pertes
        self.P_press = config.P_press
        self.V_L = config.V_L
        self.m_surge = 0.0
        self.Q_res = 0.0
        self.m_sp = 0.0
        self.m_sv = 0.0
        self.k_couplage = k_couplage
        self.h_ref = 1387e3                    # enthalpie cœur nominale

    def step(self, dt, h_chaud, P_chaud, h_froid):
        P = self.P_press
        V_L = self.V_L
        V_V = self.V_press - V_L
        rho_L, rho_V, h_L, h_V, rhoP_L, rhoP_V, hP_L, hP_V = proprietes_saturation(P)

        ecart = self.P_set - P
        # Résistances : chauffent sous la consigne, coupées au-dessus
        if ecart >= 0:
            self.Q_res = self.Q_pertes + (self.Q_res_max - self.Q_pertes) * tanh(3 * ecart / self.e_max)
        else:
            self.Q_res = self.Q_pertes * max(0.0, 1 + 5 * ecart / self.e_max)
        # Spray : s'enclenche en surpression
        self.m_sp = self.Ksp * (P - self.P_set) ** 0.5 if P > self.P_set else 0.0
        # Soupape de sûreté
        self.m_sv = self.Ksv * (P - self.P_sv) ** 0.5 if P >= self.P_sv else 0.0

        # Surge line (friction signée |ṁ|·ṁ)
        pertes = self.Kg_press * abs(self.m_surge) * self.m_surge / (2 * rho_L * self.S_press**2)
        dm = (self.S_press / self.H_press) * ((P_chaud - P) - pertes)
        self.m_surge = max(-2000, min(self.m_surge + dt * dm, 2000))

        # Système 2x2 (masse + énergie)
        a11 = rho_L - rho_V
        a12 = rhoP_L * V_L + rhoP_V * V_V
        b1 = self.m_surge + self.m_sp - self.m_sv
        a21 = rho_L * h_L - rho_V * h_V
        a22 = (rhoP_L*h_L + rho_L*hP_L)*V_L + (rhoP_V*h_V + rho_V*hP_V)*V_V
        b2 = self.m_surge*h_chaud + self.m_sp*h_froid - self.m_sv*h_V + self.Q_res - self.Q_pertes
        det = a11*a22 - a12*a21
        if abs(det) < 1e-6:
            det = 1e-6 if det >= 0 else -1e-6
        dVL = (b1*a22 - b2*a12) / det
        dP = (a11*b2 - a21*b1) / det

        # Couplage thermique : dilatation du fluide chaud -> surpression
        dP_couplage = self.k_couplage * (h_chaud - self.h_ref)

        self.V_L += dt * dVL
        self.P_press += dt * (dP + dP_couplage)
        self.P_press = max(1e5, min(self.P_press, 200e5))
        self.V_L = max(0.01*self.V_press, min(self.V_L, 0.99*self.V_press))


def lisser(x, n=30):
    """Moyenne glissante sans effet de bord (pour l'affichage)."""
    x = np.array(x, dtype=float)
    xp = np.pad(x, (n, n), mode='edge')
    return np.convolve(xp, np.ones(n)/n, mode='same')[n:-n]


# ============================================================
DT, DUREE = 0.05, 150.0
DEBIT_NOM = 26104.0
# ============================================================

cfg_c = CoeurConfig(); cfg_c.h_1s_c = 1241e3
coeur = Coeur('coeur', config=cfg_c)
pr = PressuriseurRegule()

N = int(DUREE / DT)
t_h, Qf_l, mdot_l, hsc, Tsc = [], [], [], [], []
Ppress, Qres, msp, msv = [], [], [], []
Tsat155 = T_sat(155e5) - 273.15

t = 0.0
for i in range(N):
    Qf = 3800e6
    if 40 <= t < 80:
        Qf = 3800e6 * 1.20
    m = DEBIT_NOM
    if t >= 110:
        m = DEBIT_NOM * 0.6
    coeur.step(DT, {'h_1e_c': 1241e3, 'P_1e_c': pr.P_press, 'm_dot_1_c': m, 'Qf': Qf})
    pr.step(DT, coeur.h_1s_c, coeur.P_1s_c, 1241e3)

    t_h.append(t); Qf_l.append(Qf/1e6); mdot_l.append(m/1000)
    hsc.append(coeur.h_1s_c/1e3)
    try:
        Tsc.append(T_Ph(coeur.P_1s_c, coeur.h_1s_c) - 273.15)
    except Exception:
        Tsc.append(float('nan'))
    Ppress.append(pr.P_press/1e5); Qres.append(pr.Q_res/1e6)
    msp.append(pr.m_sp); msv.append(pr.m_sv)
    t += DT

# Lissage des signaux pour l'affichage
Ppress_s = lisser(Ppress)
Qres_s = lisser(Qres)
msp_s = lisser(msp)

fig, axs = plt.subplots(5, 1, figsize=(11, 14), sharex=True)
fig.suptitle("Pressuriseur en dérivation du cœur — régulation active sous perturbations (projet 3NC)",
             fontsize=12.5, fontweight='bold', y=0.99)

axs[0].plot(t_h, Qf_l, 'purple', lw=1.8)
ax0b = axs[0].twinx(); ax0b.plot(t_h, mdot_l, 'brown', lw=1.8)
axs[0].set_ylabel("Qf (MW)", color='purple', fontsize=10)
ax0b.set_ylabel("débit (×10³ kg/s)", color='brown', fontsize=10)
axs[0].set_title("Perturbations imposées : Qf (+20% à 40-80s) et débit (−40% à 110s)", fontsize=10.5)
axs[0].grid(True, alpha=0.4)
for x in [40, 80, 110]: axs[0].axvline(x, color='gray', ls=':', lw=1)

axs[1].plot(t_h, Tsc, 'r-', lw=1.8, label="T sortie cœur")
axs[1].axhline(Tsat155, color='orange', ls=':', lw=1.5, label=f"T_sat ({Tsat155:.0f}°C)")
axs[1].set_ylabel("Température\nT (°C)", fontsize=10)
axs[1].set_title("Température de sortie du cœur — reste sous T_sat (eau liquide)", fontsize=10.5)
axs[1].grid(True, alpha=0.4); axs[1].legend(loc='center right', fontsize=9)
for x in [40, 80, 110]: axs[1].axvline(x, color='gray', ls=':', lw=1)

axs[2].plot(t_h, hsc, 'b-', lw=1.8, label="h sortie cœur")
axs[2].set_ylabel("Enthalpie\nh (kJ/kg)", fontsize=10)
axs[2].set_title("Enthalpie de sortie du cœur", fontsize=10.5)
axs[2].grid(True, alpha=0.4); axs[2].legend(loc='center right', fontsize=9)
for x in [40, 80, 110]: axs[2].axvline(x, color='gray', ls=':', lw=1)

axs[3].plot(t_h, Ppress_s, 'k-', lw=1.8, label="P pressuriseur")
axs[3].axhline(155, color='orange', ls=':', lw=1.5, label="Consigne 155 bar")
axs[3].set_ylabel("Pression\nP (bar)", fontsize=10)
axs[3].set_title("Pression interne — écarts corrigés par les actionneurs", fontsize=10.5)
axs[3].grid(True, alpha=0.4); axs[3].legend(loc='upper right', fontsize=9)
axs[3].set_ylim(154.6, 155.4)
for x in [40, 80, 110]: axs[3].axvline(x, color='gray', ls=':', lw=1)

axs[4].plot(t_h, Qres_s, 'r-', lw=1.8, label="Q_res (MW)")
ax4b = axs[4].twinx()
ax4b.plot(t_h, msp_s, 'b-', lw=1.8, label="spray (kg/s)")
ax4b.plot(t_h, msv, 'm-', lw=1.8, label="soupape (kg/s)")
axs[4].set_ylabel("Q_res (MW)", color='r', fontsize=10)
ax4b.set_ylabel("débit (kg/s)", color='b', fontsize=10)
axs[4].set_xlabel("Temps (s)", fontsize=11)
axs[4].set_title("Éléments de contrôle du pressuriseur", fontsize=10.5)
axs[4].grid(True, alpha=0.4)
for x in [40, 80, 110]: axs[4].axvline(x, color='gray', ls=':', lw=1)
l1, la1 = axs[4].get_legend_handles_labels()
l2, la2 = ax4b.get_legend_handles_labels()
axs[4].legend(l1+l2, la1+la2, loc='upper right', fontsize=9)

try:
    logo = mpimg.imread('logo_3nc.png')
    axl = fig.add_axes([0.81, 0.003, 0.12, 0.045], anchor='SE', zorder=10)
    axl.imshow(logo); axl.axis('off')
except Exception:
    pass

plt.tight_layout(rect=[0, 0.02, 1, 0.98])
plt.savefig('resultats/pressuriseur_derivation.png', dpi=125)
plt.show()