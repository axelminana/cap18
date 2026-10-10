"""Tests de l'API : la démo jouée à travers des requêtes HTTP, comme le fera le front."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, etat

client = TestClient(app)
BASKETS = {"commercant": "Sneak'Air", "montant": 89}


@pytest.fixture(autouse=True)
def demo_neuve():
    """Avant chaque test : données d'origine, 10 octobre 2026 à 1 h."""
    etat.reinitialiser()


# --- Lecture ---

def test_etat_initial():
    reponse = client.get("/api/etat")
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["maintenant"] == "2026-10-10T01:00:00"
    assert donnees["profil"]["prenom"] == "Léa"
    assert donnees["plan"]["produit"] == "Livret A"
    assert donnees["progression"] == 8
    assert donnees["suspendus"] == []


def test_liste_des_commercants():
    noms = [c["nom"] for c in client.get("/api/commercants").json()]
    assert "Sneak'Air" in noms


# --- Variante B : pause, repaiement trop tôt, puis après le délai ---

def test_variante_b_par_l_api():
    reponse = client.post("/api/paiement", json=BASKETS).json()
    assert reponse["statut"] == "pause"
    assert reponse["secondes_restantes"] == 1800
    assert {r["code"] for r in reponse["regles"]} == {"confirmation", "limite_categorie"}

    suspendus = client.get("/api/etat").json()["suspendus"]
    assert len(suspendus) == 1 and suspendus[0]["secondes_restantes"] == 1800

    client.post("/api/horloge/avancer", json={"minutes": 10})
    assert client.post("/api/paiement", json=BASKETS).json()["secondes_restantes"] == 1200

    client.post("/api/horloge/avancer", json={"minutes": 20})
    assert client.post("/api/paiement", json=BASKETS).json()["statut"] == "accepte"
    assert client.get("/api/etat").json()["suspendus"] == []


# --- Variante A : renoncer puis épargner ---

def test_variante_a_par_l_api():
    client.post("/api/paiement", json=BASKETS)
    proposition = client.post("/api/renoncer", json=BASKETS).json()
    assert proposition["somme_conseillee"] == "44"
    assert proposition["message"].startswith("Bravo")
    # Le curseur : 50 % par défaut, et une somme pour chaque position (clés en texte en JSON).
    assert proposition["pourcentage_conseille"] == 50
    assert proposition["sommes_par_pourcentage"]["75"] == "66"

    reponse = client.post("/api/epargner", json={"montant": 44}).json()
    assert reponse["objectif"]["deja_epargne"] == "194"
    assert reponse["progression"] == 10


# --- Bilan de fin de mois ---

def test_bilan_apres_passage_au_mois_suivant():
    client.post("/api/horloge/mois-suivant")
    bilan = client.get("/api/bilan").json()
    assert [(b["annee"], b["mois"]) for b in bilan["historique"]] == [(2026, 8), (2026, 9), (2026, 10)]
    assert bilan["historique"][-1]["economies"] == "94.21"  # 120 - 25,79


def test_bilan_a_epargner_a_chaque_fin_de_mois_par_l_api():
    assert client.get("/api/bilan").json()["a_epargner"] is None

    client.post("/api/horloge/mois-suivant")
    a_epargner = client.get("/api/bilan").json()["a_epargner"]
    assert (a_epargner["mois"], a_epargner["economies"]) == (10, "94.21")
    reponse = client.post("/api/bilan/epargner", json={"annee": 2026, "mois": 10, "montant": 94.21})
    assert reponse.json()["objectif"]["deja_epargne"] == "244.21"
    assert client.get("/api/bilan").json()["a_epargner"] is None
    # Une 2e fois : refusé
    assert client.post("/api/bilan/epargner", json={"annee": 2026, "mois": 10, "montant": 1}).status_code == 400

    client.post("/api/horloge/mois-suivant")
    assert client.get("/api/bilan").json()["a_epargner"]["mois"] == 11


# --- Objectif atteint : nouveau projet ---

def test_nouveau_projet_par_l_api():
    projet = {"nom": "Première voiture", "montant": 3000, "echeance": "2029-10-10"}
    assert client.post("/api/objectif/nouveau", json=projet).status_code == 400  # pas encore atteint

    client.post("/api/epargner", json={"montant": 1700})  # 1 850 € sur 1 800 €
    donnees = client.get("/api/etat").json()
    assert donnees["objectif_atteint"] and float(donnees["surplus"]) == 50

    objectif = client.post("/api/objectif/nouveau", json=projet).json()
    assert (objectif["nom"], objectif["deja_epargne"]) == ("Première voiture", "50")
    assert client.get("/api/etat").json()["objectif_atteint"] is False


# --- Mon contrat : blocage strict ---

def test_activer_le_blocage_strict_puis_payer():
    profil = client.get("/api/etat").json()["profil"]
    profil["blocage_strict"] = True
    assert client.put("/api/profil", json=profil).status_code == 200
    assert client.post("/api/paiement", json=BASKETS).json()["statut"] == "refuse"


def test_achat_en_magasin_accepte():
    reponse = client.post("/api/paiement", json={**BASKETS, "canal": "magasin"}).json()
    assert reponse["statut"] == "accepte"


# --- Erreurs : réponses propres, jamais de crash ---

def test_commercant_inconnu():
    reponse = client.post("/api/paiement", json={"commercant": "Inconnu", "montant": 10})
    assert reponse.status_code == 404
    assert "Commerçant inconnu" in reponse.json()["detail"]


def test_montant_negatif_refuse():
    assert client.post("/api/paiement", json={"commercant": "Sneak'Air", "montant": -5}).status_code == 422


def test_renoncer_sans_achat_suspendu():
    assert client.post("/api/renoncer", json=BASKETS).status_code == 404


def test_profil_invalide_refuse():
    profil = client.get("/api/etat").json()["profil"]
    profil["limites"]["vetements"] = 500  # au-delà du budget en ligne
    assert client.put("/api/profil", json=profil).status_code == 422


def test_avancer_le_temps_en_arriere_refuse():
    assert client.post("/api/horloge/avancer", json={"minutes": -10}).status_code == 400


def test_reinitialiser_remet_la_demo_a_zero():
    client.post("/api/paiement", json=BASKETS)
    client.post("/api/horloge/avancer", json={"minutes": 60})
    donnees = client.post("/api/reinitialiser").json()
    assert donnees["suspendus"] == []
    assert donnees["maintenant"] == "2026-10-10T01:00:00"


# --- Front : les pages sont servies ---

@pytest.mark.parametrize("page", ["/", "/boutique.html", "/banque.html", "/style.css", "/commun.js"])
def test_pages_du_front_servies(page):
    assert client.get(page).status_code == 200


def test_l_appli_recoit_les_raisons_de_la_pause_et_les_libelles():
    client.post("/api/paiement", json=BASKETS)
    donnees = client.get("/api/etat").json()
    assert {r["code"] for r in donnees["suspendus"][0]["regles"]} == {"confirmation", "limite_categorie"}
    assert donnees["libelles_categories"]["vetements"] == "vêtements"
    assert donnees["delais_conseilles"]["vetements"] == 30


# --- Tableau de score (US4) ---

def test_score_apres_renoncement_et_epargne():
    client.post("/api/paiement", json=BASKETS)
    client.post("/api/renoncer", json=BASKETS)
    client.post("/api/epargner", json={"montant": 44})
    donnees = client.get("/api/score").json()
    assert donnees["score"]["achats_evites"] == 1
    assert donnees["score"]["total_epargne"] == "44"
    assert "premier_achat_evite" in {b["code"] for b in donnees["badges"] if b["obtenu"]}
