# CLAUDE.md — Projet « Cap 18 » (Hackathon Sopra Steria 2026)

Ce fichier donne à Claude Code tout le contexte du projet. Lis-le en entier avant toute action.

## 1. Contexte de l'événement

- Hackathon Sopra Steria 2026, thème « Banque de demain » : imaginer une banque plus utile, plus sûre et plus inclusive.
- Le PIC, Clermont-Ferrand, samedi 10 et dimanche 11 octobre 2026.
- Défi officiel : transformer un besoin réel en une expérience simple, explicable et démontrable, **avec des données fictives** et l'humain au centre.
- Objectif de notre équipe : **fidéliser une nouvelle clientèle jeune** pour la banque.

### Calendrier des jurys
| Quand | Quoi | Attendus clés |
|---|---|---|
| Samedi 15h30 | Pitch 1 minute | Besoin, ébauche de solution, adhésion, originalité |
| Dimanche 11h30 | Jury fonctionnel | 3 user stories (+1 facultative), chacune avec description, tests de validation, maquette |
| Dimanche 11h30 | Jury technique | 6 min de présentation + 3 min de questions. Démo live qui tourne **sans crash**, stack justifiée, Git, répartition des tâches, difficultés surmontées |
| Dimanche 15h | Jury final | < 7 min + 3 min de questions. Besoin, triangle Viabilité/Désirabilité/Faisabilité, démo du parcours client |

### Règles du jury technique sur l'IA (TRÈS IMPORTANT)
- L'IA est autorisée, mais le binôme doit **comprendre et pouvoir expliquer chaque ligne**.
- Pénalisé : effet « boîte noire », dépendances ou complexité inutiles.
- Valorisé : MVP simple et fonctionnel plutôt que projet surchargé, tests sur des cas concrets, transparence sur l'aide de l'IA.

## 2. Le concept : Cap 18, de Parcoursup au premier appart

**Problème :** au moment du bac, un jeune ne sait pas ce que coûtera réellement chacun de ses vœux, ni à quelles aides il a droit. Puis, le jour de ses 18 ans, ses parents perdent d'un coup l'accès à son compte : il passe du contrôle total à aucun filet. C'est aussi le moment où il risque de quitter la banque familiale pour une néobanque.

**Solution :** une fonctionnalité intégrée à l'application bancaire, en deux temps.
1. **En terminale : « Le vrai coût de mes vœux ».** Pour chaque vœu Parcoursup (la formation et la ville sont données, on ne recommande pas de ville), on calcule le coût mensuel réel moins les aides estimées, puis le reste à financer comparé à ce que le jeune et ses parents peuvent mettre (avec consentement).
2. **À 18 ans : « Du contrôle parental au contrôle personnel ».** Le jeune choisit ses propres garde-fous (règles sur ses dépenses) et décide s'il garde un parent comme simple « témoin » (alerté en cas d'opération inhabituelle, sans voir le solde).

**Persona principale :** Léa, 17 ans, terminale à Aurillac, boursière de lycée. Vœux : BUT à Lyon, licence à Bordeaux, licence à Clermont-Ferrand. Mère : Sophie, cliente historique de la banque.

**Proposition de valeur pour la banque :** capter le jeune dès 17 ans via le parent déjà client, le garder pendant la période 18-25 ans où il risque de partir, proposer les bons produits au bon moment (Livret Jeune, assurance habitation, prêt étudiant).

## 3. User stories du MVP

**US1 — Comparer le coût réel de mes vœux**
En tant que lycéen, je souhaite voir le coût mensuel réel de chacun de mes vœux, afin de savoir lesquels sont finançables.
- Coût = loyer (selon type : Crous / colocation / studio) + alimentation + transports + allers-retours chez les parents selon la distance + divers.

**US2 — Découvrir mes aides par vœu**
En tant que lycéen, je souhaite connaître les aides estimées pour chaque vœu, afin de ne pas passer à côté d'un droit.
- Bourse sur critères sociaux (barème simplifié, voir §5), APL estimée, aide à la mobilité Parcoursup.
- Toujours afficher « estimation » + renvoi vers les simulateurs officiels.

**US3 — Créer mes garde-fous pour ma rentrée**
En tant que jeune majeur, je souhaite créer mes propres règles de dépenses, afin de limiter mes dépenses impulsives sans perdre mon autonomie.
- Exemple de règle : « tout achat > 40 € entre 23h et 6h est mis en attente 12h ».
- Évaluation des règles sur un flux de transactions fictives.

**US4 (facultative) — Choisir ce que mon parent voit à 18 ans**
Mode « témoin » : le parent ne voit pas le solde, il est seulement alerté pour une opération inhabituelle, si le jeune l'a accepté. Révocable à tout moment.

**Démo cible pour le jury final :** un curseur « temps » fait passer Léa de 17 ans (comparaison des vœux avec sa mère) à 18 ans (création d'une règle, puis une commande à 1h du matin mise en attente).

## 4. Données (toutes fictives)

- `villes.json` : coût moyen par ville (loyer Crous / colocation / studio, transports, alimentation). Valeurs plausibles, présentées comme fictives.
- `famille.json` : foyer fictif de Léa (revenus, enfants à charge, ville de résidence, académie).
- `transactions.json` : quelques mois de transactions fictives catégorisées (dont des achats nocturnes) pour la démo des garde-fous.
- `voeux.json` : les 3 vœux de Léa (formation, ville, académie, distance).

## 5. Règles métier (version simplifiée à afficher comme estimation)

- **Bourse sur critères sociaux** : dépend des revenus des parents, des enfants à charge et de la distance domicile-études. Points de charge pour la distance : 30 à 249 km = 1 point, 250 km et plus = 2 points. Utiliser un barème simplifié et fictif inspiré du réel ; ne pas présenter les montants comme officiels.
- **Aide à la mobilité Parcoursup** : 500 € versés une fois, pour un lycéen boursier de lycée qui accepte un vœu hors de son académie de résidence. (Lyon est hors de l'académie de Clermont-Ferrand ; Clermont-Ferrand est dans la même académie qu'Aurillac.)
- **APL** : estimation forfaitaire simple selon le type de logement.
- Le coût ne doit jamais servir à « recommander une ville » : on éclaire un choix de formation, on ne le fait pas à la place du jeune.

## 6. Stack et principes techniques

- Proposition (à valider par l'équipe) : React + Vite pour le front (responsive, vue mobile), petite API FastAPI ou Node, données en JSON ou SQLite.
- **Pas d'IA générative dans le produit** : tout est calculé par des règles explicables.
- Le moteur de règles (US3) et le calcul des aides (US2) doivent être des fonctions pures, testées sur des cas concrets (ex. : Léa à Lyon → aide mobilité ; Léa à Clermont → pas d'aide mobilité).
- Dépendances minimales. Chaque ajout de librairie doit être justifié.
- Git dès le début, commits fréquents et lisibles.

## 7. Comment travailler avec moi (consignes pour Claude Code)

- Avancer **par petites étapes**. Avant chaque étape, annoncer ce qui va être fait ; après, expliquer brièvement le code produit pour que l'équipe puisse le défendre devant le jury.
- Préférer du code simple et lisible à du code astucieux.
- Ne pas ajouter de fonctionnalités hors du périmètre ci-dessus sans demander.
- Priorité absolue : une démo qui tourne sans crash. En cas de manque de temps, couper US4 d'abord, puis simplifier US3.
- Répondre en français.

## 8. Vigilance (à mentionner au jury)

- RGPD et consentement : accès aux données des parents uniquement avec leur accord ; mode témoin choisi et révocable par le jeune majeur.
- Responsabilité : les aides sont des estimations, avec renvoi vers les simulateurs officiels.
- Ton : pas moralisateur, ce sont les règles du jeune, pas celles de la banque.
