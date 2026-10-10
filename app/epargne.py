"""Épargne : plan conseillé (US1), somme conseillée après un renoncement (US2),
bilan du mois et progression vers l'objectif (US3).

Fonctions pures : la date du jour est toujours reçue en paramètre.
Le produit proposé est une suggestion, jamais un conseil en investissement.
"""

from datetime import date
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from enum import Enum

from pydantic import BaseModel

from app.models import Objectif, Profil, Transaction
from app.regles import achats_en_ligne_du_mois, format_euros

SEUIL_LONG_TERME_MOIS = 5 * 12          # 5 ans ou plus = long terme
PART_CONSEILLEE = Decimal("0.5")        # on propose d'épargner 50 % du montant évité
MENTION_SUGGESTION = "Suggestion indicative, pas un conseil en investissement."
MENTION_PEA = "Placement en actions : le capital investi n'est pas garanti."


# --- Plan d'épargne conseillé ---

class Produit(str, Enum):
    LIVRET_A = "Livret A"
    PEA = "PEA"


class PlanEpargne(BaseModel):
    produit: Produit
    long_terme: bool
    mois_restants: int
    reste_a_epargner: Decimal
    versement_mensuel: Decimal
    message: str
    mentions: list[str]


def mois_entre(debut: date, fin: date) -> int:
    """Nombre de mois complets entre deux dates (10 oct. -> 10 nov. = 1 mois)."""
    mois = (fin.year - debut.year) * 12 + (fin.month - debut.month)
    if fin.day < debut.day:
        mois -= 1
    return mois


def arrondi_euro_superieur(montant: Decimal) -> Decimal:
    return montant.quantize(Decimal("1"), rounding=ROUND_CEILING)


def plan_conseille(objectif: Objectif, aujourd_hui: date) -> PlanEpargne:
    mois_restants = mois_entre(aujourd_hui, objectif.echeance)
    long_terme = mois_restants >= SEUIL_LONG_TERME_MOIS
    reste = max(objectif.montant - objectif.deja_epargne, Decimal("0"))
    # Au moins 1 mois, pour ne jamais diviser par zéro (échéance proche ou dépassée).
    mois_de_versement = max(mois_restants, 1)
    # Arrondi à l'euro supérieur : en versant ce montant, l'objectif est atteint à temps.
    versement = arrondi_euro_superieur(reste / mois_de_versement)

    if long_terme:
        produit = Produit.PEA
        pourquoi = "ton objectif est lointain : un placement en actions peut mieux rapporter sur la durée"
        mentions = [MENTION_SUGGESTION, MENTION_PEA]
    else:
        produit = Produit.LIVRET_A
        pourquoi = "ton argent reste disponible à tout moment et sans risque"
        mentions = [MENTION_SUGGESTION]

    if reste == 0:
        message = f"Bravo, ton objectif « {objectif.nom} » est atteint !"
    else:
        message = (
            f"Pour « {objectif.nom} », on te suggère un {produit.value} : {pourquoi}. "
            f"En versant {format_euros(versement)} par mois pendant {mois_de_versement} mois, "
            f"tu atteins ton objectif à temps."
        )

    return PlanEpargne(
        produit=produit,
        long_terme=long_terme,
        mois_restants=mois_restants,
        reste_a_epargner=reste,
        versement_mensuel=versement,
        message=message,
        mentions=mentions,
    )


# --- Après un renoncement : félicitations et somme conseillée ---

class PropositionEpargne(BaseModel):
    montant_evite: Decimal
    somme_conseillee: Decimal
    message: str


def somme_conseillee(montant_evite: Decimal, budget_restant: Decimal) -> Decimal:
    """50 % du montant évité, arrondi à l'euro inférieur, sans dépasser le budget en ligne restant."""
    moitie = (montant_evite * PART_CONSEILLEE).quantize(Decimal("1"), rounding=ROUND_FLOOR)
    return max(min(moitie, budget_restant), Decimal("0"))


def proposition_apres_renoncement(
    montant_evite: Decimal, budget_restant: Decimal, objectif: Objectif
) -> PropositionEpargne:
    somme = somme_conseillee(montant_evite, budget_restant)
    message = f"Bravo ! Tu viens d'éviter une dépense de {format_euros(montant_evite)}."
    if somme > 0:
        message += (
            f" Et si tu mettais {format_euros(somme)} de côté "
            f"pour ton objectif « {objectif.nom} » ?"
        )
    return PropositionEpargne(montant_evite=montant_evite, somme_conseillee=somme, message=message)


def budget_restant(profil: Profil, transactions: list[Transaction], aujourd_hui: date) -> Decimal:
    """Budget en ligne du mois en cours, moins les achats en ligne déjà faits (peut être négatif)."""
    depenses = sum(
        (t.montant for t in achats_en_ligne_du_mois(transactions, aujourd_hui.year, aujourd_hui.month)),
        Decimal("0"),
    )
    return profil.budget_en_ligne - depenses


# --- Bilan du mois et historique ---

class BilanMensuel(BaseModel):
    annee: int
    mois: int
    budget: Decimal
    depenses_en_ligne: Decimal
    economies: Decimal          # budget - dépenses, si positif
    budget_respecte: bool


def bilan_mensuel(profil: Profil, transactions: list[Transaction], annee: int, mois: int) -> BilanMensuel:
    depenses = sum((t.montant for t in achats_en_ligne_du_mois(transactions, annee, mois)), Decimal("0"))
    return BilanMensuel(
        annee=annee,
        mois=mois,
        budget=profil.budget_en_ligne,
        depenses_en_ligne=depenses,
        economies=max(profil.budget_en_ligne - depenses, Decimal("0")),
        budget_respecte=depenses <= profil.budget_en_ligne,
    )


def historique(profil: Profil, transactions: list[Transaction], aujourd_hui: date) -> list[BilanMensuel]:
    """Bilans des mois terminés (strictement avant le mois en cours), du plus ancien au plus récent."""
    mois_termines = sorted({
        (t.date_heure.year, t.date_heure.month) for t in transactions
        if (t.date_heure.year, t.date_heure.month) < (aujourd_hui.year, aujourd_hui.month)
    })
    return [bilan_mensuel(profil, transactions, annee, mois) for annee, mois in mois_termines]


# --- Verser vers l'objectif et suivre la progression ---

def epargner(objectif: Objectif, montant: Decimal) -> Objectif:
    """Renvoie un nouvel objectif avec le montant ajouté (tout, une partie, ou 0 = rien)."""
    if montant < 0:
        raise ValueError("Le montant à épargner ne peut pas être négatif.")
    return objectif.model_copy(update={"deja_epargne": objectif.deja_epargne + montant})


def progression(objectif: Objectif) -> int:
    """Pourcentage de l'objectif atteint, entre 0 et 100."""
    pourcentage = int(objectif.deja_epargne * 100 / objectif.montant)
    return min(pourcentage, 100)
