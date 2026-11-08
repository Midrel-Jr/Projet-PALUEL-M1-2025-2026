"""
scenarios/nominal.py
====================

Scénario nominal : simulation complète du circuit primaire (4 boucles).
Affiche les enthalpies, les températures (via tables IAPWS), et vérifie
que l'eau reste liquide tout au long de la simulation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

from Equipements.pompe import Pompe
from Equipements.coeur import Coeur
from Equipements.gv import GenerateurVapeur
from Equipements.pressuriseur import PressuriseurCouple
from moteur.bus import bus_initial_nominal
from moteur.reseau import reseau_primaire
from moteur.simulateur import Simulateur
from fluides.eau_iapws import T_Ph, T_sat


# ============================================================
DUREE = 60.0
DT    = 0.05
# ============================================================


# --- 1. Instancier les équipements (configs nominales par défaut) ---
equipements = {
    'pompe':        Pompe('pompe'),
    'coeur':        Coeur('coeur'),
    'gv':           GenerateurVapeur('gv'),
    'pressuriseur': PressuriseurCouple('pressuriseur'),   # ← version couplée
}

# --- 2. Bus initial et réseau ---
bus = bus_initial_nominal()
reseau = reseau_primaire()

# --- 3. Lancer la simulation ---
sim = Simulateur(equipements, reseau, bus_init=bus, dt=DT)
sim.run(duree=DUREE)
# Diagnostic du bilan d'énergie sur le dernier état
b = sim.bus_hist[-1]
print(f"h sortie pompe : {b['primaire.pompe_sortie.h']/1e6:.2f} MJ/kg")
print(f"h sortie coeur : {b['primaire.coeur_sortie.h']/1e6:.2f} MJ/kg")
print(f"h sortie GV    : {b['primaire.gv_sortie.h']/1e6:.2f} MJ/kg")
print(f"debit pompe    : {b['primaire.pompe_sortie.m_dot']:.0f} kg/s")
print(f"debit coeur    : {b['primaire.coeur_sortie.m_dot']:.0f} kg/s")
print(f"debit GV       : {b['primaire.gv_sortie.m_dot']:.0f} kg/s")

print(f"Simulation terminee : {len(sim.t_hist)} points archives.")

# --- 4. Extraire les enthalpies (MJ/kg) ---
t = sim.t_hist
h_entree_pompe = [b['primaire.gv_sortie.h'] / 1e6 for b in sim.bus_hist]
h_sortie_pompe = [b['primaire.pompe_sortie.h'] / 1e6 for b in sim.bus_hist]
h_sortie_coeur = [b['primaire.coeur_sortie.h'] / 1e6 for b in sim.bus_hist]
h_sortie_gv    = [b['primaire.gv_sortie.h'] / 1e6 for b in sim.bus_hist]

# --- Diagnostic des pressions ---
P_gv_all = [b['primaire.gv_sortie.P']/1e5 for b in sim.bus_hist]
P_coeur_all = [b['primaire.coeur_sortie.P']/1e5 for b in sim.bus_hist]
print(f"P_GV   : min={min(P_gv_all):.1f} bar, max={max(P_gv_all):.1f} bar")
print(f"P_coeur: min={min(P_coeur_all):.1f} bar, max={max(P_coeur_all):.1f} bar")

# --- 5. Calculer les températures via tables IAPWS (°C) ---
T_coeur = []
T_gv    = []
eau_liquide_partout = True

for b in sim.bus_hist:
    P_c = b['primaire.coeur_sortie.P']
    h_c = b['primaire.coeur_sortie.h']
    P_g = b['primaire.gv_sortie.P']
    h_g = b['primaire.gv_sortie.h']

    try:
        Tc = T_Ph(P_c, h_c)
        T_coeur.append(Tc - 273.15)
        if Tc >= T_sat(P_c):
            eau_liquide_partout = False
    except Exception:
        T_coeur.append(float('nan'))

    try:
        Tg = T_Ph(P_g, h_g)
        T_gv.append(Tg - 273.15)
        if Tg >= T_sat(P_g):
            eau_liquide_partout = False
    except Exception:
        T_gv.append(float('nan'))

# --- 6. Verdict eau liquide ---
print("\n" + "="*50)
if eau_liquide_partout:
    print("✓ L'eau est restee LIQUIDE pendant toute la simulation.")
else:
    print("✗ ATTENTION : ebullition detectee (eau pas toujours liquide) !")
print(f"  T sortie coeur finale : {T_coeur[-1]:.1f} °C")
print(f"  T sortie GV finale    : {T_gv[-1]:.1f} °C")
print(f"  T_sat a 154.5 bar     : {T_sat(154.5e5)-273.15:.1f} °C")
print("="*50 + "\n")

# --- Securite : aligner toutes les listes sur la longueur de t ---
n = len(t)
T_coeur = T_coeur[:n]
T_gv    = T_gv[:n]
h_entree_pompe = h_entree_pompe[:n]
h_sortie_pompe = h_sortie_pompe[:n]
h_sortie_coeur = h_sortie_coeur[:n]
h_sortie_gv    = h_sortie_gv[:n]

# --- 7. Tracer ---
fig, axs = plt.subplots(3, 1, figsize=(11, 11), sharex=True)

# Graphe 1 : les 4 enthalpies
axs[0].plot(t, h_entree_pompe, label='entree pompe (= sortie GV)')
axs[0].plot(t, h_sortie_pompe, label='sortie pompe')
axs[0].plot(t, h_sortie_coeur, label='sortie coeur')
axs[0].plot(t, h_sortie_gv, '--', label='sortie GV')
axs[0].set_ylabel('h (MJ/kg)')
axs[0].set_title(f'Circuit primaire nominal (4 boucles) sur {DUREE} s')
axs[0].grid(True); axs[0].legend()

# Graphe 2 : temperatures (avec ligne de saturation)
axs[1].plot(t, T_coeur, 'r-', label='T sortie coeur')
axs[1].plot(t, T_gv, 'b-', label='T sortie GV')
axs[1].axhline(T_sat(154.5e5)-273.15, color='orange', linestyle='--',
               label=f'T_sat ({T_sat(154.5e5)-273.15:.0f}°C)')
axs[1].set_ylabel('Temperature (°C)')
axs[1].grid(True); axs[1].legend()

# Graphe 3 : debit
m_dot = [b['primaire.coeur_sortie.m_dot'] for b in sim.bus_hist]
axs[2].plot(t, m_dot, 'm-')
axs[2].set_ylabel('debit coeur (kg/s)')
axs[2].set_xlabel('temps (s)')
axs[2].grid(True)

plt.tight_layout()
plt.savefig('resultats/nominal.png', dpi=150)
print("Courbe sauvegardee : resultats/nominal.png")
plt.show()