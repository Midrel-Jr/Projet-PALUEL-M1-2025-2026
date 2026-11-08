"""
scenarios/simu_turbine_hp.py
============================
Fait tourner la turbine HP seule sur une durée donnée et trace
l'évolution de P_2s_gv, C_TH et Omega_TH en fonction du temps.

Stratégie de simulation isolée :
  La TurbineHP seule ne peut pas utiliser sa régulation interne (qui a besoin
  de Q_e fournie par le TurboAlternateur). On pilote donc Omega_TH directement
  depuis l'extérieur, en passant accel_TH=False et en imposant Q_e = Q_ec
  (écart nul → régulation inactive). On provoque les événements en modifiant
  Omega_TH manuellement via une rampe, puis en déclenchant l'accéléromètre.

Scénario simulé :
  - 0  à 20 s : régime nominal, Omega_TH = 1.0
  - 20 à 25 s : fermeture progressive de la vanne TH  1.0 → 0.6  (délestage simulé)
  - 25 à 50 s : Omega_TH stable à 0.6
  - 50 s+     : déclenchement accéléromètre → fermeture exponentielle (tau_Omega_TH = 0.5 s)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib.pyplot as plt
from Equipements.turbine_hp import TurbineHP

# ============================================================
# PARAMETRES DE SIMULATION (modifiables a la main)
# ============================================================
DUREE = 70.0    # duree totale simulee (s)
DT    = 0.05    # pas de temps (s)

# ============================================================
# --- 1. Creer la turbine HP ---
th = TurbineHP('th1')

# --- 2. Boucle de simulation ---
N_pas = int(DUREE / DT)

t_hist           = []
P_2s_gv_hist     = []
C_TH_hist        = []
Omega_TH_hist    = []
m_dot_2e_TH_hist = []

t = 0.0
for i in range(N_pas):

    # ── Calcul des entrees selon la phase ────────────────────────────────
    # On passe Q_e = Q_ec à chaque pas → écart nul → régulation inactive.
    # On pilote Omega_TH depuis l'extérieur via accel_TH ou en forçant
    # l'ouverture après le step (Omega_TH est un attribut public).

    if t <= 20.0:
        # Phase 1 : nominal, vanne pleine ouverture
        accel       = False
        omega_cible = 1.0

    elif t <= 25.0:
        # Phase 2 : délestage — fermeture progressive 1.0 → 0.6 sur 5 s
        accel       = False
        omega_cible = 1.0 - 0.4 * (t - 20.0) / 5.0

    elif t <= 50.0:
        # Phase 3 : stabilisation à Omega_TH = 0.6
        accel       = False
        omega_cible = 0.6

    else:
        # Phase 4 : déclenchement accéléromètre — fermeture gérée par le code
        accel       = True
        omega_cible = None   # laisse le code gérer

    # Entrees : Q_e = Q_ec → régulation à écart nul (vanne pilotée manuellement)
    entrees = {
        'm_dot_2e_TB': 1500.0,
        'Omega_D':     0.0,
        'N':           1500.0,
        'Q_e':         1300e6,   # = Q_ec → dOmega/dt = 0 via régulation
        'Q_ec':        1300e6,
        'accel_TH':    accel,
    }

    # En dehors de l'accéléromètre, on impose Omega_TH directement
    if not accel and omega_cible is not None:
        th.Omega_TH = omega_cible

    th.step(DT, entrees)

    t_hist.append(t)
    P_2s_gv_hist.append(th.P_2s_gv / 1e5)        # Pa → bar
    C_TH_hist.append(th.C_TH / 1e6)               # N·m → MN·m
    Omega_TH_hist.append(th.Omega_TH)
    m_dot_2e_TH_hist.append(th.m_dot_2e_TH)       # kg/s
    t += DT

# --- 3. Tracer les courbes ---
fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
ax1, ax2, ax3, ax4 = axes

ax1.plot(t_hist, Omega_TH_hist, 'g-', linewidth=1.5)
ax1.set_ylabel('$\\Omega_{TH}$ (-)')
ax1.set_title('Simulation TurbineHP sur 70 s — délestage $\\Omega_{TH}$ : 1.0 → 0.6 puis fermeture vanne')
ax1.axvline(20, color='gray', linestyle='--', linewidth=0.8, label='début délestage')
ax1.axvline(50, color='red',  linestyle='--', linewidth=0.8, label='t = 50 s')
ax1.set_ylim(-0.05, 1.05)
ax1.legend(fontsize=8)
ax1.grid(True)

ax2.plot(t_hist, m_dot_2e_TH_hist, 'orange', linewidth=1.5)
ax2.set_ylabel('$\\dot{m}_{2e,TH}$ (kg/s)')
ax2.axvline(20, color='gray', linestyle='--', linewidth=0.8)
ax2.axvline(50, color='red',  linestyle='--', linewidth=0.8)
ax2.grid(True)

ax3.plot(t_hist, P_2s_gv_hist, 'b-', linewidth=1.5)
ax3.set_ylabel('$P_{2s,gv}$ (bar)')
ax3.axvline(20, color='gray', linestyle='--', linewidth=0.8)
ax3.axvline(50, color='red',  linestyle='--', linewidth=0.8)
ax3.grid(True)

ax4.plot(t_hist, C_TH_hist, 'r-', linewidth=1.5)
ax4.set_ylabel('$C_{TH}$ (MN·m)')
ax4.set_xlabel('temps (s)')
ax4.axvline(20, color='gray', linestyle='--', linewidth=0.8)
ax4.axvline(50, color='red',  linestyle='--', linewidth=0.8)
ax4.grid(True)

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
os.makedirs('resultats', exist_ok=True)
plt.savefig('resultats/simu_turbine_hp.png', dpi=150)
print("Courbe sauvegardee dans resultats/simu_turbine_hp.png")
plt.show()
