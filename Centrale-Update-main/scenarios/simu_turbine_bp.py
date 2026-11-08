"""
scenarios/simu_turbine_bp.py
============================

Fait tourner la turbine BP seule sur une durée donnée et trace
l'évolution de C_{TB}, ṁ_{2e,TB} et Ω_{TB} en fonction du temps.

Notations conformes au Rapport Relaxation 3NC (§5.4.5, §5.6.5, Table 5).

Scénario simulé :
  - 0 à 20 s  : régime nominal (P_{2e,TB} = 1.2 MPa)
  - 20 à 30 s : chute progressive de pression entrée TB vers 0.6 MPa
                (simule une baisse de production TH en amont)
  - 30 à 50 s : régime stabilisé à basse pression
  - 50 s      : déclenchement accéléromètre (fermeture rapide vanne TB)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib.pyplot as plt
from Equipements.turbine_bp import TurbineBP

# ============================================================
# PARAMETRES DE SIMULATION
# ============================================================
DUREE = 65.0    # durée totale simulée                (s)
DT    = 0.05    # pas de temps                        (s)

# Entrées nominales de base (Rapport §5.7, Table 3)
ENTREES = {
    'P_2e_TB':  1.2e6,   # P_{2e,TB} — pression nominale entrée corps TB  (Pa)
    'accel_TB': False,   # déclenchement accéléromètre                    (bool)
}

# ============================================================
# --- 1. Créer la turbine BP ---
tb = TurbineBP('TB')

# --- 2. Boucle de simulation ---
N_pas = int(DUREE / DT)

t_hist           = []
C_TB_hist        = []
m_dot_2e_TB_hist = []
Omega_TB_hist    = []

t = 0.0
for i in range(N_pas):
    entrees_courantes = dict(ENTREES)

    # Phase 1 : 0–20 s → régime nominal
    if t <= 20.0:
        entrees_courantes['P_2e_TB'] = 1.2e6

    # Phase 2 : 20–30 s → chute progressive de P_{2e,TB}
    elif t <= 30.0:
        entrees_courantes['P_2e_TB'] = 1.2e6 - (1.2e6 - 0.6e6) * (t - 20.0) / 10.0

    # Phase 3 : 30–50 s → stabilisation à basse pression
    elif t <= 50.0:
        entrees_courantes['P_2e_TB'] = 0.6e6

    # Phase 4 : t > 50 s → déclenchement accéléromètre
    else:
        entrees_courantes['P_2e_TB']  = 0.6e6
        entrees_courantes['accel_TB'] = True

    tb.step(DT, entrees_courantes)

    t_hist.append(t)
    C_TB_hist.append(tb.C_TB / 1e6)          # N·m → MN·m
    m_dot_2e_TB_hist.append(tb.m_dot_2e_TB)  # kg/s
    Omega_TB_hist.append(tb.Omega_TB)         # (−)
    t += DT

# --- 3. Tracer les courbes ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

ax1.plot(t_hist, C_TB_hist, 'r-', linewidth=1.5)
ax1.set_ylabel(r'$C_{TB}$ (MN·m)')
ax1.set_title(
    f'Simulation TurbineBP sur {DUREE} s\n'
    r'Chute $P_{2e,TB}$ (20–30 s) puis accéléromètre à 50 s'
)
ax1.axvline(20, color='gray', linestyle='--', linewidth=0.8, label=r'début chute $P_{2e,TB}$')
ax1.axvline(50, color='red',  linestyle='--', linewidth=0.8, label='accéléromètre')
ax1.legend(fontsize=8)
ax1.grid(True)

ax2.plot(t_hist, m_dot_2e_TB_hist, 'b-', linewidth=1.5)
ax2.set_ylabel(r'$\dot{m}_{2e,TB}$ (kg/s)')
ax2.axvline(20, color='gray', linestyle='--', linewidth=0.8)
ax2.axvline(50, color='red',  linestyle='--', linewidth=0.8)
ax2.grid(True)

ax3.plot(t_hist, Omega_TB_hist, 'g-', linewidth=1.5)
ax3.set_ylabel(r'$\Omega_{TB}$ (−)')
ax3.set_xlabel('temps (s)')
ax3.axvline(20, color='gray', linestyle='--', linewidth=0.8)
ax3.axvline(50, color='red',  linestyle='--', linewidth=0.8)
ax3.set_ylim(-0.05, 1.05)
ax3.grid(True)

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
os.makedirs('resultats', exist_ok=True)
plt.savefig('resultats/simu_turbine_bp.png', dpi=150)
print("Courbe sauvegardée dans resultats/simu_turbine_bp.png")
plt.show()
