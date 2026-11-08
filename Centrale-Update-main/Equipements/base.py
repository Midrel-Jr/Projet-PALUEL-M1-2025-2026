# classe équipement
# Voici le language commun à tous les objets de notre centrale.
"""
equipements/base.py
===================

Classe parente abstraite de tous les équipements de la centrale.

Ce module définit la classe `Equipement`, qui sert de modèle commun à
toutes les classes du dossier `equipements/` (Pompe, Coeur, GV,
Pressuriseur, TurbineHP, TurbineBP, Condenseur, Arbre).

PRINCIPE
--------
Chaque équipement de la centrale est un objet Python qui sait :
  1. avancer son état interne d'un pas de temps dt (méthode `step`),
  2. raconter son état courant pour l'affichage (méthode `get_state`).

La classe `Equipement` ci-dessous est ABSTRAITE : on ne l'instancie
jamais directement. Toutes les classes filles DOIVENT en hériter et
DOIVENT implémenter `step` et `get_state`. Si elles oublient, Python
refusera de les instancier et lèvera une erreur explicite.

CE QUE LES CLASSES FILLES DOIVENT ÉCRIRE
----------------------------------------
- step(dt, entrees) -> dict
    Avance l'état de l'équipement de `dt` secondes en utilisant le
    dictionnaire `entrees` (grandeurs reçues du voisin amont).
    Renvoie un dictionnaire des grandeurs en sortie (vers le voisin
    aval). Ne modifie PAS `entrees` en place.

- get_state() -> dict
    Renvoie un dictionnaire contenant toutes les grandeurs internes
    visibles à l'utilisateur (pour le tooltip de l'interface).

CE QUE LES CLASSES FILLES RÉCUPÈRENT GRATUITEMENT
-------------------------------------------------
- self.nom : nom de l'instance (str), fixé au moment de la création.
- self.historique : liste qui accumule les états successifs
  (utilisée plus tard pour tracer les courbes du rapport).
- archive(t) : méthode qui ajoute l'état courant + le temps `t`
  dans `historique`. À appeler par la boucle principale après
  chaque pas de temps.

CONVENTION D'UNITÉS (STRICTE, SI PARTOUT DANS LE MOTEUR)
--------------------------------------------------------
- Pression       : Pascal (Pa)              -- PAS de bar
- Température    : Kelvin (K)               -- PAS de °C
- Enthalpie      : Joule par kg (J/kg)      -- PAS de kJ/kg
- Débit massique : kg/s
- Volume         : m^3
- Surface        : m^2
- Temps          : seconde (s)
- Puissance      : Watt (W)

La conversion en unités "lisibles" (bar, °C, MW...) se fait
UNIQUEMENT dans le module `interface/`, jamais ici.

CONVENTION DE NOMMAGE DES ENTRÉES / SORTIES
-------------------------------------------
Les clés des dictionnaires `entrees` et celui renvoyé par `step`
suivent la notation du document Equations_V2 (section 2.1).

Un nom de grandeur est composé de 4 morceaux, dans cet ordre :

    <grandeur>_<entrée/sortie><circuit>_<équipement>

  - <grandeur>          : h, P, m_dot, T, ... (TOUJOURS en majuscule
                          pour P et T, en minuscule pour h, afin
                          d'éviter toute confusion avec l'indice
                          d'équipement _p).
  - <entrée/sortie>     : 'e' pour entrée de l'équipement,
                          's' pour sortie.
  - <circuit>           : '1' primaire, '2' secondaire, '3' tertiaire.
  - <équipement>        : indice de l'équipement (voir tableau).

Indices d'équipements (repris du document Equations_V2) :
    _p   : pompe
    _c   : cœur + cuve
    _gv  : générateur de vapeur
    _pr  : pressuriseur
    _th  : turbine haute pression
    _tb  : turbine basse pression
    _cd  : condenseur

Exemple pour une pompe primaire (équations 1, 2, 3 du document) :

    entrees = {
        'h_1e_p'    : enthalpie entrée pompe, primaire    (J/kg),
        'P_1e_p'    : pression entrée pompe, primaire     (Pa),
        'm_dot_1e_p': débit entrée pompe, primaire        (kg/s),
    }

    sortie = {
        'h_1s_p'    : enthalpie sortie pompe, primaire    (J/kg),
        'P_1s_p'    : pression sortie pompe, primaire     (Pa),
        'm_dot_1s_p': débit sortie pompe, primaire        (kg/s),
    }

Cette convention reprend strictement les indices du document
Equations_V2, ce qui permet une traduction directe des équations
mathématiques en code Python (ṁ_1e,p devient m_dot_1e_p).

REMARQUE SUR LE BUS GLOBAL
--------------------------
À l'intérieur d'un équipement, on utilise les noms ci-dessus
(proches des équations). Sur le bus global (moteur/bus.py), une
autre notation à points est utilisée (ex: 'primaire.pompe_sortie.h')
pour décrire le câblage du circuit. La traduction entre les deux
est faite par moteur/reseau.py -- ce n'est PAS la responsabilité
de chaque équipement.

EXEMPLE MINIMAL D'UNE CLASSE FILLE
----------------------------------
    from equipements.base import Equipement

    class PompeBidon(Equipement):
        def __init__(self, nom):
            super().__init__(nom)
            self.h_1s_p = 1.40e6   # état initial (J/kg)

        def step(self, dt, entrees):
            self.h_1s_p = entrees['h_1e_p'] + 1000.0
            return {
                'h_1s_p'    : self.h_1s_p,
                'P_1s_p'    : entrees['P_1e_p'],
                'm_dot_1s_p': entrees['m_dot_1e_p'],
            }

        def get_state(self):
            return {'nom': self.nom, 'h_1s_p': self.h_1s_p}

Auteur : Midrel DJAMEN (équipe 3NC -- Solenn, Godwin, Midrel)
"""

from abc import ABC, abstractmethod
class Equipement(ABC):
    """Classe parente abstraite. Voir docstring du module."""

    def __init__(self, nom):
        self.nom = nom
        self.historique = []

    @abstractmethod
    def step(self, dt, entrees):
        """Avance l'état de dt secondes. Renvoie un dict des sorties."""
        pass

    @abstractmethod
    def get_state(self):
        """Renvoie un dict de toutes les grandeurs internes."""
        pass

    def archive(self, t):
        """Sauvegarde l'état courant dans l'historique."""
        etat = self.get_state()
        etat['t'] = t
        self.historique.append(etat)
