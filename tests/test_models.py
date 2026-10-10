"""Tests des modèles Pydantic et du chargement des données."""

import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import LIBELLES_CATEGORIES, Categorie, Profil, Transaction, charger_donnees


def profil_valide() -> dict:
    """Un profil minimal correct, que chaque test modifie pour créer une erreur."""
    return {
        "prenom": "Léa",
        "age": 18,
        "revenus_mensuels": 850,
        "depenses_obligatoires": [{"libelle": "Loyer", "montant": 420}],
        "budget_en_ligne": 120,
        "limites": {"vetements": 60},
        "delais_minutes": {"vetements": 30},
        "objectif": {"nom": "Permis", "montant": 1800, "echeance": "2027-10-10"},
    }


# --- Les vrais fichiers de data/ ---

def test_les_fichiers_de_donnees_se_chargent():
    donnees = charger_donnees()
    assert donnees.profil.prenom == "Léa"
    assert donnees.profil.age == 18
    assert donnees.profil.limites[Categorie.VETEMENTS] == Decimal("60")
    assert len(donnees.transactions) > 0


def test_chaque_transaction_vient_d_un_commercant_connu_avec_la_bonne_categorie():
    donnees = charger_donnees()
    categorie_par_nom = {c.nom: c.categorie for c in donnees.commercants}
    for transaction in donnees.transactions:
        assert categorie_par_nom[transaction.commercant] == transaction.categorie


# --- Valeurs par défaut ---

def test_blocage_strict_desactive_par_defaut():
    assert Profil(**profil_valide()).blocage_strict is False


def test_deja_epargne_vaut_zero_par_defaut():
    assert Profil(**profil_valide()).objectif.deja_epargne == 0


# --- Données invalides : erreurs claires ---

def test_montant_negatif_refuse():
    with pytest.raises(ValidationError):
        Transaction(
            commercant="Sneak'Air", categorie="vetements", montant=-89,
            canal="en_ligne", date_heure="2026-10-10T01:00:00",
        )


def test_categorie_inconnue_refusee():
    with pytest.raises(ValidationError):
        Transaction(
            commercant="Inconnu", categorie="voyage", montant=50,
            canal="en_ligne", date_heure="2026-10-10T01:00:00",
        )


def test_canal_inconnu_refuse():
    with pytest.raises(ValidationError):
        Transaction(
            commercant="Sneak'Air", categorie="vetements", montant=89,
            canal="telephone", date_heure="2026-10-10T01:00:00",
        )


def test_age_hors_cible_refuse():
    profil = profil_valide()
    profil["age"] = 17
    with pytest.raises(ValidationError):
        Profil(**profil)


def test_limite_superieure_au_budget_refusee():
    profil = profil_valide()
    profil["limites"] = {"vetements": 200}
    with pytest.raises(ValidationError, match="ne pas dépasser le budget"):
        Profil(**profil)


def test_categorie_obligatoire_sans_limite_ni_delai():
    profil = profil_valide()
    profil["delais_minutes"] = {"loyer": 30}
    with pytest.raises(ValidationError, match="obligatoire"):
        Profil(**profil)


def test_delai_de_24h_ou_plus_refuse():
    profil = profil_valide()
    profil["delais_minutes"] = {"vetements": 24 * 60}
    with pytest.raises(ValidationError, match="24 h"):
        Profil(**profil)


def test_fichier_invalide_indique_le_nom_du_fichier(tmp_path):
    profil = profil_valide()
    profil["budget_en_ligne"] = -10
    (tmp_path / "profil.json").write_text(json.dumps(profil), encoding="utf-8")
    (tmp_path / "commercants.json").write_text("[]", encoding="utf-8")
    (tmp_path / "transactions.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="profil.json"):
        charger_donnees(tmp_path)


def test_chaque_categorie_a_un_libelle():
    assert set(LIBELLES_CATEGORIES) == set(Categorie)
