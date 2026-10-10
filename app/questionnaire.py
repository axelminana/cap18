"""Questionnaire de réflexion, affiché pendant la pause d'un achat qui pèse peu sur l'objectif.

Non intrusif, par choix :
- 2 questions au maximum : une commune + une de la catégorie, à tour de rôle ;
- deux réponses en un clic, sans texte à écrire, et un bouton « Passer » ;
- aucun délai ajouté, aucune réponse enregistrée ni jugée : chaque réponse affiche
  seulement une phrase bienveillante ;
- activé par défaut, désactivable dans « Mon contrat » (Profil.questionnaire).

Au-delà de 3 % de l'objectif, c'est la règle « part_objectif » qui s'affiche à la place.
"""

from pydantic import BaseModel

from app.models import Categorie, Profil, Transaction
from app.regles import pese_sur_l_objectif

C_EST_TOI_QUI_DECIDES = "OK, c'est toi qui décides 👍"
LA_PAUSE_EST_LA = "Si tu hésites, la pause est là pour ça."


class Choix(BaseModel):
    libelle: str   # texte du bouton
    reponse: str   # phrase affichée après le clic


class Question(BaseModel):
    texte: str
    choix: list[Choix]


def question(texte: str, choix_1: tuple[str, str], choix_2: tuple[str, str]) -> Question:
    return Question(texte=texte, choix=[Choix(libelle=l, reponse=r) for l, r in (choix_1, choix_2)])


QUESTION_COMMUNE = question(
    "En as-tu vraiment besoin, ou est-ce une envie du moment ?",
    ("J'en ai besoin", C_EST_TOI_QUI_DECIDES),
    ("C'est une envie", "Les envies passent souvent : profite de la pause pour voir si celle-ci tient."),
)

QUESTIONS_PAR_CATEGORIE: dict[Categorie, list[Question]] = {
    Categorie.LIVRAISON_REPAS: [
        question("Peux-tu te préparer quelque chose avec ce que tu as chez toi ?",
                 ("Oui", "Bonne idée ! Si tu renonces, tu peux mettre la différence de côté."),
                 ("Non", C_EST_TOI_QUI_DECIDES)),
        question("Ne penses-tu pas que c'est plutôt l'ennui ou la fatigue ?",
                 ("Peut-être", "Une pause, un verre d'eau… et si l'envie passe, tu sais quoi faire 😉"),
                 ("Non, j'ai faim", "OK, bon appétit ! C'est toi qui décides.")),
    ],
    Categorie.VETEMENTS: [
        question("As-tu déjà quelque chose de similaire dans ton armoire ?",
                 ("Oui", "Alors cet achat peut sans doute attendre."),
                 ("Non", C_EST_TOI_QUI_DECIDES)),
        question("Le porteras-tu au moins 10 fois ?",
                 ("Oui", C_EST_TOI_QUI_DECIDES),
                 ("Pas sûr", LA_PAUSE_EST_LA)),
    ],
    Categorie.ELECTRONIQUE: [
        question("Ton appareil actuel fonctionne-t-il encore ?",
                 ("Oui", "Alors rien ne presse : tu peux attendre une bonne occasion."),
                 ("Non", C_EST_TOI_QUI_DECIDES)),
        question("As-tu comparé les prix ou pensé au reconditionné ?",
                 ("Oui", C_EST_TOI_QUI_DECIDES),
                 ("Pas encore", "Le reconditionné coûte souvent bien moins cher : ça vaut le coup de regarder.")),
    ],
    Categorie.JEUX_VIDEO: [
        question("As-tu fini le dernier jeu que tu as acheté ?",
                 ("Oui", C_EST_TOI_QUI_DECIDES),
                 ("Pas encore", "Il peut peut-être t'occuper encore un peu ?")),
        question("Son prix baisse souvent après la sortie : peux-tu attendre ?",
                 ("Oui", "Bonne stratégie : ton portefeuille te remerciera."),
                 ("Non", C_EST_TOI_QUI_DECIDES)),
    ],
    Categorie.ABONNEMENTS: [
        question("Utilises-tu vraiment tes abonnements actuels ?",
                 ("Oui", C_EST_TOI_QUI_DECIDES),
                 ("Pas tous", "C'est peut-être l'occasion d'en arrêter un ?")),
        question("Pourrais-tu en arrêter un autre à la place ?",
                 ("Oui", "Bonne idée : ton budget reste le même."),
                 ("Non", C_EST_TOI_QUI_DECIDES)),
    ],
    Categorie.AUTRES: [
        question("Si tu attends une semaine, en auras-tu toujours envie ?",
                 ("Oui", C_EST_TOI_QUI_DECIDES),
                 ("Pas sûr", LA_PAUSE_EST_LA)),
    ],
}


def questions_pour(achat: Transaction, profil: Profil, rang: int) -> list[Question]:
    """Les questions à afficher pour cet achat en pause (liste vide si aucune).

    rang = nombre de pauses déjà faites : à chaque nouvelle pause, on passe à la question
    suivante de la catégorie, pour ne pas reposer toujours la même.
    """
    if not profil.questionnaire or pese_sur_l_objectif(achat.montant, profil.objectif):
        return []
    questions = [QUESTION_COMMUNE]
    de_la_categorie = QUESTIONS_PAR_CATEGORIE.get(achat.categorie, [])
    if de_la_categorie:
        questions.append(de_la_categorie[rang % len(de_la_categorie)])
    return questions
