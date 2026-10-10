"""Tests du moteur de la pause de réflexion, sur des cas concrets.

Le profil est celui de Léa (data/profil.json) :
budget en ligne 120 €, limite vêtements 60 €, délai vêtements 30 min, délai repas 5 min.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models import Categorie, Transaction, charger_donnees
from app.regles import Statut, evaluer_achat, format_euros, part_de_l_objectif, pese_sur_l_objectif

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
    assert codes(decision) == {"confirmation", "limite_categorie", "part_objectif"}


def test_message_en_langage_clair_avec_le_delai():
    decision = evaluer_achat(BASKETS_LA_NUIT, LEA, HISTORIQUE)
    assert "30 min" in decision.regles[0].message
    assert "89 €" in decision.regles[1].message and "60 €" in decision.regles[1].message


def test_meme_achat_en_magasin_pas_de_pause():
    en_magasin = achat("Sneak'Air", "vetements", 89, UNE_HEURE_DU_MATIN, canal="magasin")
    assert evaluer_achat(en_magasin, LEA, HISTORIQUE).statut == Statut.ACCEPTE


def test_loyer_jamais_de_pause_meme_en_blocage_strict():
    loyer = achat("Résidence Les Tilleuls", "loyer", 420, UNE_HEURE_DU_MATIN)
    lea_stricte = LEA.model_copy(update={"blocage_strict": True})
    assert evaluer_achat(loyer, LEA, HISTORIQUE).statut == Statut.ACCEPTE
    assert evaluer_achat(loyer, lea_stricte, HISTORIQUE).statut == Statut.ACCEPTE


def test_courses_en_ligne_necessaires_pas_de_pause():
    drive = achat("Supermarché du Coin", "courses", 45, QUATORZE_HEURES)
    assert evaluer_achat(drive, LEA, HISTORIQUE).statut == Statut.ACCEPTE


def test_blocage_strict_et_limite_depassee_refus():
    lea_stricte = LEA.model_copy(update={"blocage_strict": True})
    decision = evaluer_achat(BASKETS_LA_NUIT, lea_stricte, HISTORIQUE)
    assert decision.statut == Statut.REFUSE
    assert "limite_categorie" in codes(decision)


def test_blocage_strict_sans_depassement_reste_une_simple_pause():
    lea_stricte = LEA.model_copy(update={"blocage_strict": True})
    petit_achat = achat("Bazar en Ligne", "autres", 25, QUATORZE_HEURES)
    decision = evaluer_achat(petit_achat, lea_stricte, HISTORIQUE)
    assert decision.statut == Statut.PAUSE
    assert codes(decision) == {"confirmation"}


# --- L'heure n'a aucune importance ---

@pytest.mark.parametrize("heure", [1, 9, 14, 20, 23])
def test_meme_decision_a_toute_heure(heure):
    quand = datetime(2026, 10, 10, heure, 0)
    decision = evaluer_achat(achat("Sneak'Air", "vetements", 89, quand), LEA, HISTORIQUE)
    assert decision.statut == Statut.PAUSE
    assert decision.delai_minutes == 30
    assert codes(decision) == {"confirmation", "limite_categorie", "part_objectif"}


# --- Tout achat en ligne non nécessaire demande confirmation ---

def test_petit_achat_sous_les_limites_demande_quand_meme_confirmation():
    tee_shirt = achat("Mode Urbaine", "vetements", 25, QUATORZE_HEURES)
    decision = evaluer_achat(tee_shirt, LEA, HISTORIQUE)
    assert decision.statut == Statut.PAUSE
    assert codes(decision) == {"confirmation"}


def test_achat_pile_a_la_limite_sans_raison_supplementaire():
    # Les 89 € de baskets de septembre ne comptent pas pour octobre.
    tenue = achat("Mode Urbaine", "vetements", 60, QUATORZE_HEURES)
    # 60 € = 3,3 % de l'objectif de 1 800 € : seule la raison « part de l'objectif » s'ajoute.
    assert codes(evaluer_achat(tenue, LEA, HISTORIQUE)) == {"confirmation", "part_objectif"}


def test_budget_total_depasse():
    octobre = [
        achat("Mode Urbaine", "vetements", 50, datetime(2026, 10, 2, 15, 0)),
        achat("TechnoPlus", "electronique", 45, datetime(2026, 10, 4, 15, 0)),
        achat("Bazar en Ligne", "autres", 20, datetime(2026, 10, 6, 15, 0)),
    ]  # 115 € dépensés en ligne
    jeu = achat("GameZone", "jeux_video", 10, QUATORZE_HEURES)  # sous la limite jeux (20 €)
    decision = evaluer_achat(jeu, LEA, octobre)
    assert decision.statut == Statut.PAUSE
    assert codes(decision) == {"confirmation", "budget_total"}
    assert decision.delai_minutes == 30


def test_courses_ne_comptent_pas_dans_le_budget_en_ligne():
    octobre = [achat("Supermarché du Coin", "courses", 110, datetime(2026, 10, 2, 15, 0))]
    jeu = achat("GameZone", "jeux_video", 15, QUATORZE_HEURES)
    assert codes(evaluer_achat(jeu, LEA, octobre)) == {"confirmation"}


def test_categorie_sans_delai_utilise_le_delai_par_defaut():
    delais_sans_autres = {c: d for c, d in LEA.delais_minutes.items() if c != Categorie.AUTRES}
    lea = LEA.model_copy(update={"delais_minutes": delais_sans_autres})
    decision = evaluer_achat(achat("Bazar en Ligne", "autres", 10, QUATORZE_HEURES), lea, [])
    assert decision.delai_minutes == 15


# --- Livraison de repas : message renforcé dès la 2e commande en 7 jours ---

def test_premiere_livraison_de_la_semaine_confirmation_simple():
    repas = achat("Pizza Minute", "livraison_repas", 12, datetime(2026, 10, 16, 20, 0))
    decision = evaluer_achat(repas, LEA, HISTORIQUE)  # dernière livraison le 8 : plus de 7 jours
    assert decision.statut == Statut.PAUSE
    assert decision.delai_minutes == 5
    assert codes(decision) == {"confirmation"}


def test_deuxieme_livraison_en_7_jours_message_renforce():
    repas = achat("Pizza Minute", "livraison_repas", 12, datetime(2026, 10, 10, 20, 0))
    decision = evaluer_achat(repas, LEA, HISTORIQUE)  # MiamExpress le 8 octobre
    assert codes(decision) == {"confirmation", "repetition"}
    assert "2e commande" in decision.regles[-1].message


# --- Affichage des montants ---

@pytest.mark.parametrize("montant, texte", [
    (Decimal("89"), "89 €"),
    (Decimal("9.99"), "9,99 €"),
    (Decimal("114.8"), "114,80 €"),
])
def test_format_euros(montant, texte):
    assert format_euros(montant) == texte


def test_categorie_affichee_avec_ses_accents():
    decision = evaluer_achat(BASKETS_LA_NUIT, LEA, HISTORIQUE)
    assert "« vêtements »" in decision.regles[0].message


# --- Part de l'objectif : au-delà de 3 % du projet, on montre ce que représente l'achat ---

def test_exemple_du_cahier_des_charges_100_euros_sur_un_projet_de_1000():
    projet = LEA.objectif.model_copy(update={"montant": Decimal("1000"), "deja_epargne": Decimal("0")})
    assert part_de_l_objectif(Decimal("100"), projet) == Decimal("10.0")
    assert pese_sur_l_objectif(Decimal("100"), projet)


@pytest.mark.parametrize("montant, pese", [
    ("54", False),     # 3 % pile de 1 800 € : pas au-delà
    ("54.01", True),
    ("15.80", False),  # une livraison de repas : 0,9 %
])
def test_seuil_des_3_pourcent(montant, pese):
    assert pese_sur_l_objectif(Decimal(montant), LEA.objectif) == pese


def test_message_des_baskets_4_virgule_9_pourcent_du_permis():
    decision = evaluer_achat(achat("Sneak'Air", "vetements", 89, UNE_HEURE_DU_MATIN), LEA, HISTORIQUE)
    regle = next(r for r in decision.regles if r.code == "part_objectif")
    assert regle.message == (
        "Cet achat représente 4,9 % de ton objectif « Permis de conduire » (1800 €). "
        "Veux-tu vraiment le faire ?"
    )


def test_pas_de_message_si_l_objectif_est_deja_atteint():
    atteint = LEA.objectif.model_copy(update={"deja_epargne": Decimal("1800")})
    assert not pese_sur_l_objectif(Decimal("500"), atteint)


def test_le_blocage_strict_ne_refuse_pas_pour_la_part_de_l_objectif():
    strict = LEA.model_copy(update={"blocage_strict": True})
    # Tenue à 60 € : pile à la limite vêtements, sous le budget, mais 3,3 % du permis.
    decision = evaluer_achat(achat("Mode Urbaine", "vetements", 60, QUATORZE_HEURES), strict, HISTORIQUE)
    assert decision.statut == Statut.PAUSE
    assert {r.code for r in decision.regles} == {"confirmation", "part_objectif"}
