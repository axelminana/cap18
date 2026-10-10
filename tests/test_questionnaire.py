"""Tests du questionnaire de réflexion (achat de 3 % de l'objectif ou moins).

Objectif de Léa : permis à 1 800 €, donc questionnaire jusqu'à 54 € d'achat.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.models import Categorie, Transaction, charger_donnees
from app.paiement import compte_initial, payer
from app.questionnaire import QUESTION_COMMUNE, QUESTIONS_PAR_CATEGORIE, questions_pour

DONNEES = charger_donnees()
LEA = DONNEES.profil
UNE_HEURE = datetime(2026, 10, 10, 1, 0)


def achat(categorie, montant, commercant="Bazar en Ligne", quand=UNE_HEURE) -> Transaction:
    return Transaction(commercant=commercant, categorie=categorie, montant=Decimal(str(montant)),
                       canal="en_ligne", date_heure=quand)


def textes(questions) -> list[str]:
    return [q.texte for q in questions]


def test_pizza_question_commune_et_question_repas():
    questions = questions_pour(achat("livraison_repas", 15.80), LEA, rang=0)
    assert textes(questions) == [
        "En as-tu vraiment besoin, ou est-ce une envie du moment ?",
        "Peux-tu te préparer quelque chose avec ce que tu as chez toi ?",
    ]


def test_les_questions_de_la_categorie_tournent():
    pizza = achat("livraison_repas", 15.80)
    assert textes(questions_pour(pizza, LEA, rang=1))[1] == "Ne penses-tu pas que c'est plutôt l'ennui ou la fatigue ?"
    assert questions_pour(pizza, LEA, rang=2) == questions_pour(pizza, LEA, rang=0)  # on revient au début


def test_au_dela_de_3_pourcent_pas_de_questionnaire():
    # Baskets 89 € = 4,9 % du permis : c'est la règle « part_objectif » qui s'affiche à la place.
    assert questions_pour(achat("vetements", 89), LEA, rang=0) == []
    assert len(questions_pour(achat("vetements", 54), LEA, rang=0)) == 2  # 3 % pile


def test_questionnaire_desactive_dans_mon_contrat():
    sans = LEA.model_copy(update={"questionnaire": False})
    assert questions_pour(achat("livraison_repas", 15.80), sans, rang=0) == []


def test_active_par_defaut():
    assert LEA.questionnaire


@pytest.mark.parametrize("categorie", list(QUESTIONS_PAR_CATEGORIE))
def test_au_plus_2_questions_a_2_reponses_pour_chaque_categorie(categorie):
    questions = questions_pour(achat(categorie, 10), LEA, rang=0)
    assert 1 <= len(questions) <= 2 and questions[0] == QUESTION_COMMUNE
    assert all(len(q.choix) == 2 and all(c.libelle and c.reponse for c in q.choix) for q in questions)


def test_les_categories_necessaires_n_ont_pas_de_questions():
    assert not {Categorie.LOYER, Categorie.FACTURES, Categorie.COURSES} & set(QUESTIONS_PAR_CATEGORIE)


# --- Dans le parcours de paiement ---

def test_la_pause_memorise_les_questions_et_les_fait_tourner():
    compte = compte_initial(DONNEES)
    compte, _ = payer(compte, achat("livraison_repas", 15.80, "MiamExpress"))
    compte, _ = payer(compte, achat("livraison_repas", 12.50, "Pizza Minute"))
    assert compte.pauses == 2
    premiere, deuxieme = compte.suspendus
    assert premiere.questions[1].texte.startswith("Peux-tu te préparer")
    assert deuxieme.questions[1].texte.startswith("Ne penses-tu pas")
