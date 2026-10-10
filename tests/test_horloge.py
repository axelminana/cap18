"""Tests de l'horloge simulable."""

from datetime import datetime, timedelta

import pytest

from app.horloge import Horloge

UNE_HEURE_DU_MATIN = datetime(2026, 10, 10, 1, 0)


def test_mode_reel_par_defaut():
    horloge = Horloge()
    assert not horloge.est_simulee()
    assert abs(horloge.maintenant() - datetime.now()) < timedelta(seconds=1)


def test_heure_fixee_ne_bouge_pas_toute_seule():
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    assert horloge.maintenant() == UNE_HEURE_DU_MATIN
    assert horloge.maintenant() == UNE_HEURE_DU_MATIN


def test_avancer_de_30_minutes():
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    horloge.avancer(30)
    assert horloge.maintenant() == datetime(2026, 10, 10, 1, 30)


def test_avancer_passe_au_jour_suivant():
    horloge = Horloge(datetime(2026, 10, 10, 23, 50))
    horloge.avancer(20)
    assert horloge.maintenant() == datetime(2026, 10, 11, 0, 10)


def test_avancer_en_mode_reel_passe_en_mode_simule():
    horloge = Horloge()
    avant = datetime.now()
    horloge.avancer(60)
    assert horloge.est_simulee()
    assert horloge.maintenant() >= avant + timedelta(minutes=60)


@pytest.mark.parametrize("minutes", [0, -10])
def test_le_temps_ne_recule_pas(minutes):
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    with pytest.raises(ValueError):
        horloge.avancer(minutes)
    assert horloge.maintenant() == UNE_HEURE_DU_MATIN


def test_mois_suivant():
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    horloge.aller_au_mois_suivant()
    assert horloge.maintenant() == datetime(2026, 11, 1, 9, 0)


def test_mois_suivant_en_decembre_change_d_annee():
    horloge = Horloge(datetime(2026, 12, 15, 14, 0))
    horloge.aller_au_mois_suivant()
    assert horloge.maintenant() == datetime(2027, 1, 1, 9, 0)


def test_revenir_au_reel():
    horloge = Horloge(UNE_HEURE_DU_MATIN)
    horloge.revenir_au_reel()
    assert not horloge.est_simulee()
