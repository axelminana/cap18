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
POURCENTAGE_CONSEILLE = 50             # position par défaut du curseur : 50 % du montant évité
PAS_DU_CURSEUR = 5                      # le curseur avance de 5 % en 5 % (0, 5, 10… 100)
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
    elif objectif.echeance < aujourd_hui:
        message = (
            f"L'échéance de ton objectif « {objectif.nom} » est passée. "
            f"Tu as déjà épargné {format_euros(objectif.deja_epargne)} : choisis une nouvelle date "
            f"ou ajuste ton objectif."
        )
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
    pourcentage_conseille: int
    # Pour le curseur : pourcentage choisi -> somme à épargner, calculée ici et non en JavaScript.
    sommes_par_pourcentage: dict[int, Decimal]
    message: str


def somme_pour_pourcentage(montant_evite: Decimal, pourcentage: int, budget_restant: Decimal) -> Decimal:
    """Le pourcentage du montant évité, arrondi à l'euro inférieur, sans dépasser le budget en ligne restant."""
    part = (montant_evite * pourcentage / 100).quantize(Decimal("1"), rounding=ROUND_FLOOR)
    return max(min(part, budget_restant), Decimal("0"))


def somme_conseillee(montant_evite: Decimal, budget_restant: Decimal) -> Decimal:
    """La somme proposée par défaut : 50 % du montant évité."""
    return somme_pour_pourcentage(montant_evite, POURCENTAGE_CONSEILLE, budget_restant)


def sommes_par_pourcentage(montant_evite: Decimal, budget_restant: Decimal) -> dict[int, Decimal]:
    """Toutes les positions du curseur : {0: 0, 5: 4, 10: 8, …, 100: 89} pour 89 € évités."""
    return {
        pourcentage: somme_pour_pourcentage(montant_evite, pourcentage, budget_restant)
        for pourcentage in range(0, 101, PAS_DU_CURSEUR)
    }


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
    return PropositionEpargne(
        montant_evite=montant_evite,
        somme_conseillee=somme,
        pourcentage_conseille=POURCENTAGE_CONSEILLE,
        sommes_par_pourcentage=sommes_par_pourcentage(montant_evite, budget_restant),
        message=message,
    )


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


def mois_suivant(annee: int, mois: int) -> tuple[int, int]:
    return (annee + 1, 1) if mois == 12 else (annee, mois + 1)


def historique(profil: Profil, transactions: list[Transaction], aujourd_hui: date) -> list[BilanMensuel]:
    """Bilans des mois terminés (strictement avant le mois en cours), du plus ancien au plus récent.

    Tous les mois sont présents depuis la première transaction, même un mois sans aucun
    achat en ligne (c'est alors un mois réussi : tout le budget est économisé).
    """
    if not transactions:
        return []
    premiere = min(t.date_heure for t in transactions)
    courant = (premiere.year, premiere.month)
    bilans = []
    while courant < (aujourd_hui.year, aujourd_hui.month):
        bilans.append(bilan_mensuel(profil, transactions, *courant))
        courant = mois_suivant(*courant)
    return bilans


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


def objectif_atteint(objectif: Objectif) -> bool:
    return objectif.deja_epargne >= objectif.montant


def surplus(objectif: Objectif) -> Decimal:
    """Ce qui a été épargné au-delà de l'objectif (0 s'il n'est pas atteint)."""
    return max(objectif.deja_epargne - objectif.montant, Decimal("0"))


def echeance_depassee(objectif: Objectif, aujourd_hui: date) -> bool:
    """La date est passée alors que l'objectif n'est pas atteint : on propose de l'ajuster."""
    return not objectif_atteint(objectif) and objectif.echeance < aujourd_hui


def verifier_echeance(echeance: date, aujourd_hui: date) -> None:
    if echeance <= aujourd_hui:
        raise ValueError("Choisis une échéance dans le futur.")


def modifier_objectif(
    ancien: Objectif, nom: str, montant: Decimal, echeance: date, aujourd_hui: date
) -> Objectif:
    """Change le nom, le montant ou la date de l'objectif. Ce qui est déjà épargné est gardé."""
    verifier_echeance(echeance, aujourd_hui)
    return Objectif(nom=nom, montant=montant, echeance=echeance, deja_epargne=ancien.deja_epargne)


def nouvel_objectif(
    ancien: Objectif, nom: str, montant: Decimal, echeance: date, aujourd_hui: date
) -> Objectif:
    """Objectif atteint : on démarre le projet suivant, en reportant ce qui dépasse l'ancien objectif."""
    if not objectif_atteint(ancien):
        raise ValueError(f"Ton objectif « {ancien.nom} » n'est pas encore atteint.")
    verifier_echeance(echeance, aujourd_hui)
    return Objectif(nom=nom, montant=montant, echeance=echeance, deja_epargne=surplus(ancien))
