"""
scenarios/simu_turbo_alternateur.py
====================================

Fait tourner le turbo-alternateur seul sur une durée donnée et trace
l'évolution de N, Q_e et C_a en fonction du temps.

Notations conformes au Rapport Relaxation 3NC (§5.4.5, §5.6.5, §5.6.7, Table 5).

Scénario simulé :
  - 0 à 20 s  : réseau infini nominal (N figée à N⁰ = 1500 tr/min)
  - 20 s      : décrochage réseau → passage en ilotage (reseau_infini = False)
                Les couples C_{TH} + C_{TB} sont maintenus nominaux au moment
                du décrochage, puis réduits progressivement (fermeture vannes)
  - 20 à 60 s : ilotage — évolution libre de N
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math
import matplotlib.pyplot as plt
from Equipements.turbo_alternateur import TurboAlternateur

# ============================================================
# PARAMETRES DE SIMULATION
# ============================================================
DUREE = 60.0    # durée totale simulée   (s)
DT    = 0.05    # pas de temps           (s)

# Couples nominaux Paluel précalculés (Rapport §5.6.7, Table 5)
# ω⁰ = 2π·N⁰/60  ;  C⁰_u = Q⁰_e / ω⁰
_omega0 = 2.0 * math.pi * 1500.0 / 60.0
C0_u    = 1300e6 / _omega0          # C⁰_u ≈ 8.28×10⁶ N·m
C0_TH   = 0.215 * C0_u             # K'_{HP} = 0.215 (Rapport Table 5)
C0_TB   = 0.785 * C0_u             # K'_{BP} = 0.785 (Rapport Table 5)

# Entrées nominales de base
ENTREES = {
    'C_TH':          C0_TH,   # C_{TH} nominal   (N·m)
    'C_TB':          C0_TB,   # C_{TB} nominal   (N·m)
    'reseau_infini':  True,
}

# ============================================================
# --- 1. Créer le turbo-alternateur ---
ta = TurboAlternateur('TA')

# --- 2. Boucle de simulation ---
N_pas = int(DUREE / DT)

t_hist  = []
N_hist  = []
Qe_hist = []
Ca_hist = []

t = 0.0
for i in range(N_pas):
    entrees_courantes = dict(ENTREES)

    # Phase 1 : 0–20 s → réseau infini nominal
    if t <= 20.0:
        entrees_courantes['reseau_infini'] = True
        entrees_courantes['C_TH'] = C0_TH
        entrees_courantes['C_TB'] = C0_TB

    # Phase 2 : t > 20 s → ilotage
    # Baisse progressive des couples sur 15 s après le décrochage
    else:
        entrees_courantes['reseau_infini'] = False
        if t < 35.0:
            facteur = 1.0 - 0.6 * (t - 20.0) / 15.0   # de 1.0 à 0.4
        else:
            facteur = 0.4
        entrees_courantes['C_TH'] = C0_TH * facteur
        entrees_courantes['C_TB'] = C0_TB * facteur

    ta.step(DT, entrees_courantes)

    t_hist.append(t)
    N_hist.append(ta.N)
    Qe_hist.append(ta.Q_e / 1e6)    # W → MW
    Ca_hist.append(ta.C_a / 1e6)    # N·m → MN·m
    t += DT

# --- 3. Tracer les courbes ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

ax1.plot(t_hist, N_hist, 'b-', linewidth=1.5)
ax1.set_ylabel(r'$N$ (tr/min)')
ax1.set_title(f'Simulation TurboAlternateur sur {DUREE} s — décrochage réseau à 20 s')
ax1.axvline(20, color='red', linestyle='--', linewidth=0.8, label='décrochage réseau')
ax1.axhline(1500, color='gray', linestyle=':', linewidth=0.8, label=r'$N^0$ = 1500 tr/min')
ax1.legend(fontsize=8)
ax1.grid(True)

ax2.plot(t_hist, Qe_hist, 'r-', linewidth=1.5)
ax2.set_ylabel(r'$Q_e$ (MW)')
ax2.axvline(20, color='red', linestyle='--', linewidth=0.8)
ax2.axhline(1300, color='gray', linestyle=':', linewidth=0.8, label=r'$Q^0_e$ = 1300 MW')
ax2.legend(fontsize=8)
ax2.grid(True)

ax3.plot(t_hist, Ca_hist, 'g-', linewidth=1.5)
ax3.set_ylabel(r'$C_a$ (MN·m)')
ax3.set_xlabel('temps (s)')
ax3.axvline(20, color='red', linestyle='--', linewidth=0.8)
ax3.grid(True)

plt.tight_layout()

# --- 4. Sauvegarder et afficher ---
os.makedirs('resultats', exist_ok=True)
plt.savefig('resultats/simu_turbo_alternateur.png', dpi=150)
print("Courbe sauvegardée dans resultats/simu_turbo_alternateur.png")
plt.show()
