"""Moteur de déclenchement de la pause de réflexion (US2).

evaluer_achat() est une fonction pure : elle reçoit l'achat tenté (avec son heure),
le profil et les transactions déjà acceptées, et renvoie une Decision.
Elle ne lit pas l'heure système et ne modifie rien.
"""

from datetime import timedelta
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from app.models import CATEGORIES_OBLIGATOIRES, Canal, Categorie, Profil, Transaction

# Achat nocturne : entre 23 h et 4 h, au-delà de 20 €.
HEURE_DEBUT_NUIT = 23
HEURE_FIN_NUIT = 4
SEUIL_NOCTURNE = Decimal("20")

# Catégories toujours mises en pause, même au premier achat.
CATEGORIES_TOUJOURS_EN_PAUSE = {Categorie.LIVRAISON_REPAS}

# Répétition : message renforcé à partir de la 2e commande sur 7 jours glissants.
SEUIL_REPETITION = 2
FENETRE_REPETITION = timedelta(days=7)

# Délai utilisé si la catégorie n'a pas de délai dans le profil.
DELAI_PAR_DEFAUT_MINUTES = 15

# Règles qui concernent un dépassement de limite (seules visées par le blocage strict).
REGLES_DE_LIMITE = {"limite_categorie", "budget_total"}


class Statut(str, Enum):
    ACCEPTE = "accepte"
    PAUSE = "pause"
    REFUSE = "refuse"


class RegleDeclenchee(BaseModel):
    code: str     # identifiant stable, utilisé par le front et les tests
    message: str  # explication en langage clair pour l'utilisateur


class Decision(BaseModel):
    statut: Statut
    regles: list[RegleDeclenchee] = []
    delai_minutes: int = 0


def format_euros(montant: Decimal) -> str:
    """89 -> « 89 € », 9.99 -> « 9,99 € »."""
    texte = f"{montant:.2f}".replace(".", ",")
    return texte.removesuffix(",00") + " €"


def est_achat_surveille(transaction: Transaction) -> bool:
    """Un achat compte dans le budget s'il est en ligne et non obligatoire."""
    return transaction.canal == Canal.EN_LIGNE and transaction.categorie not in CATEGORIES_OBLIGATOIRES


def est_la_nuit(achat: Transaction) -> bool:
    heure = achat.date_heure.hour
    return heure >= HEURE_DEBUT_NUIT or heure < HEURE_FIN_NUIT


def evaluer_achat(achat: Transaction, profil: Profil, transactions: list[Transaction]) -> Decision:
    # 1. Hors périmètre : achat en magasin ou dépense obligatoire.
    if not est_achat_surveille(achat):
        return Decision(statut=Statut.ACCEPTE)

    # Dépenses en ligne déjà acceptées pendant le mois de l'achat.
    du_mois = [
        t for t in transactions
        if est_achat_surveille(t)
        and t.date_heure.year == achat.date_heure.year
        and t.date_heure.month == achat.date_heure.month
    ]
    total_mois = sum((t.montant for t in du_mois), Decimal("0"))
    total_categorie = sum((t.montant for t in du_mois if t.categorie == achat.categorie), Decimal("0"))
    nom_categorie = achat.categorie.value.replace("_", " ")

    # 2. Calcul de toutes les règles déclenchées.
    regles: list[RegleDeclenchee] = []

    limite = profil.limites.get(achat.categorie)
    if limite is not None and total_categorie + achat.montant > limite:
        regles.append(RegleDeclenchee(
            code="limite_categorie",
            message=(
                f"Avec cet achat, tes dépenses « {nom_categorie} » passeraient à "
                f"{format_euros(total_categorie + achat.montant)} ce mois-ci, "
                f"au-delà de la limite de {format_euros(limite)} que tu t'es fixée."
            ),
        ))

    if total_mois + achat.montant > profil.budget_en_ligne:
        regles.append(RegleDeclenchee(
            code="budget_total",
            message=(
                f"Avec cet achat, tes achats en ligne passeraient à "
                f"{format_euros(total_mois + achat.montant)} ce mois-ci, "
                f"au-delà de ton budget de {format_euros(profil.budget_en_ligne)}."
            ),
        ))

    if est_la_nuit(achat) and achat.montant > SEUIL_NOCTURNE:
        regles.append(RegleDeclenchee(
            code="nocturne",
            message=(
                f"Il est {achat.date_heure.hour} h {achat.date_heure.minute:02d} : "
                f"la nuit (entre {HEURE_DEBUT_NUIT} h et {HEURE_FIN_NUIT} h), tu prends le temps "
                f"de réfléchir avant tout achat de plus de {format_euros(SEUIL_NOCTURNE)}."
            ),
        ))

    if achat.categorie in CATEGORIES_TOUJOURS_EN_PAUSE:
        regles.append(RegleDeclenchee(
            code="categorie_impulsive",
            message=f"Tu prends quelques minutes avant chaque commande « {nom_categorie} ».",
        ))
        recentes = [
            t for t in transactions
            if est_achat_surveille(t)
            and t.categorie == achat.categorie
            and achat.date_heure - FENETRE_REPETITION <= t.date_heure <= achat.date_heure
        ]
        rang = len(recentes) + 1  # cet achat serait la commande n° rang sur 7 jours
        if rang >= SEUIL_REPETITION:
            regles.append(RegleDeclenchee(
                code="repetition",
                message=f"Ce serait ta {rang}e commande « {nom_categorie} » en 7 jours.",
            ))

    # 3. Blocage strict : un dépassement de limite est refusé.
    if profil.blocage_strict and any(r.code in REGLES_DE_LIMITE for r in regles):
        return Decision(statut=Statut.REFUSE, regles=regles)

    # 4. Au moins une règle : pause avec le délai de la catégorie.
    if regles:
        delai = profil.delais_minutes.get(achat.categorie, DELAI_PAR_DEFAUT_MINUTES)
        return Decision(statut=Statut.PAUSE, regles=regles, delai_minutes=delai)

    # 5. Sinon, l'achat passe.
    return Decision(statut=Statut.ACCEPTE)
