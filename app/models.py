"""Modèles de données de Cap 18 et chargement des fichiers JSON.

Chaque fichier de data/ est validé par Pydantic au chargement :
une donnée invalide provoque une erreur claire qui indique le fichier en cause.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, model_validator

DOSSIER_DATA = Path(__file__).parent.parent / "data"


class Categorie(str, Enum):
    """Catégories de dépenses (inspirées des codes MCC des commerçants)."""

    LOYER = "loyer"
    FACTURES = "factures"
    COURSES = "courses"
    LIVRAISON_REPAS = "livraison_repas"
    VETEMENTS = "vetements"
    ELECTRONIQUE = "electronique"
    JEUX_VIDEO = "jeux_video"
    ABONNEMENTS = "abonnements"
    AUTRES = "autres"


# Noms affichés à l'utilisateur.
LIBELLES_CATEGORIES = {
    Categorie.LOYER: "loyer",
    Categorie.FACTURES: "factures",
    Categorie.COURSES: "courses",
    Categorie.LIVRAISON_REPAS: "livraison de repas",
    Categorie.VETEMENTS: "vêtements",
    Categorie.ELECTRONIQUE: "électronique",
    Categorie.JEUX_VIDEO: "jeux vidéo",
    Categorie.ABONNEMENTS: "abonnements",
    Categorie.AUTRES: "autres",
}

# Délais de réflexion conseillés (en minutes), affichés à côté des choix de l'utilisateur.
DELAIS_CONSEILLES = {
    Categorie.LIVRAISON_REPAS: 5,
    Categorie.VETEMENTS: 30,
    Categorie.ELECTRONIQUE: 60,
    Categorie.JEUX_VIDEO: 30,
    Categorie.ABONNEMENTS: 10,
    Categorie.AUTRES: 15,
}

# Dépenses nécessaires : jamais de pause, jamais de limite, hors budget en ligne.
CATEGORIES_OBLIGATOIRES = {Categorie.LOYER, Categorie.FACTURES, Categorie.COURSES}

# Un délai de réflexion doit rester inférieur à 24 h (durée de vie d'un achat mémorisé).
DELAI_MAXIMUM_MINUTES = 24 * 60


class Canal(str, Enum):
    """Où le paiement a lieu. Seul le canal en ligne est concerné par Cap 18."""

    EN_LIGNE = "en_ligne"
    MAGASIN = "magasin"


class Commercant(BaseModel):
    nom: str
    categorie: Categorie


class Transaction(BaseModel):
    commercant: str
    categorie: Categorie
    montant: Decimal = Field(gt=0)
    canal: Canal
    date_heure: datetime


class DepenseObligatoire(BaseModel):
    libelle: str
    montant: Decimal = Field(gt=0)


class Objectif(BaseModel):
    nom: str
    montant: Decimal = Field(gt=0)
    echeance: date
    deja_epargne: Decimal = Field(default=Decimal("0"), ge=0)


class Profil(BaseModel):
    prenom: str
    age: int = Field(ge=18, le=25)
    revenus_mensuels: Decimal = Field(ge=0)
    depenses_obligatoires: list[DepenseObligatoire]
    budget_en_ligne: Decimal = Field(gt=0)
    limites: dict[Categorie, Decimal]
    delais_minutes: dict[Categorie, int]
    blocage_strict: bool = False
    questionnaire: bool = True   # questions de réflexion pendant la pause
    objectif: Objectif

    @model_validator(mode="after")
    def verifier_coherence(self):
        for categorie in CATEGORIES_OBLIGATOIRES:
            if categorie in self.limites or categorie in self.delais_minutes:
                raise ValueError(
                    f"La catégorie obligatoire « {categorie.value} » "
                    "ne peut pas avoir de limite ni de délai."
                )
        for categorie, limite in self.limites.items():
            if limite <= 0 or limite > self.budget_en_ligne:
                raise ValueError(
                    f"La limite de « {categorie.value} » ({limite} €) doit être "
                    f"positive et ne pas dépasser le budget en ligne ({self.budget_en_ligne} €)."
                )
        for categorie, delai in self.delais_minutes.items():
            # Un achat mémorisé expire après 24 h : le délai doit être plus court.
            if delai < 0 or delai >= DELAI_MAXIMUM_MINUTES:
                raise ValueError(
                    f"Le délai de « {categorie.value} » doit être compris "
                    "entre 0 et 24 h (exclu)."
                )
        return self


class Donnees(BaseModel):
    """Tout ce qui est chargé depuis le dossier data/."""

    profil: Profil
    commercants: list[Commercant]
    transactions: list[Transaction]


def lire_json(chemin: Path, modele):
    """Lit un fichier JSON et le valide avec le modèle donné."""
    try:
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
        return TypeAdapter(modele).validate_python(contenu)
    except (ValidationError, json.JSONDecodeError) as erreur:
        raise ValueError(f"Données invalides dans {chemin.name} :\n{erreur}") from erreur


def charger_donnees(dossier: Path = DOSSIER_DATA) -> Donnees:
    return Donnees(
        profil=lire_json(dossier / "profil.json", Profil),
        commercants=lire_json(dossier / "commercants.json", list[Commercant]),
        transactions=lire_json(dossier / "transactions.json", list[Transaction]),
    )
