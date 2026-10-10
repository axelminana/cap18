"""Orchestration du parcours de Léa : payer, renoncer, épargner.

Enchaîne les modules métier :
  suspension.py (achat déjà mémorisé ?) -> regles.py (pause ?) -> enregistrement.

Fonctions pures : elles reçoivent un Compte et renvoient un nouveau Compte avec le
résultat. Le Compte d'origine n'est jamais modifié. Seule l'API garde le Compte en mémoire.
"""

import math
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from app.epargne import (
    BilanMensuel,
    PropositionEpargne,
    budget_restant,
    epargner,
    historique,
    modifier_objectif,
    nouvel_objectif,
    proposition_apres_renoncement,
)
from app.models import Categorie, Donnees, Profil, Transaction
from app.regles import RegleDeclenchee, Statut, evaluer_achat
from app.suspension import AchatSuspendu, EtatTentative, memoriser, retirer, verifier_tentative


class AchatEvite(BaseModel):
    """Un achat auquel Léa a renoncé (pour le tableau de score)."""

    commercant: str
    categorie: Categorie
    montant: Decimal
    date: datetime


class Versement(BaseModel):
    """Un versement vers l'objectif fait depuis l'appli (pour le tableau de score)."""

    montant: Decimal
    date: datetime


class Compte(BaseModel):
    """Tout l'état de Léa à un instant donné."""

    profil: Profil
    transactions: list[Transaction]
    suspendus: list[AchatSuspendu] = []
    achats_evites: list[AchatEvite] = []
    versements: list[Versement] = []
    bilans_traites: list[tuple[int, int]] = []  # (année, mois) déjà épargnés ou ignorés
    objectifs_atteints: list[str] = []          # noms des objectifs déjà atteints (pour le score)


def compte_initial(donnees: Donnees) -> Compte:
    return Compte(profil=donnees.profil, transactions=donnees.transactions)


class StatutPaiement(str, Enum):
    ACCEPTE = "accepte"
    PAUSE = "pause"
    REFUSE = "refuse"


class ResultatPaiement(BaseModel):
    statut: StatutPaiement
    message: str
    regles: list[RegleDeclenchee] = []
    secondes_restantes: int = 0
    heure_deblocage: datetime | None = None


def ajouter_transaction(compte: Compte, achat: Transaction) -> Compte:
    return compte.model_copy(update={"transactions": compte.transactions + [achat]})


def payer(compte: Compte, achat: Transaction) -> tuple[Compte, ResultatPaiement]:
    # 1. Cet achat a-t-il déjà été mémorisé ?
    tentative = verifier_tentative(achat, compte.suspendus)

    if tentative.etat == EtatTentative.TOUJOURS_SUSPENDU:
        minutes = math.ceil(tentative.secondes_restantes / 60)
        return compte, ResultatPaiement(
            statut=StatutPaiement.PAUSE,
            message=f"Encore {minutes} min de réflexion avant de pouvoir valider cet achat.",
            secondes_restantes=tentative.secondes_restantes,
            heure_deblocage=tentative.achat_memorise.heure_deblocage,
        )

    if tentative.etat == EtatTentative.DEBLOQUE:
        nouveau = ajouter_transaction(compte, achat)
        nouveau = nouveau.model_copy(update={"suspendus": retirer(tentative.achat_memorise, compte.suspendus)})
        return nouveau, ResultatPaiement(
            statut=StatutPaiement.ACCEPTE,
            message="Délai de réflexion terminé : ton achat est validé. C'est toi qui décides.",
        )

    # 2. Nouvel achat : on applique les règles.
    decision = evaluer_achat(achat, compte.profil, compte.transactions)

    if decision.statut == Statut.ACCEPTE:
        return ajouter_transaction(compte, achat), ResultatPaiement(
            statut=StatutPaiement.ACCEPTE, message="Paiement accepté.",
        )

    if decision.statut == Statut.REFUSE:
        return compte, ResultatPaiement(
            statut=StatutPaiement.REFUSE,
            message="Paiement refusé : tu as activé le blocage strict et cet achat dépasse ta limite.",
            regles=decision.regles,
        )

    # 3. Pause : la banque refuse ce premier essai et mémorise l'achat.
    suspendus = memoriser(achat, decision.delai_minutes, compte.suspendus, decision.regles)
    memorise = suspendus[-1]
    return compte.model_copy(update={"suspendus": suspendus}), ResultatPaiement(
        statut=StatutPaiement.PAUSE,
        message=(
            f"Pause de réflexion de {decision.delai_minutes} min. Après ce délai, "
            "relance le paiement si tu le veux toujours, ou renonce et épargne."
        ),
        regles=decision.regles,
        secondes_restantes=decision.delai_minutes * 60,
        heure_deblocage=memorise.heure_deblocage,
    )


def renoncer(
    compte: Compte, commercant: str, montant: Decimal, maintenant: datetime
) -> tuple[Compte, PropositionEpargne]:
    """Léa renonce à un achat suspendu : on le retire, on la félicite et on propose d'épargner."""
    trouve = [s for s in compte.suspendus if s.commercant == commercant and s.montant == montant]
    if not trouve:
        raise ValueError("Aucun achat suspendu ne correspond à ce commerçant et ce montant.")
    evite = AchatEvite(
        commercant=commercant, categorie=trouve[0].categorie, montant=montant, date=maintenant
    )
    nouveau = compte.model_copy(update={
        "suspendus": retirer(trouve[0], compte.suspendus),
        "achats_evites": compte.achats_evites + [evite],
    })
    restant = budget_restant(compte.profil, compte.transactions, maintenant.date())
    proposition = proposition_apres_renoncement(montant, restant, compte.profil.objectif)
    return nouveau, proposition


def verser_epargne(compte: Compte, montant: Decimal, maintenant: datetime) -> Compte:
    """Verse un montant vers l'objectif (après un renoncement ou au bilan du mois)."""
    objectif = epargner(compte.profil.objectif, montant)
    profil = compte.profil.model_copy(update={"objectif": objectif})
    versements = compte.versements
    if montant > 0:  # « ne rien épargner » n'est pas un versement
        versements = versements + [Versement(montant=montant, date=maintenant)]
    return compte.model_copy(update={"profil": profil, "versements": versements})


def bilan_a_epargner(compte: Compte, aujourd_hui: date) -> BilanMensuel | None:
    """Le bilan du dernier mois terminé, s'il a des économies et n'a pas encore été traité."""
    bilans = historique(compte.profil, compte.transactions, aujourd_hui)
    if not bilans:
        return None
    dernier = bilans[-1]
    if dernier.economies <= 0 or (dernier.annee, dernier.mois) in compte.bilans_traites:
        return None
    return dernier


def epargner_bilan(
    compte: Compte, annee: int, mois: int, montant: Decimal, maintenant: datetime
) -> Compte:
    """Léa choisit d'épargner tout, une partie ou rien (0) des économies du mois terminé."""
    bilan = bilan_a_epargner(compte, maintenant.date())
    if bilan is None or (bilan.annee, bilan.mois) != (annee, mois):
        raise ValueError("Ce bilan n'est pas à épargner (mois en cours, déjà traité ou sans économies).")
    if montant > bilan.economies:
        raise ValueError(f"Tu ne peux pas épargner plus que tes économies du mois ({bilan.economies} €).")
    nouveau = verser_epargne(compte, montant, maintenant)
    return nouveau.model_copy(update={"bilans_traites": compte.bilans_traites + [(annee, mois)]})


def demarrer_nouvel_objectif(
    compte: Compte, nom: str, montant: Decimal, echeance: date, aujourd_hui: date
) -> Compte:
    """Remplace l'objectif atteint par un nouveau projet (le surplus éventuel est reporté)."""
    ancien = compte.profil.objectif
    nouveau = nouvel_objectif(ancien, nom, montant, echeance, aujourd_hui)
    profil = compte.profil.model_copy(update={"objectif": nouveau})
    return compte.model_copy(update={
        "profil": profil,
        "objectifs_atteints": compte.objectifs_atteints + [ancien.nom],
    })


def ajuster_objectif(compte: Compte, nom: str, montant: Decimal, echeance: date, aujourd_hui: date) -> Compte:
    """Échéance dépassée (ou simple changement d'avis) : nouvelle date, nouveau montant ou nouveau nom."""
    objectif = modifier_objectif(compte.profil.objectif, nom, montant, echeance, aujourd_hui)
    return compte.model_copy(update={"profil": compte.profil.model_copy(update={"objectif": objectif})})
