"""Mémorisation des achats suspendus (US2).

Les sites marchands abandonnent un paiement non validé rapidement. La banque refuse
donc le premier essai et mémorise l'achat. Si l'utilisateur repaie le même montant
chez le même commerçant après le délai (et avant 24 h), l'achat passe sans nouvelle pause.

Fonctions pures : la liste des achats suspendus est reçue en paramètre, et une
nouvelle liste est renvoyée. La liste d'origine n'est jamais modifiée.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from app.models import Categorie, Transaction
from app.regles import RegleDeclenchee

DUREE_VALIDITE = timedelta(hours=24)


class AchatSuspendu(BaseModel):
    commercant: str
    categorie: Categorie
    montant: Decimal
    date_essai: datetime
    heure_deblocage: datetime
    regles: list[RegleDeclenchee] = []  # raisons de la pause, affichées dans l'appli


class EtatTentative(str, Enum):
    NOUVEL_ACHAT = "nouvel_achat"            # rien de mémorisé : on évalue les règles
    TOUJOURS_SUSPENDU = "toujours_suspendu"  # délai pas encore écoulé
    DEBLOQUE = "debloque"                    # délai écoulé : l'achat peut passer


class ResultatTentative(BaseModel):
    etat: EtatTentative
    achat_memorise: AchatSuspendu | None = None
    secondes_restantes: int = 0


def est_expire(suspendu: AchatSuspendu, maintenant: datetime) -> bool:
    return maintenant >= suspendu.date_essai + DUREE_VALIDITE


def correspond(suspendu: AchatSuspendu, achat: Transaction) -> bool:
    """Même commerçant et montant exact."""
    return suspendu.commercant == achat.commercant and suspendu.montant == achat.montant


def verifier_tentative(achat: Transaction, suspendus: list[AchatSuspendu]) -> ResultatTentative:
    """Regarde si cette tentative de paiement correspond à un achat mémorisé encore valide."""
    maintenant = achat.date_heure
    for suspendu in suspendus:
        if correspond(suspendu, achat) and not est_expire(suspendu, maintenant):
            if maintenant < suspendu.heure_deblocage:
                restant = suspendu.heure_deblocage - maintenant
                return ResultatTentative(
                    etat=EtatTentative.TOUJOURS_SUSPENDU,
                    achat_memorise=suspendu,
                    secondes_restantes=int(restant.total_seconds()),
                )
            return ResultatTentative(etat=EtatTentative.DEBLOQUE, achat_memorise=suspendu)
    # Montant différent, autre commerçant, ou achat mémorisé expiré : nouvel achat.
    return ResultatTentative(etat=EtatTentative.NOUVEL_ACHAT)


def memoriser(
    achat: Transaction,
    delai_minutes: int,
    suspendus: list[AchatSuspendu],
    regles: list[RegleDeclenchee] | None = None,
) -> list[AchatSuspendu]:
    """Ajoute l'achat à la liste, et en profite pour retirer les achats expirés."""
    nouveau = AchatSuspendu(
        commercant=achat.commercant,
        categorie=achat.categorie,
        montant=achat.montant,
        date_essai=achat.date_heure,
        heure_deblocage=achat.date_heure + timedelta(minutes=delai_minutes),
        regles=regles or [],
    )
    conserves = [
        s for s in suspendus
        if not correspond(s, achat) and not est_expire(s, achat.date_heure)
    ]
    return conserves + [nouveau]


def retirer(achat_memorise: AchatSuspendu, suspendus: list[AchatSuspendu]) -> list[AchatSuspendu]:
    """Retire un achat de la liste (une fois payé, ou si l'utilisateur renonce)."""
    return [s for s in suspendus if s != achat_memorise]
