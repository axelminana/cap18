"""Tests du tableau de score personnel (US4), sur les données de Léa.

Mois terminés au 10 octobre 2026 : août réussi (71,51 € économisés),
septembre dépassé (0 €). Octobre : 25,79 € dépensés en ligne au 10.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.epargne import BilanMensuel
from app.models import Transaction, charger_donnees
from app.paiement import compte_initial, demarrer_nouvel_objectif, payer, renoncer, verser_epargne
from app.score import calculer_score, series

AUJOURD_HUI = date(2026, 10, 10)
UNE_HEURE = datetime(2026, 10, 10, 1, 0)
DEBUT_NOVEMBRE = date(2026, 11, 1)


@pytest.fixture
def compte():
    return compte_initial(charger_donnees())


def obtenus(badges) -> set[str]:
    return {b.code for b in badges if b.obtenu}


def bilan(respecte: bool) -> BilanMensuel:
    economies = Decimal("10") if respecte else Decimal("0")
    return BilanMensuel(annee=2026, mois=1, budget=Decimal("120"), depenses_en_ligne=Decimal("110"),
                        economies=economies, budget_respecte=respecte)


# --- Séries de mois réussis ---

@pytest.mark.parametrize("mois, en_cours, meilleure", [
    ([], 0, 0),
    ([True, False, True, True], 2, 2),
    ([True, True, True, False], 0, 3),
    ([False, True], 1, 1),
])
def test_series(mois, en_cours, meilleure):
    assert series([bilan(r) for r in mois]) == (en_cours, meilleure)


# --- Score au début de la démo ---

def test_score_initial_de_lea(compte):
    score, badges = calculer_score(compte, AUJOURD_HUI)
    assert score.serie_en_cours == 0          # septembre dépassé
    assert score.meilleure_serie == 1         # août réussi
    assert score.achats_evites == 0
    assert score.total_epargne == 0
    assert score.progression == 8
    assert (score.meilleur_mois.annee, score.meilleur_mois.mois) == (2026, 8)
    assert score.ecart_mois_precedent == Decimal("-71.51")
    assert obtenus(badges) == {"premier_mois_reussi"}


def test_tous_les_badges_sont_listes_meme_non_obtenus(compte):
    _, badges = calculer_score(compte, AUJOURD_HUI)
    assert len(badges) == 6


# --- Après un renoncement et un versement (variante A) ---

def test_renoncer_et_epargner_fait_progresser_le_score(compte):
    baskets = Transaction(commercant="Sneak'Air", categorie="vetements", montant=Decimal("89"),
                          canal="en_ligne", date_heure=UNE_HEURE)
    compte, _ = payer(compte, baskets)
    compte, proposition = renoncer(compte, "Sneak'Air", Decimal("89"), UNE_HEURE)
    compte = verser_epargne(compte, proposition.somme_conseillee, UNE_HEURE)

    score, badges = calculer_score(compte, AUJOURD_HUI)
    assert score.achats_evites == 1
    assert score.montant_evite == Decimal("89")
    assert score.total_epargne == Decimal("44")
    assert "premier_achat_evite" in obtenus(badges)
    assert compte.achats_evites[0].categorie == "vetements"


def test_ne_rien_epargner_n_est_pas_un_versement(compte):
    compte = verser_epargne(compte, Decimal("0"), UNE_HEURE)
    assert compte.versements == []


# --- Fin du mois : comparaison entre mois ---

def test_fin_octobre_mois_reussi_et_progres(compte):
    score, badges = calculer_score(compte, DEBUT_NOVEMBRE)
    assert score.serie_en_cours == 1
    assert (score.meilleur_mois.mois, score.meilleur_mois.economies) == (10, Decimal("94.21"))
    assert score.ecart_mois_precedent == Decimal("94.21")  # septembre : 0 €


# --- Badges d'épargne ---

def test_badge_100_euros(compte):
    compte = verser_epargne(compte, Decimal("60"), UNE_HEURE)
    assert "cent_euros" not in obtenus(calculer_score(compte, AUJOURD_HUI)[1])
    compte = verser_epargne(compte, Decimal("40"), UNE_HEURE)
    assert "cent_euros" in obtenus(calculer_score(compte, AUJOURD_HUI)[1])


def test_badges_de_progression_de_l_objectif(compte):
    compte = verser_epargne(compte, Decimal("300"), UNE_HEURE)  # 450 / 1800 = 25 %
    badges = obtenus(calculer_score(compte, AUJOURD_HUI)[1])
    assert "objectif_25" in badges and "objectif_50" not in badges
    compte = verser_epargne(compte, Decimal("450"), UNE_HEURE)  # 900 / 1800 = 50 %
    assert "objectif_50" in obtenus(calculer_score(compte, AUJOURD_HUI)[1])



def test_les_badges_d_objectif_restent_acquis_avec_un_nouveau_projet(compte):
    compte = verser_epargne(compte, Decimal("1650"), UNE_HEURE)  # 1 800 / 1 800 €
    compte = demarrer_nouvel_objectif(compte, "Voiture", Decimal("3000"), date(2029, 10, 10))
    score, badges = calculer_score(compte, AUJOURD_HUI)
    assert score.progression == 0 and score.objectifs_atteints == 1
    assert {"objectif_25", "objectif_50"} <= obtenus(badges)
