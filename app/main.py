"""API de Cap 18 : expose la logique métier en JSON et sert les pages du dossier static/.

Aucune règle métier ici : chaque route lit l'état, appelle une fonction des modules
métier, enregistre le nouvel état et renvoie le résultat.

Lancement : uvicorn app.main:app --reload   puis   http://127.0.0.1:8000
Documentation interactive des routes : http://127.0.0.1:8000/docs
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.epargne import (
    bilan_mensuel,
    budget_restant,
    historique,
    objectif_atteint,
    plan_conseille,
    progression,
    surplus,
)
from app.horloge import Horloge
from app.models import DELAIS_CONSEILLES, LIBELLES_CATEGORIES, Canal, Profil, Transaction, charger_donnees
from app.paiement import (
    bilan_a_epargner,
    compte_initial,
    demarrer_nouvel_objectif,
    epargner_bilan,
    payer,
    renoncer,
    verser_epargne,
)
from app.score import calculer_score
from app.suspension import est_expire

# La démo commence le samedi 10 octobre 2026 à 1 h du matin.
DEBUT_DEMO = datetime(2026, 10, 10, 1, 0)
DOSSIER_STATIC = Path(__file__).parent.parent / "static"


class EtatDemo:
    """Le seul état de l'application, gardé en mémoire tant que le serveur tourne."""

    def __init__(self):
        self.reinitialiser()

    def reinitialiser(self):
        donnees = charger_donnees()
        self.compte = compte_initial(donnees)
        self.commercants = donnees.commercants
        self.horloge = Horloge(DEBUT_DEMO)


etat = EtatDemo()
app = FastAPI(title="Cap 18", description="Pause de réflexion sur les achats en ligne, au service de l'épargne.")


# --- Corps des requêtes ---

class DemandePaiement(BaseModel):
    commercant: str
    montant: Decimal = Field(gt=0)
    canal: Canal = Canal.EN_LIGNE


class DemandeRenoncement(BaseModel):
    commercant: str
    montant: Decimal = Field(gt=0)


class DemandeEpargne(BaseModel):
    montant: Decimal = Field(ge=0)


class DemandeEpargneBilan(BaseModel):
    annee: int
    mois: int
    montant: Decimal = Field(ge=0)   # 0 = « ne rien épargner ce mois-ci »


class DemandeNouvelObjectif(BaseModel):
    nom: str = Field(min_length=1)
    montant: Decimal = Field(gt=0)
    echeance: date


class DemandeAvance(BaseModel):
    minutes: int


# --- Lecture de l'état ---

@app.get("/api/etat")
def lire_etat():
    """Tout ce que l'écran de la banque affiche : profil, objectif, budget, achats en pause."""
    maintenant = etat.horloge.maintenant()
    compte = etat.compte
    suspendus = [
        {
            **s.model_dump(),
            "secondes_restantes": max(0, int((s.heure_deblocage - maintenant).total_seconds())),
        }
        for s in compte.suspendus if not est_expire(s, maintenant)
    ]
    return {
        "maintenant": maintenant,
        "profil": compte.profil,
        "plan": plan_conseille(compte.profil.objectif, maintenant.date()),
        "progression": progression(compte.profil.objectif),
        "objectif_atteint": objectif_atteint(compte.profil.objectif),
        "surplus": surplus(compte.profil.objectif),
        "budget_restant": budget_restant(compte.profil, compte.transactions, maintenant.date()),
        "suspendus": suspendus,
        "libelles_categories": LIBELLES_CATEGORIES,
        "delais_conseilles": DELAIS_CONSEILLES,
    }


@app.get("/api/commercants")
def lire_commercants():
    return etat.commercants


@app.get("/api/bilan")
def lire_bilan():
    aujourd_hui = etat.horloge.maintenant().date()
    compte = etat.compte
    return {
        "historique": historique(compte.profil, compte.transactions, aujourd_hui),
        "mois_en_cours": bilan_mensuel(compte.profil, compte.transactions, aujourd_hui.year, aujourd_hui.month),
        "a_epargner": bilan_a_epargner(compte, aujourd_hui),
    }


@app.get("/api/score")
def lire_score():
    """Tableau de score personnel (US4)."""
    score, badges = calculer_score(etat.compte, etat.horloge.maintenant().date())
    return {"score": score, "badges": badges}


# --- Mon contrat (US1) ---

@app.put("/api/profil")
def modifier_profil(profil: Profil):
    """Remplace le contrat de Léa. Pydantic valide tout (limites, délais…) avant d'arriver ici."""
    etat.compte = etat.compte.model_copy(update={"profil": profil})
    return profil


@app.post("/api/objectif/nouveau")
def nouveau_projet(demande: DemandeNouvelObjectif):
    """Objectif atteint : démarrer le projet suivant (le surplus déjà épargné est reporté)."""
    try:
        etat.compte = demarrer_nouvel_objectif(etat.compte, demande.nom, demande.montant, demande.echeance)
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))
    return etat.compte.profil.objectif


# --- Paiement, renoncement, épargne (US2, US3) ---

@app.post("/api/paiement")
def demander_paiement(demande: DemandePaiement):
    # Détection automatique de la catégorie à partir du commerçant (comme un code MCC).
    commercant = next((c for c in etat.commercants if c.nom == demande.commercant), None)
    if commercant is None:
        raise HTTPException(status_code=404, detail=f"Commerçant inconnu : {demande.commercant}")
    achat = Transaction(
        commercant=commercant.nom,
        categorie=commercant.categorie,
        montant=demande.montant,
        canal=demande.canal,
        date_heure=etat.horloge.maintenant(),
    )
    etat.compte, resultat = payer(etat.compte, achat)
    return resultat


@app.post("/api/renoncer")
def renoncer_achat(demande: DemandeRenoncement):
    try:
        etat.compte, proposition = renoncer(
            etat.compte, demande.commercant, demande.montant, etat.horloge.maintenant()
        )
    except ValueError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur))
    return proposition


@app.post("/api/epargner")
def epargner_montant(demande: DemandeEpargne):
    etat.compte = verser_epargne(etat.compte, demande.montant, etat.horloge.maintenant())
    objectif = etat.compte.profil.objectif
    return {"objectif": objectif, "progression": progression(objectif)}


@app.post("/api/bilan/epargner")
def epargner_le_bilan(demande: DemandeEpargneBilan):
    """Fin de mois : épargner tout, une partie ou rien (montant 0) des économies."""
    try:
        etat.compte = epargner_bilan(
            etat.compte, demande.annee, demande.mois, demande.montant, etat.horloge.maintenant()
        )
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))
    objectif = etat.compte.profil.objectif
    return {"objectif": objectif, "progression": progression(objectif)}


# --- Horloge de démo ---

@app.get("/api/horloge")
def lire_horloge():
    return {"maintenant": etat.horloge.maintenant(), "simulee": etat.horloge.est_simulee()}


@app.post("/api/horloge/avancer")
def avancer_horloge(demande: DemandeAvance):
    try:
        etat.horloge.avancer(demande.minutes)
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))
    return lire_horloge()


@app.post("/api/horloge/mois-suivant")
def mois_suivant():
    etat.horloge.aller_au_mois_suivant()
    return lire_horloge()


@app.post("/api/reinitialiser")
def reinitialiser():
    """Remet la démo à zéro : données d'origine, 10 octobre 2026 à 1 h."""
    etat.reinitialiser()
    return lire_etat()


# --- Pages du front (étape 8). Monté en dernier pour ne pas masquer les routes /api. ---
app.mount("/", StaticFiles(directory=DOSSIER_STATIC, html=True), name="static")
