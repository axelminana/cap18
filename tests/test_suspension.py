"""Tests de la mémorisation des achats suspendus (règles de CLAUDE.md §5)."""

from datetime import datetime, timedelta
from decimal import Decimal

from app.models import Transaction
from app.regles import RegleDeclenchee
from app.suspension import EtatTentative, memoriser, retirer, verifier_tentative

PREMIER_ESSAI = datetime(2026, 10, 10, 1, 0)
DELAI_VETEMENTS = 30


def baskets(quand, montant=89, commercant="Sneak'Air") -> Transaction:
    return Transaction(
        commercant=commercant, categorie="vetements", montant=Decimal(str(montant)),
        canal="en_ligne", date_heure=quand,
    )


def apres(**duree) -> datetime:
    return PREMIER_ESSAI + timedelta(**duree)


# Léa a tenté d'acheter les baskets à 1 h : l'achat est mémorisé avec 30 min de délai.
SUSPENDUS = memoriser(baskets(PREMIER_ESSAI), DELAI_VETEMENTS, [])


# --- Règle 1 : le premier essai est mémorisé ---

def test_memorisation_du_premier_essai():
    assert len(SUSPENDUS) == 1
    memorise = SUSPENDUS[0]
    assert memorise.commercant == "Sneak'Air"
    assert memorise.montant == Decimal("89")
    assert memorise.date_essai == PREMIER_ESSAI
    assert memorise.heure_deblocage == datetime(2026, 10, 10, 1, 30)


def test_memoriser_ne_modifie_pas_la_liste_d_origine():
    liste_vide = []
    memoriser(baskets(PREMIER_ESSAI), DELAI_VETEMENTS, liste_vide)
    assert liste_vide == []


# --- Règle 2 : nouvel essai avant le déblocage ---

def test_repaiement_avant_la_fin_du_delai_toujours_suspendu():
    resultat = verifier_tentative(baskets(apres(minutes=10)), SUSPENDUS)
    assert resultat.etat == EtatTentative.TOUJOURS_SUSPENDU
    assert resultat.secondes_restantes == 20 * 60


# --- Règle 3 : nouvel essai après le déblocage, même commerçant, même montant ---

def test_repaiement_pile_a_l_heure_de_deblocage_accepte():
    resultat = verifier_tentative(baskets(apres(minutes=30)), SUSPENDUS)
    assert resultat.etat == EtatTentative.DEBLOQUE
    assert resultat.achat_memorise == SUSPENDUS[0]


def test_repaiement_apres_le_delai_accepte():
    assert verifier_tentative(baskets(apres(hours=2)), SUSPENDUS).etat == EtatTentative.DEBLOQUE


# --- Règle 4 : montant différent ou autre commerçant ---

def test_montant_different_nouvel_achat():
    resultat = verifier_tentative(baskets(apres(minutes=40), montant=79), SUSPENDUS)
    assert resultat.etat == EtatTentative.NOUVEL_ACHAT


def test_autre_commercant_nouvel_achat():
    resultat = verifier_tentative(baskets(apres(minutes=40), commercant="Mode Urbaine"), SUSPENDUS)
    assert resultat.etat == EtatTentative.NOUVEL_ACHAT


# --- Règle 5 : expiration au bout de 24 h ---

def test_juste_avant_24h_toujours_valable():
    resultat = verifier_tentative(baskets(apres(hours=23, minutes=59)), SUSPENDUS)
    assert resultat.etat == EtatTentative.DEBLOQUE


def test_apres_24h_nouvel_achat():
    assert verifier_tentative(baskets(apres(hours=24)), SUSPENDUS).etat == EtatTentative.NOUVEL_ACHAT


def test_rememoriser_apres_expiration_remplace_l_ancien():
    nouveaux = memoriser(baskets(apres(hours=25)), DELAI_VETEMENTS, SUSPENDUS)
    assert len(nouveaux) == 1
    assert nouveaux[0].date_essai == apres(hours=25)


# --- Gestion de la liste ---

def test_plusieurs_achats_suspendus_en_meme_temps():
    repas = Transaction(
        commercant="Pizza Minute", categorie="livraison_repas", montant=Decimal("12"),
        canal="en_ligne", date_heure=apres(minutes=5),
    )
    liste = memoriser(repas, 5, SUSPENDUS)
    assert len(liste) == 2
    # La pizza est débloquée à 1 h 10, les baskets toujours suspendues.
    a_1h10_repas = repas.model_copy(update={"date_heure": apres(minutes=10)})
    assert verifier_tentative(a_1h10_repas, liste).etat == EtatTentative.DEBLOQUE
    assert verifier_tentative(baskets(apres(minutes=10)), liste).etat == EtatTentative.TOUJOURS_SUSPENDU


def test_retirer_un_achat():
    assert retirer(SUSPENDUS[0], SUSPENDUS) == []
    assert len(SUSPENDUS) == 1  # la liste d'origine n'a pas bougé


def test_l_achat_memorise_garde_les_raisons_de_la_pause():
    regles = [RegleDeclenchee(code="confirmation", message="30 min de réflexion")]
    liste = memoriser(baskets(PREMIER_ESSAI), DELAI_VETEMENTS, [], regles)
    assert liste[0].regles == regles
