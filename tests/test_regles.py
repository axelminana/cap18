"""Tests du moteur de déclenchement de la pause, sur des cas concrets.

Le profil est celui de Léa (data/profil.json) :
budget en ligne 120 €, limite vêtements 60 €, délai vêtements 30 min, délai repas 5 min.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models import Transaction, charger_donnees
from app.regles import Statut, evaluer_achat, format_euros

DONNEES = charger_donnees()
LEA = DONNEES.profil
# Historique réel : en octobre, avant le 10, Léa a dépensé 9,99 € (StreamBox)
# et 15,80 € (MiamExpress le 8 à 20 h 15) en ligne, soit 25,79 €.
HISTORIQUE = DONNEES.transactions

UNE_HEURE_DU_MATIN = datetime(2026, 10, 10, 1, 0)
QUATORZE_HEURES = datetime(2026, 10, 10, 14, 0)


def achat(commercant, categorie, montant, quand, canal="en_ligne") -> Transaction:
    return Transaction(
        commercant=commercant, categorie=categorie, montant=Decimal(str(montant)),
        canal=canal, date_heure=quand,
    )


def codes(decision) -> set[str]:
    return {regle.code for regle in decision.regles}


BASKETS_LA_NUIT = achat("Sneak'Air", "vetements", 89, UNE_HEURE_DU_MATIN)


# --- Les cas de référence de CLAUDE.md ---

def test_baskets_89_euros_a_1h_en_ligne_pause_de_30_minutes():
    decision = evaluer_achat(BASKETS_LA_NUIT, LEA, HISTORIQUE)
    assert decision.statut == Statut.PAUSE
    assert decision.delai_minutes == 30
    assert codes(decision) == {"limite_categorie", "nocturne"}


def test_message_en_langage_clair():
    decision = evaluer_achat(BASKETS_LA_NUIT, LEA, HISTORIQUE)
    message_limite = decision.regles[0].message
    assert "89 €" in message_limite and "60 €" in message_limite
    assert "1 h 00" in decision.regles[1].message


def test_meme_achat_en_magasin_pas_de_pause():
    en_magasin = achat("Sneak'Air", "vetements", 89, UNE_HEURE_DU_MATIN, canal="magasin")
    assert evaluer_achat(en_magasin, LEA, HISTORIQUE).statut == Statut.ACCEPTE


def test_loyer_jamais_de_pause_meme_la_nuit_et_en_blocage_strict():
    loyer = achat("Résidence Les Tilleuls", "loyer", 420, UNE_HEURE_DU_MATIN)
    lea_stricte = LEA.model_copy(update={"blocage_strict": True})
    assert evaluer_achat(loyer, LEA, HISTORIQUE).statut == Statut.ACCEPTE
    assert evaluer_achat(loyer, lea_stricte, HISTORIQUE).statut == Statut.ACCEPTE


def test_blocage_strict_et_limite_depassee_refus():
    lea_stricte = LEA.model_copy(update={"blocage_strict": True})
    decision = evaluer_achat(BASKETS_LA_NUIT, lea_stricte, HISTORIQUE)
    assert decision.statut == Statut.REFUSE
    assert "limite_categorie" in codes(decision)


def test_blocage_strict_sans_depassement_reste_une_simple_pause():
    lea_stricte = LEA.model_copy(update={"blocage_strict": True})
    petit_achat_nocturne = achat("Bazar en Ligne", "autres", 25, UNE_HEURE_DU_MATIN)
    decision = evaluer_achat(petit_achat_nocturne, lea_stricte, HISTORIQUE)
    assert decision.statut == Statut.PAUSE
    assert codes(decision) == {"nocturne"}


# --- Limites et budget ---

def test_achat_raisonnable_en_journee_accepte():
    tee_shirt = achat("Mode Urbaine", "vetements", 25, QUATORZE_HEURES)
    assert evaluer_achat(tee_shirt, LEA, HISTORIQUE).statut == Statut.ACCEPTE


def test_achat_pile_a_la_limite_accepte():
    # Les 89 € de baskets de septembre ne comptent pas pour octobre.
    tenue = achat("Mode Urbaine", "vetements", 60, QUATORZE_HEURES)
    assert evaluer_achat(tenue, LEA, HISTORIQUE).statut == Statut.ACCEPTE


def test_budget_total_depasse():
    octobre = [
        achat("Mode Urbaine", "vetements", 50, datetime(2026, 10, 2, 15, 0)),
        achat("TechnoPlus", "electronique", 45, datetime(2026, 10, 4, 15, 0)),
        achat("Bazar en Ligne", "autres", 20, datetime(2026, 10, 6, 15, 0)),
    ]  # 115 € dépensés en ligne
    jeu = achat("GameZone", "jeux_video", 10, QUATORZE_HEURES)  # sous la limite jeux (20 €)
    decision = evaluer_achat(jeu, LEA, octobre)
    assert decision.statut == Statut.PAUSE
    assert codes(decision) == {"budget_total"}
    assert decision.delai_minutes == 30


# --- Achat nocturne : 23 h – 4 h, au-delà de 20 € ---

@pytest.mark.parametrize("heure, minute, statut_attendu", [
    (22, 59, Statut.ACCEPTE),
    (23, 0, Statut.PAUSE),
    (3, 59, Statut.PAUSE),
    (4, 0, Statut.ACCEPTE),
])
def test_limites_de_la_nuit(heure, minute, statut_attendu):
    quand = datetime(2026, 10, 10, heure, minute)
    decision = evaluer_achat(achat("Bazar en Ligne", "autres", 25, quand), LEA, [])
    assert decision.statut == statut_attendu


def test_20_euros_pile_la_nuit_accepte():
    decision = evaluer_achat(achat("Bazar en Ligne", "autres", 20, UNE_HEURE_DU_MATIN), LEA, [])
    assert decision.statut == Statut.ACCEPTE


def test_categorie_sans_delai_utilise_le_delai_par_defaut():
    drive = achat("Supermarché du Coin", "courses", 45, UNE_HEURE_DU_MATIN)
    decision = evaluer_achat(drive, LEA, [])
    assert decision.statut == Statut.PAUSE
    assert decision.delai_minutes == 15


# --- Livraison de repas : pause à chaque commande ---

def test_premiere_livraison_de_la_semaine_pause_quand_meme():
    repas = achat("Pizza Minute", "livraison_repas", 12, datetime(2026, 10, 16, 20, 0))
    decision = evaluer_achat(repas, LEA, HISTORIQUE)  # dernière livraison le 8 : plus de 7 jours
    assert decision.statut == Statut.PAUSE
    assert decision.delai_minutes == 5
    assert codes(decision) == {"categorie_impulsive"}


def test_deuxieme_livraison_en_7_jours_message_renforce():
    repas = achat("Pizza Minute", "livraison_repas", 12, datetime(2026, 10, 10, 20, 0))
    decision = evaluer_achat(repas, LEA, HISTORIQUE)  # MiamExpress le 8 octobre
    assert decision.statut == Statut.PAUSE
    assert codes(decision) == {"categorie_impulsive", "repetition"}
    assert "2e commande" in decision.regles[1].message


# --- Affichage des montants ---

@pytest.mark.parametrize("montant, texte", [
    (Decimal("89"), "89 €"),
    (Decimal("9.99"), "9,99 €"),
    (Decimal("114.8"), "114,80 €"),
])
def test_format_euros(montant, texte):
    assert format_euros(montant) == texte
