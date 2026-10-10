"""Tableau de score personnel (US4).

Strictement personnel : aucune comparaison avec d'autres utilisateurs.
Uniquement des encouragements : pas de badge négatif, un mois dépassé casse
simplement la série en cours.

Fonctions pures : la date du jour est reçue en paramètre.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.epargne import BilanMensuel, historique, progression
from app.paiement import Compte


class Badge(BaseModel):
    code: str
    nom: str
    description: str
    obtenu: bool


class Score(BaseModel):
    serie_en_cours: int                    # mois réussis consécutifs, jusqu'au dernier mois terminé
    meilleure_serie: int
    achats_evites: int
    montant_evite: Decimal
    total_epargne: Decimal                 # somme des versements faits dans l'appli
    progression: int                       # % de l'objectif atteint
    mois: list[BilanMensuel]               # mois terminés, du plus ancien au plus récent
    meilleur_mois: BilanMensuel | None
    ecart_mois_precedent: Decimal | None   # économies du dernier mois - celles du mois d'avant


def series(bilans: list[BilanMensuel]) -> tuple[int, int]:
    """Renvoie (série en cours, meilleure série) de mois où le budget est respecté."""
    en_cours = 0
    meilleure = 0
    for bilan in bilans:
        en_cours = en_cours + 1 if bilan.budget_respecte else 0
        meilleure = max(meilleure, en_cours)
    return en_cours, meilleure


def badges(score: Score) -> list[Badge]:
    """Tous les badges, obtenus ou non (ceux à débloquer sont affichés en grisé)."""
    return [
        Badge(code="premier_achat_evite", nom="Premier achat évité",
              description="Renoncer à un achat après la pause de réflexion.",
              obtenu=score.achats_evites >= 1),
        Badge(code="premier_mois_reussi", nom="Premier mois réussi",
              description="Terminer un mois sans dépasser son budget en ligne.",
              obtenu=score.meilleure_serie >= 1),
        Badge(code="trois_mois_de_suite", nom="3 mois de suite",
              description="Respecter son budget trois mois d'affilée.",
              obtenu=score.meilleure_serie >= 3),
        Badge(code="cent_euros", nom="100 € épargnés",
              description="Verser 100 € vers son objectif depuis l'appli.",
              obtenu=score.total_epargne >= 100),
        Badge(code="objectif_25", nom="Objectif à 25 %",
              description="Atteindre le quart de son objectif.",
              obtenu=score.progression >= 25),
        Badge(code="objectif_50", nom="Objectif à 50 %",
              description="Atteindre la moitié de son objectif.",
              obtenu=score.progression >= 50),
    ]


def calculer_score(compte: Compte, aujourd_hui: date) -> tuple[Score, list[Badge]]:
    bilans = historique(compte.profil, compte.transactions, aujourd_hui)
    en_cours, meilleure = series(bilans)

    avec_economies = [b for b in bilans if b.economies > 0]
    meilleur_mois = max(avec_economies, key=lambda b: b.economies) if avec_economies else None
    ecart = bilans[-1].economies - bilans[-2].economies if len(bilans) >= 2 else None

    score = Score(
        serie_en_cours=en_cours,
        meilleure_serie=meilleure,
        achats_evites=len(compte.achats_evites),
        montant_evite=sum((a.montant for a in compte.achats_evites), Decimal("0")),
        total_epargne=sum((v.montant for v in compte.versements), Decimal("0")),
        progression=progression(compte.profil.objectif),
        mois=bilans,
        meilleur_mois=meilleur_mois,
        ecart_mois_precedent=ecart,
    )
    return score, badges(score)
