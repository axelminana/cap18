"""Moteur de la pause de réflexion (US2).

Tout achat en ligne non nécessaire est mis en pause, quelle que soit l'heure :
il faut le confirmer après le délai de sa catégorie. Le message liste aussi les
raisons supplémentaires (limite dépassée, budget dépassé, commandes répétées).

evaluer_achat() est une fonction pure : elle reçoit l'achat tenté, le profil et
les transactions déjà acceptées, et renvoie une Decision. Elle ne modifie rien.
"""

from datetime import timedelta
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from app.models import CATEGORIES_OBLIGATOIRES, Canal, Categorie, Profil, Transaction

# Répétition : message renforcé à partir de la 2e commande sur 7 jours glissants.
CATEGORIES_REPETITION = {Categorie.LIVRAISON_REPAS}
SEUIL_REPETITION = 2
FENETRE_REPETITION = timedelta(days=7)

# Délai utilisé si la catégorie n'a pas de délai dans le profil.
DELAI_PAR_DEFAUT_MINUTES = 15

# Règles qui concernent un dépassement (seules visées par le blocage strict).
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
    """Un achat est concerné s'il est en ligne et non nécessaire."""
    return transaction.canal == Canal.EN_LIGNE and transaction.categorie not in CATEGORIES_OBLIGATOIRES


def achats_en_ligne_du_mois(transactions: list[Transaction], annee: int, mois: int) -> list[Transaction]:
    """Achats en ligne non nécessaires d'un mois donné (ceux qui comptent dans le budget)."""
    return [
        t for t in transactions
        if est_achat_surveille(t) and t.date_heure.year == annee and t.date_heure.month == mois
    ]


def evaluer_achat(achat: Transaction, profil: Profil, transactions: list[Transaction]) -> Decision:
    # 1. Hors périmètre : achat en magasin ou dépense nécessaire.
    if not est_achat_surveille(achat):
        return Decision(statut=Statut.ACCEPTE)

    nom_categorie = achat.categorie.value.replace("_", " ")
    delai = profil.delais_minutes.get(achat.categorie, DELAI_PAR_DEFAUT_MINUTES)

    # 2. Règle de base : tout achat en ligne non nécessaire demande une confirmation.
    regles = [RegleDeclenchee(
        code="confirmation",
        message=(
            f"Achat en ligne « {nom_categorie} » de {format_euros(achat.montant)} : "
            f"tu as choisi de prendre {delai} min de réflexion avant de le valider."
        ),
    )]

    # 3. Raisons supplémentaires, à partir des dépenses en ligne du mois.
    du_mois = achats_en_ligne_du_mois(transactions, achat.date_heure.year, achat.date_heure.month)
    total_mois = sum((t.montant for t in du_mois), Decimal("0"))
    total_categorie = sum((t.montant for t in du_mois if t.categorie == achat.categorie), Decimal("0"))

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

    if achat.categorie in CATEGORIES_REPETITION:
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

    # 4. Blocage strict : un dépassement de limite ou de budget est refusé.
    if profil.blocage_strict and any(r.code in REGLES_DE_LIMITE for r in regles):
        return Decision(statut=Statut.REFUSE, regles=regles)

    # 5. Sinon : pause avec le délai de la catégorie.
    return Decision(statut=Statut.PAUSE, regles=regles, delai_minutes=delai)
