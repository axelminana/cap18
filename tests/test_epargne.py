"""Tests de l'épargne : plan conseillé, somme conseillée, bilan, progression.

Données de Léa : objectif permis 1 800 € pour le 10/10/2027, 150 € déjà épargnés,
budget en ligne 120 €. Achats en ligne : août 48,49 €, septembre 164,58 €,
octobre (au 10) 25,79 €.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.epargne import (
    Produit,
    budget_restant,
    echeance_depassee,
    epargner,
    historique,
    modifier_objectif,
    mois_entre,
    nouvel_objectif,
    objectif_atteint,
    plan_conseille,
    progression,
    proposition_apres_renoncement,
    somme_conseillee,
    somme_pour_pourcentage,
    sommes_par_pourcentage,
    surplus,
)
from app.models import Objectif, charger_donnees

DONNEES = charger_donnees()
LEA = DONNEES.profil
PERMIS = LEA.objectif
AUJOURD_HUI = date(2026, 10, 10)


def objectif(echeance, montant=3000, deja_epargne=0) -> Objectif:
    return Objectif(nom="Voiture", montant=montant, echeance=echeance, deja_epargne=deja_epargne)


# --- Plan d'épargne conseillé ---

def test_plan_du_permis_de_lea_livret_a():
    plan = plan_conseille(PERMIS, AUJOURD_HUI)
    assert plan.produit == Produit.LIVRET_A
    assert not plan.long_terme
    assert plan.mois_restants == 12
    assert plan.reste_a_epargner == Decimal("1650")
    assert plan.versement_mensuel == Decimal("138")  # 1650 / 12 = 137,50 -> 138 €
    assert "138 €" in plan.message


def test_objectif_a_6_ans_pea_avec_mention_capital_non_garanti():
    plan = plan_conseille(objectif(date(2032, 10, 10)), AUJOURD_HUI)
    assert plan.produit == Produit.PEA
    assert plan.long_terme
    assert any("pas garanti" in mention for mention in plan.mentions)


def test_toujours_presente_comme_une_suggestion():
    for plan in (plan_conseille(PERMIS, AUJOURD_HUI), plan_conseille(objectif(date(2032, 10, 10)), AUJOURD_HUI)):
        assert any("pas un conseil en investissement" in mention for mention in plan.mentions)


@pytest.mark.parametrize("echeance, produit_attendu", [
    (date(2031, 9, 10), Produit.LIVRET_A),  # 4 ans et 11 mois
    (date(2031, 10, 10), Produit.PEA),      # 5 ans pile : long terme
])
def test_seuil_des_5_ans(echeance, produit_attendu):
    assert plan_conseille(objectif(echeance), AUJOURD_HUI).produit == produit_attendu


def test_echeance_depassee_pas_de_division_par_zero():
    plan = plan_conseille(objectif(date(2026, 1, 1), montant=500), AUJOURD_HUI)
    assert plan.versement_mensuel == Decimal("500")  # tout le reste en une fois


def test_objectif_deja_atteint():
    plan = plan_conseille(objectif(date(2027, 10, 10), montant=500, deja_epargne=600), AUJOURD_HUI)
    assert plan.versement_mensuel == 0
    assert "atteint" in plan.message


@pytest.mark.parametrize("fin, attendu", [
    (date(2026, 11, 10), 1),
    (date(2026, 11, 9), 0),
    (date(2027, 10, 10), 12),
])
def test_mois_entre(fin, attendu):
    assert mois_entre(AUJOURD_HUI, fin) == attendu


# --- Somme conseillée après un renoncement ---

def test_budget_restant_de_lea_en_octobre():
    assert budget_restant(LEA, DONNEES.transactions, AUJOURD_HUI) == Decimal("94.21")


@pytest.mark.parametrize("montant_evite, restant, attendu", [
    ("89", "94.21", "44"),     # 50 % de 89 € = 44,50 -> 44 €
    ("15.80", "94.21", "7"),   # 7,90 -> 7 €
    ("89", "30", "30"),        # plafonnée au budget restant
    ("89", "-10", "0"),        # budget déjà dépassé : rien à proposer
])
def test_somme_conseillee(montant_evite, restant, attendu):
    assert somme_conseillee(Decimal(montant_evite), Decimal(restant)) == Decimal(attendu)


def test_renoncement_aux_baskets_felicitations_et_incitation_a_epargner():
    proposition = proposition_apres_renoncement(Decimal("89"), Decimal("94.21"), PERMIS)
    assert proposition.somme_conseillee == Decimal("44")
    assert proposition.message.startswith("Bravo")
    assert "44 €" in proposition.message and "Permis de conduire" in proposition.message


@pytest.mark.parametrize("pourcentage, restant, attendu", [
    (50, "94.21", "44"),   # position par défaut
    (0, "94.21", "0"),
    (25, "94.21", "22"),   # 22,25 -> 22 €
    (100, "94.21", "89"),  # tout le montant évité
    (100, "60", "60"),     # plafonné au budget restant
])
def test_somme_pour_pourcentage(pourcentage, restant, attendu):
    assert somme_pour_pourcentage(Decimal("89"), pourcentage, Decimal(restant)) == Decimal(attendu)


def test_positions_du_curseur_de_5_en_5():
    sommes = sommes_par_pourcentage(Decimal("89"), Decimal("94.21"))
    assert list(sommes) == list(range(0, 101, 5))  # 0, 5, 10… 100
    assert sommes[50] == Decimal("44") and sommes[100] == Decimal("89")


def test_le_curseur_commence_a_50_pourcent():
    proposition = proposition_apres_renoncement(Decimal("89"), Decimal("94.21"), PERMIS)
    assert proposition.pourcentage_conseille == 50
    assert proposition.sommes_par_pourcentage[50] == proposition.somme_conseillee


def test_renoncement_sans_budget_restant_felicitations_seules():
    proposition = proposition_apres_renoncement(Decimal("89"), Decimal("-10"), PERMIS)
    assert proposition.somme_conseillee == 0
    assert proposition.message == "Bravo ! Tu viens d'éviter une dépense de 89 €."


# --- Bilan du mois et historique ---

def test_historique_contient_seulement_les_mois_termines():
    bilans = historique(LEA, DONNEES.transactions, AUJOURD_HUI)
    assert [(b.annee, b.mois) for b in bilans] == [(2026, 8), (2026, 9)]


def test_un_mois_sans_achat_en_ligne_apparait_dans_l_historique():
    # Au 1er décembre, novembre n'a aucune transaction : il compte quand même, tout est économisé.
    bilans = historique(LEA, DONNEES.transactions, date(2026, 12, 1))
    assert [(b.annee, b.mois) for b in bilans] == [(2026, 8), (2026, 9), (2026, 10), (2026, 11)]
    novembre = bilans[-1]
    assert novembre.depenses_en_ligne == 0
    assert novembre.economies == Decimal("120")
    assert novembre.budget_respecte


def test_historique_vide_sans_transaction():
    assert historique(LEA, [], AUJOURD_HUI) == []


def test_bilan_d_aout_mois_reussi():
    aout = historique(LEA, DONNEES.transactions, AUJOURD_HUI)[0]
    # Loyer, factures et courses en magasin ne comptent pas.
    assert aout.depenses_en_ligne == Decimal("48.49")
    assert aout.economies == Decimal("71.51")
    assert aout.budget_respecte


def test_bilan_de_septembre_budget_depasse_economies_a_zero():
    septembre = historique(LEA, DONNEES.transactions, AUJOURD_HUI)[1]
    assert septembre.depenses_en_ligne == Decimal("164.58")
    assert septembre.economies == 0
    assert not septembre.budget_respecte


# --- Épargner et progression ---

def test_epargner_les_economies_d_aout():
    nouveau = epargner(PERMIS, Decimal("71.51"))
    assert nouveau.deja_epargne == Decimal("221.51")
    assert PERMIS.deja_epargne == Decimal("150")  # l'objectif d'origine n'a pas bougé


def test_ne_rien_epargner_est_un_choix_possible():
    assert epargner(PERMIS, Decimal("0")).deja_epargne == Decimal("150")


def test_montant_negatif_refuse():
    with pytest.raises(ValueError):
        epargner(PERMIS, Decimal("-5"))


def test_progression():
    assert progression(PERMIS) == 8  # 150 / 1800 = 8,3 %
    assert progression(epargner(PERMIS, Decimal("2000"))) == 100  # plafonnée à 100 %


# --- Objectif atteint : démarrer le projet suivant ---

def test_objectif_atteint_et_surplus():
    assert not objectif_atteint(PERMIS)
    assert surplus(PERMIS) == 0
    depasse = epargner(PERMIS, Decimal("1700"))  # 1 850 € sur 1 800 €
    assert objectif_atteint(depasse)
    assert surplus(depasse) == Decimal("50")


def test_nouveau_projet_reporte_le_surplus():
    depasse = epargner(PERMIS, Decimal("1700"))
    voiture = nouvel_objectif(depasse, "Première voiture", Decimal("3000"), date(2029, 10, 10), AUJOURD_HUI)
    assert (voiture.nom, voiture.montant, voiture.deja_epargne) == ("Première voiture", Decimal("3000"), Decimal("50"))
    assert progression(voiture) == 1


def test_nouveau_projet_refuse_si_objectif_pas_atteint():
    with pytest.raises(ValueError):
        nouvel_objectif(PERMIS, "Voiture", Decimal("3000"), date(2029, 10, 10), AUJOURD_HUI)


# --- Échéance dépassée : ajuster l'objectif ---

LENDEMAIN_DE_L_ECHEANCE = date(2027, 10, 11)


def test_echeance_depassee_detectee():
    assert not echeance_depassee(PERMIS, date(2027, 10, 10))  # le jour même : pas encore dépassée
    assert echeance_depassee(PERMIS, LENDEMAIN_DE_L_ECHEANCE)
    atteint = epargner(PERMIS, Decimal("1650"))
    assert not echeance_depassee(atteint, LENDEMAIN_DE_L_ECHEANCE)  # objectif atteint : rien à ajuster


def test_le_plan_previent_que_l_echeance_est_passee():
    plan = plan_conseille(PERMIS, LENDEMAIN_DE_L_ECHEANCE)
    assert "est passée" in plan.message and "150 €" in plan.message


def test_modifier_l_objectif_garde_l_epargne():
    nouveau = modifier_objectif(PERMIS, "Permis de conduire", Decimal("1500"), date(2028, 4, 10), LENDEMAIN_DE_L_ECHEANCE)
    assert (nouveau.montant, nouveau.echeance, nouveau.deja_epargne) == (Decimal("1500"), date(2028, 4, 10), Decimal("150"))
    assert not echeance_depassee(nouveau, LENDEMAIN_DE_L_ECHEANCE)


@pytest.mark.parametrize("echeance", [date(2027, 10, 11), date(2027, 1, 1)])
def test_nouvelle_echeance_dans_le_passe_ou_aujourd_hui_refusee(echeance):
    with pytest.raises(ValueError):
        modifier_objectif(PERMIS, "Permis", Decimal("1800"), echeance, LENDEMAIN_DE_L_ECHEANCE)
