"""Tests du parcours complet de la démo (CLAUDE.md §3), sur les données de Léa.

Le 10 octobre 2026 à 1 h, Léa veut acheter des baskets à 89 € chez Sneak'Air.
Délai vêtements : 30 min. Achats en ligne d'octobre avant cet achat : 25,79 €.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from app.epargne import historique, progression
from app.horloge import Horloge
from app.models import Transaction, charger_donnees
from app.paiement import (
    StatutPaiement,
    bilan_a_epargner,
    compte_initial,
    epargner_bilan,
    payer,
    renoncer,
    verser_epargne,
)

UNE_HEURE_DU_MATIN = datetime(2026, 10, 10, 1, 0)


def baskets(quand: datetime, canal="en_ligne") -> Transaction:
    return Transaction(
        commercant="Sneak'Air", categorie="vetements", montant=Decimal("89"),
        canal=canal, date_heure=quand,
    )


@pytest.fixture
def compte():
    """Un compte neuf pour chaque test, chargé depuis data/."""
    return compte_initial(charger_donnees())


def codes(resultat) -> set[str]:
    return {regle.code for regle in resultat.regles}


# --- Premier essai : pause ---

def test_premier_essai_pause_et_achat_memorise(compte):
    nouveau, resultat = payer(compte, baskets(UNE_HEURE_DU_MATIN))
    assert resultat.statut == StatutPaiement.PAUSE
    assert resultat.secondes_restantes == 30 * 60
    assert resultat.heure_deblocage == datetime(2026, 10, 10, 1, 30)
    assert codes(resultat) == {"confirmation", "limite_categorie"}
    assert len(nouveau.suspendus) == 1
    assert len(nouveau.transactions) == len(compte.transactions)  # rien n'est payé
    assert compte.suspendus == []  # le compte d'origine n'a pas bougé


# --- Variante A : Léa renonce et épargne ---

def test_variante_a_renoncer_puis_epargner(compte):
    compte, _ = payer(compte, baskets(UNE_HEURE_DU_MATIN))

    compte, proposition = renoncer(compte, "Sneak'Air", Decimal("89"), datetime(2026, 10, 10, 1, 5))
    assert compte.suspendus == []
    assert proposition.somme_conseillee == Decimal("44")
    assert proposition.message.startswith("Bravo")

    compte = verser_epargne(compte, proposition.somme_conseillee, datetime(2026, 10, 10, 1, 6))
    assert compte.profil.objectif.deja_epargne == Decimal("194")  # 150 + 44
    assert progression(compte.profil.objectif) == 10


def test_renoncer_a_un_achat_inconnu(compte):
    with pytest.raises(ValueError):
        renoncer(compte, "Sneak'Air", Decimal("89"), UNE_HEURE_DU_MATIN)


# --- Variante B : Léa attend la fin du délai et repaie ---

def test_variante_b_repaiement_trop_tot_puis_apres_le_delai(compte):
    nb_transactions = len(compte.transactions)
    compte, _ = payer(compte, baskets(UNE_HEURE_DU_MATIN))

    compte, resultat = payer(compte, baskets(datetime(2026, 10, 10, 1, 10)))
    assert resultat.statut == StatutPaiement.PAUSE
    assert resultat.secondes_restantes == 20 * 60
    assert "20 min" in resultat.message

    compte, resultat = payer(compte, baskets(datetime(2026, 10, 10, 1, 30)))
    assert resultat.statut == StatutPaiement.ACCEPTE
    assert len(compte.transactions) == nb_transactions + 1
    assert compte.suspendus == []


def test_un_achat_debloque_ne_sert_qu_une_fois(compte):
    compte, _ = payer(compte, baskets(UNE_HEURE_DU_MATIN))
    compte, _ = payer(compte, baskets(datetime(2026, 10, 10, 1, 30)))
    # Une deuxième paire : nouvel achat, nouvelle pause.
    compte, resultat = payer(compte, baskets(datetime(2026, 10, 10, 1, 35)))
    assert resultat.statut == StatutPaiement.PAUSE
    assert "budget_total" in codes(resultat)  # 114,79 + 89 > 120 €


# --- Hors périmètre ---

def test_en_magasin_paiement_immediat(compte):
    nouveau, resultat = payer(compte, baskets(UNE_HEURE_DU_MATIN, canal="magasin"))
    assert resultat.statut == StatutPaiement.ACCEPTE
    assert len(nouveau.transactions) == len(compte.transactions) + 1


def test_loyer_paiement_immediat(compte):
    loyer = Transaction(
        commercant="Résidence Les Tilleuls", categorie="loyer", montant=Decimal("420"),
        canal="en_ligne", date_heure=datetime(2026, 11, 1, 9, 0),
    )
    assert payer(compte, loyer)[1].statut == StatutPaiement.ACCEPTE


# --- Blocage strict ---

def test_blocage_strict_refus_sans_memorisation(compte):
    profil_strict = compte.profil.model_copy(update={"blocage_strict": True})
    compte = compte.model_copy(update={"profil": profil_strict})
    nouveau, resultat = payer(compte, baskets(UNE_HEURE_DU_MATIN))
    assert resultat.statut == StatutPaiement.REFUSE
    assert nouveau.suspendus == []
    assert nouveau.transactions == compte.transactions


def test_desactiver_le_blocage_strict_prend_effet_immediatement(compte):
    strict = compte.model_copy(update={"profil": compte.profil.model_copy(update={"blocage_strict": True})})
    strict, resultat = payer(strict, baskets(UNE_HEURE_DU_MATIN))
    assert resultat.statut == StatutPaiement.REFUSE

    libre = strict.model_copy(update={"profil": strict.profil.model_copy(update={"blocage_strict": False})})
    _, resultat = payer(libre, baskets(datetime(2026, 10, 10, 1, 1)))
    assert resultat.statut == StatutPaiement.PAUSE


# --- La démo de bout en bout, avec l'horloge simulée ---

def test_demo_complete_avec_horloge(compte):
    horloge = Horloge(UNE_HEURE_DU_MATIN)

    compte, resultat = payer(compte, baskets(horloge.maintenant()))
    assert resultat.statut == StatutPaiement.PAUSE

    horloge.avancer(30)  # bouton « +30 min »
    compte, resultat = payer(compte, baskets(horloge.maintenant()))
    assert resultat.statut == StatutPaiement.ACCEPTE

    horloge.aller_au_mois_suivant()  # bouton « fin du mois »
    octobre = historique(compte.profil, compte.transactions, horloge.maintenant().date())[-1]
    assert (octobre.annee, octobre.mois) == (2026, 10)
    assert octobre.depenses_en_ligne == Decimal("114.79")  # 25,79 + 89
    assert octobre.economies == Decimal("5.21")

    compte = verser_epargne(compte, octobre.economies, horloge.maintenant())
    assert compte.profil.objectif.deja_epargne == Decimal("155.21")


# --- Bilan de fin de mois : proposé chaque mois, une seule fois ---

def test_bilan_propose_a_chaque_fin_de_mois(compte):
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    # Au début de la démo, le dernier mois terminé (septembre) est dépassé : rien à épargner.
    assert bilan_a_epargner(compte, horloge.maintenant().date()) is None

    horloge.aller_au_mois_suivant()  # 1er novembre : bilan d'octobre
    octobre = bilan_a_epargner(compte, horloge.maintenant().date())
    assert (octobre.mois, octobre.economies) == (10, Decimal("94.21"))
    compte = epargner_bilan(compte, 2026, 10, Decimal("94.21"), horloge.maintenant())
    assert bilan_a_epargner(compte, horloge.maintenant().date()) is None  # déjà traité

    horloge.aller_au_mois_suivant()  # 1er décembre : bilan de novembre, mois sans achat
    novembre = bilan_a_epargner(compte, horloge.maintenant().date())
    assert (novembre.mois, novembre.economies) == (11, Decimal("120"))


def test_ne_rien_epargner_traite_aussi_le_mois(compte):
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    horloge.aller_au_mois_suivant()
    compte = epargner_bilan(compte, 2026, 10, Decimal("0"), horloge.maintenant())
    assert compte.profil.objectif.deja_epargne == Decimal("150")
    assert bilan_a_epargner(compte, horloge.maintenant().date()) is None


def test_epargner_un_bilan_deja_traite_ou_trop_eleve_refuse(compte):
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    horloge.aller_au_mois_suivant()
    with pytest.raises(ValueError):
        epargner_bilan(compte, 2026, 10, Decimal("200"), horloge.maintenant())  # > 94,21 €
    compte = epargner_bilan(compte, 2026, 10, Decimal("50"), horloge.maintenant())
    with pytest.raises(ValueError):
        epargner_bilan(compte, 2026, 10, Decimal("10"), horloge.maintenant())  # déjà traité
