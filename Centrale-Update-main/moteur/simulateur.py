"""
moteur/simulateur.py
====================

Boucle principale de simulation.

Le simulateur prend les équipements, le réseau (câblage) et le bus
initial, puis fait avancer tous les équipements pas de temps après
pas de temps, en archivant l'historique pour les courbes.
"""


class Simulateur:
    """Orchestre la simulation du circuit."""

    def __init__(self, equipements, reseau, bus_init, dt=0.05):
        """
        Paramètres
        ----------
        equipements : dict
            {nom: instance d'équipement}
        reseau : list
            Liste ordonnée des étapes (cf. moteur/reseau.py).
        bus_init : dict
            État initial du bus (cf. moteur/bus.py).
        dt : float
            Pas de temps (s).
        """
        self.eq = equipements
        self.reseau = reseau
        self.bus = dict(bus_init)   # copie pour ne pas modifier l'original
        self.dt = dt
        self.t = 0.0

        self.t_hist = []
        self.bus_hist = []

    def pas(self):
        """Un pas de temps : tous les équipements avancent de dt."""
        for etape in self.reseau:
            nom_eq = etape['equipement']

            # Lire les entrées sur le bus (avec facteur multiplicateur optionnel)
            entrees = {}
            for k, v in etape['entrees'].items():
                if isinstance(v, tuple):
                    # (cle_bus, facteur) -- ex: ('primaire.pompe_sortie.m_dot', 4)
                    cle_bus, facteur = v
                    entrees[k] = self.bus[cle_bus] * facteur
                else:
                    entrees[k] = self.bus[v]

            sorties = self.eq[nom_eq].step(self.dt, entrees)

            for k, v in etape['sorties'].items():
                self.bus[v] = sorties[k]

        self.t = self.t + self.dt

    def archive(self):
        """Sauvegarde l'état courant du bus avec son timestamp."""
        self.t_hist.append(self.t)
        self.bus_hist.append(dict(self.bus))

    def run(self, duree, perturbation=None, archive_every=1):
        """Lance la simulation.

        Paramètres
        ----------
        duree : float
            Durée totale simulée (s).
        perturbation : fonction(t, bus, equipements) ou None
            Appelée à chaque pas avant l'avancement, pour modifier
            le bus ou les équipements (déclencher un incident).
        archive_every : int
            Archive un pas sur N (pour limiter la taille de l'historique).
        """
        N = int(duree / self.dt)
        for i in range(N):
            if perturbation is not None:
                perturbation(self.t, self.bus, self.eq)

            self.pas()

            if i % archive_every == 0:
                self.archive()