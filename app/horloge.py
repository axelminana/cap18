"""Horloge de Cap 18 : heure réelle ou heure simulée pour la démo.

Les fonctions métier ne lisent jamais l'heure elles-mêmes : elles reçoivent
« maintenant » en paramètre. Seule l'API utilise cette horloge pour le leur fournir.
Pendant la démo, on fixe l'heure (ex. 1 h du matin) puis on l'avance à la demande.
"""

from datetime import datetime, timedelta


class Horloge:
    def __init__(self, heure_fixee: datetime | None = None):
        # None = mode réel ; sinon = mode simulé, l'heure ne bouge que si on l'avance.
        self.heure_fixee = heure_fixee

    def maintenant(self) -> datetime:
        if self.heure_fixee is None:
            return datetime.now()
        return self.heure_fixee

    def est_simulee(self) -> bool:
        return self.heure_fixee is not None

    def fixer(self, heure: datetime) -> None:
        self.heure_fixee = heure

    def avancer(self, minutes: int) -> datetime:
        """Avance le temps (passe en mode simulé si on était en mode réel)."""
        if minutes <= 0:
            raise ValueError("On ne peut avancer le temps que d'un nombre de minutes positif.")
        self.heure_fixee = self.maintenant() + timedelta(minutes=minutes)
        return self.heure_fixee

    def aller_au_mois_suivant(self) -> datetime:
        """Saute au 1er du mois suivant à 9 h, pour afficher le bilan du mois écoulé."""
        actuel = self.maintenant()
        if actuel.month == 12:
            self.heure_fixee = datetime(actuel.year + 1, 1, 1, 9, 0)
        else:
            self.heure_fixee = datetime(actuel.year, actuel.month + 1, 1, 9, 0)
        return self.heure_fixee

    def revenir_au_reel(self) -> None:
        self.heure_fixee = None
