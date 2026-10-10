# Cap 18 — Dépenser, c'est facile. Choisir… ça s'apprend.

Projet du **Hackathon Sopra Steria 2026** (thème « Banque de demain »).

Cap 18 est une fonctionnalité d'appli bancaire pour les 18-25 ans. Avant chaque achat en ligne non nécessaire, elle impose une **pause de réflexion**. Si l'utilisateur renonce, l'appli le **félicite** et lui propose de **verser une partie de la somme vers son objectif d'épargne**. Chaque fin de mois, il voit ce qu'il a économisé et sa progression.

Persona de la démo : **Léa, 18 ans**, premier appartement, premier job étudiant. Son objectif : **son permis de conduire, 1 800 € d'ici octobre 2027**.

> Toutes les données sont **fictives** (personne, commerçants, transactions). Aucune IA générative dans le produit : tout est calculé par des règles explicables.

---

## Sommaire

1. [Lancer la démo](#1-lancer-la-démo)
2. [Les règles métier en bref](#2-les-règles-métier-en-bref)
3. [Architecture](#3-architecture)
4. [Le code, module par module](#4-le-code-module-par-module)
5. [Le front](#5-le-front)
6. [Les tests](#6-les-tests)
7. [Pour le jury technique](#7-pour-le-jury-technique)

Documents complémentaires :
- [`ARCHITECTURE.md`](ARCHITECTURE.md) : technologies, arborescence, choix de conception, routes de l'API ;
- [`CLAUDE.md`](CLAUDE.md) : contexte du hackathon, user stories, règles métier détaillées, décisions de l'équipe.

---

## 1. Lancer la démo

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest                              # 149 tests
uvicorn app.main:app --reload       # puis ouvrir http://127.0.0.1:8000
```

La documentation interactive de l'API est sur http://127.0.0.1:8000/docs.

La page de démo affiche **la boutique fictive à gauche** et **le téléphone de Léa à droite**. La barre du bas pilote l'horloge de la démo, qui commence le samedi 10 octobre 2026 à 1 h du matin.

### Parcours à présenter

1. **Variante A, Léa renonce.**
   - Dans la boutique, « Payer 89 € » pour les baskets.
   - Sur le téléphone, une pause de réflexion de 30 min s'affiche, avec ses raisons.
   - « Je renonce » → « Bravo ! … Et si tu mettais 44 € de côté ? ».
   - Le curseur est à 50 % (44 €) ; on peut le déplacer (ex. 75 % → 66 €) → « Épargner 44 € ».
   - L'onglet **Mon score** affiche 1 achat évité et 44 € épargnés.
2. **« Réinitialiser la démo ».**
3. **Variante B, Léa attend.**
   - « Payer 89 € », puis « +30 min ».
   - Dans la boutique, « Relancer le paiement » → la commande est confirmée.
4. **Fin du mois.**
   - « Fin du mois » → carte du bilan d'octobre sur l'Accueil.
   - Choix : tout épargner, une partie ou rien.
   - « Fin du mois » une 2e fois → bilan de novembre (mois sans achat : 120 € économisés).
   - Onglets **Bilan** et **Mon score**.

---

## 2. Les règles métier en bref

| Règle | Comportement |
|---|---|
| Périmètre | Uniquement les **paiements en ligne**. Les achats en magasin et les dépenses nécessaires (loyer, factures, courses) ne sont jamais mis en pause. |
| Pause de réflexion | **Tout achat en ligne non nécessaire** demande une confirmation après le délai de sa catégorie, **quelle que soit l'heure**. |
| Délais conseillés | Livraison de repas 5 min, vêtements 30 min, électronique 60 min, jeux vidéo 30 min, abonnements 10 min, autres 15 min. Modifiables par l'utilisateur (< 24 h). |
| Raisons affichées en plus | Limite de la catégorie dépassée, budget en ligne du mois dépassé, 2e livraison de repas en 7 jours. |
| Achat mémorisé | Le 1er essai est refusé et mémorisé. Un nouvel essai **même commerçant, même montant** après le délai passe sans nouvelle pause. Avant le délai, il reste en pause. Expiration au bout de **24 h**. |
| Blocage strict | **Désactivé par défaut.** S'il est activé, un achat qui dépasse une limite est refusé. La désactivation prend effet immédiatement. |
| Après un renoncement | Félicitations, avec une somme conseillée = **50 % du montant évité**, arrondie à l'euro inférieur, plafonnée au budget en ligne restant. Un **curseur** (0 à 100 %, 50 % par défaut) permet d'en choisir une autre. |
| Plan d'épargne | Objectif à **moins de 5 ans → Livret A**, **5 ans ou plus → PEA** (capital non garanti). Versement mensuel = reste à épargner / mois restants, arrondi à l'euro supérieur. Toujours présenté comme une **suggestion**. |
| Bilan du mois | Économies = budget en ligne − achats en ligne du mois (0 si dépassé). Proposé à chaque fin de mois, une seule fois, même pour un mois sans achat. L'utilisateur choisit d'épargner tout, une partie ou rien. |
| Objectif atteint | L'utilisateur démarre un nouveau projet ; ce qu'il a épargné en plus est reporté dessus. |
| Échéance dépassée | Sans reproche, l'appli propose de choisir une nouvelle date ou d'ajuster l'objectif ; ce qui est épargné est gardé. |
| Tableau de score | **Strictement personnel**, uniquement des encouragements : séries de mois réussis, achats évités, total épargné, meilleur mois, badges. |

---

## 3. Architecture

```
 Navigateur                          Serveur Python (FastAPI)
┌──────────────────────┐           ┌──────────────────────────────────────┐
│ boutique.html        │  fetch    │ main.py   (API JSON + pages)         │
│ (fausse boutique)    │ ───────►  │    │                                 │
│                      │           │    ▼                                 │
│ banque.html          │ ◄───────  │ paiement.py (orchestration)          │
│ (appli mobile Léa)   │   JSON    │    ├── regles.py     (pause, raisons)│
└──────────────────────┘           │    ├── suspension.py (achats mémo.)  │
  Aucune logique métier            │    ├── epargne.py    (plan, bilan)   │
  côté navigateur                  │    └── score.py      (US4)           │
                                   │ horloge.py (temps simulable)         │
                                   │ models.py  (modèles Pydantic)        │
                                   │ data/*.json (données fictives)       │
                                   └──────────────────────────────────────┘
```

**Stack :**

| Techno | Rôle |
|---|---|
| Python | Langage unique |
| Pydantic | Modèles et validation des données |
| pytest | Tests |
| FastAPI + Uvicorn | API et serveur |
| HTML / CSS / JavaScript sans framework | Front |
| JSON | Données |

Les dépendances sont limitées à 5 et leurs versions sont figées dans `requirements.txt`.

**Trois principes guident tout le code :**
1. **Fonctions pures.** Toute la logique métier est faite de fonctions qui reçoivent des données et renvoient un résultat, sans rien modifier. Mêmes entrées, même résultat. C'est ce qui les rend simples à tester.
2. **Le temps est un paramètre.** Aucune fonction métier ne lit l'heure de l'ordinateur. L'heure est portée par l'achat ou passée en argument. On peut donc tester « 1 h du matin » ou « 24 h plus tard » sans attendre, et piloter le temps pendant la démo.
3. **L'API ne contient aucune règle.** Chaque route lit l'état, appelle une fonction métier déjà testée, enregistre le nouvel état et renvoie la réponse.

---

## 4. Le code, module par module

### `app/models.py` : la forme des données
Les modèles Pydantic décrivent la forme attendue des données. Quand on leur donne du JSON, ils vérifient et convertissent chaque champ, ou lèvent une erreur claire.

**Les modèles :**
- `Categorie` et `Canal` : listes fermées (`Enum`). Une catégorie ou un canal inconnu est refusé.
- `Transaction` : commerçant, catégorie, montant (> 0), canal, date et heure.
- `Objectif` : nom, montant, échéance, déjà épargné.
- `Profil` : tout le contrat de Léa (revenus, dépenses obligatoires, budget en ligne, limites et délais par catégorie, blocage strict à `False` par défaut, objectif).

**`verifier_coherence`** contrôle le profil entier :
- pas de limite ni de délai sur une dépense nécessaire ;
- une limite ne dépasse pas le budget en ligne ;
- un délai est compris entre 0 et 24 h. Au-delà, l'achat mémorisé expirerait avant d'être débloqué.

**Les constantes :**
- `CATEGORIES_OBLIGATOIRES` : loyer, factures, courses ;
- `DELAIS_CONSEILLES` ;
- `LIBELLES_CATEGORIES` : noms affichés, comme « vêtements » ou « livraison de repas ».

**`charger_donnees()`** lit et valide les trois fichiers de `data/`. En cas d'erreur, le message indique le fichier en cause.

Les montants sont en **`Decimal`** et non en `float`, qui stocke 9,99 € de façon approchée. `Decimal` garde les centimes exacts.

### `app/horloge.py` : l'horloge simulable
La classe `Horloge` a deux modes :
- **réel** : l'heure de l'ordinateur ;
- **simulé** : une heure fixée, qui n'avance que sur demande.

| Méthode | Rôle |
|---|---|
| `avancer(minutes)` | Avance le temps. Refuse 0 ou un nombre négatif : le temps ne recule pas. |
| `aller_au_mois_suivant()` | Passe au 1er du mois suivant à 9 h. Gère décembre → janvier. |
| `revenir_au_reel()` | Revient à l'heure de l'ordinateur. |

C'est le seul objet du projet qui garde un état, avec l'état de l'API.

### `app/regles.py` : la pause de réflexion (US2)
`evaluer_achat(achat, profil, transactions)` renvoie une `Decision`, qui contient :
- un statut : `accepte`, `pause` ou `refuse` ;
- les règles déclenchées, chacune avec un `code` stable et un `message` en langage clair ;
- le délai.

La fonction procède en 5 étapes :
1. Achat en magasin ou dépense nécessaire → **accepté**.
2. Sinon, la règle **`confirmation`** s'applique toujours : « Achat en ligne « vêtements » de 89 € : tu as choisi de prendre 30 min de réflexion avant de le valider. »
3. On ajoute les raisons supplémentaires :
   - `limite_categorie` ;
   - `budget_total` ;
   - `repetition`, à partir de la 2e livraison de repas sur 7 jours glissants.
4. Blocage strict activé avec une limite dépassée → **refusé**.
5. Sinon → **pause**, avec le délai de la catégorie (15 min par défaut).

**Fonctions utilitaires :**
- `achats_en_ligne_du_mois()` : partagée avec l'épargne, pour que le budget se calcule de la même façon partout ;
- `format_euros()` : « 89 € », « 9,99 € ».

**Ton des messages :** ils rappellent que c'est l'utilisateur qui a fixé ses règles (« la limite de 60 € que tu t'es fixée »). Ils ne font jamais la morale.

### `app/suspension.py` : la mémorisation des achats suspendus
C'est le problème technique central. Un site marchand abandonne un paiement non validé rapidement. La banque refuse donc le premier essai **et se souvient de l'achat**.

`AchatSuspendu` contient :
- le commerçant, la catégorie et le montant exact ;
- la date de l'essai et l'heure de déblocage ;
- les raisons de la pause.

**`verifier_tentative(achat, suspendus)`** renvoie l'un des 3 états suivants :

| État | Quand |
|---|---|
| `nouvel_achat` | Rien de mémorisé, ou montant ou commerçant différent, ou achat expiré (24 h) |
| `toujours_suspendu` | Même achat, délai pas fini (avec les secondes restantes) |
| `debloque` | Même achat, délai fini |

**Les autres fonctions :**
- **`memoriser()`** ajoute l'achat (heure de déblocage = essai + délai) et nettoie au passage les achats expirés.
- **`retirer()`** enlève un achat une fois payé, ou quand l'utilisateur renonce.

Ces fonctions ne modifient jamais la liste reçue : elles en renvoient une nouvelle.

### `app/epargne.py` : l'épargne (US1, US2, US3)
**Plan conseillé et renoncement :**
- **`plan_conseille(objectif, aujourd_hui)`** : Livret A ou PEA selon l'horizon, avec le versement mensuel et les mentions (« pas un conseil en investissement », « capital non garanti » pour le PEA). Pour Léa : (1 800 − 150) / 12 mois → **138 €/mois sur un Livret A**. Si l'échéance est dépassée, on compte au moins 1 mois, jamais de division par zéro.
- **`somme_conseillee()`** et **`proposition_apres_renoncement()`** produisent la somme et le message de félicitations. Pour les baskets : **44 €**. Si le budget est déjà dépassé, Léa reçoit les félicitations seules, sans reproche.
- **`sommes_par_pourcentage()`** calcule la somme de chaque position du curseur (0, 5… 100 %) avec la même règle. Le JavaScript ne fait que lire ce tableau : aucun calcul côté navigateur.
- **`budget_restant()`** : budget en ligne moins les achats en ligne du mois.

**Bilan et progression :**
- **`bilan_mensuel()`** et **`historique()`** : économies par mois. L'historique contient tous les mois terminés, **même un mois sans achat** (tout le budget est alors économisé). Pour Léa : août 71,51 € économisés, septembre dépassé.
- **`epargner()`** renvoie un nouvel objectif. Un montant négatif est refusé.
- **`progression()`** : pourcentage atteint, plafonné à 100 %.
- **`objectif_atteint()`**, **`surplus()`** et **`nouvel_objectif()`** : quand l'objectif est atteint, on démarre le projet suivant en reportant le surplus (1 850 € pour 1 800 € → 50 € reportés).
- **`echeance_depassee()`** et **`modifier_objectif()`** : si la date est passée sans que l'objectif soit atteint, le plan le dit clairement et Léa peut changer la date, le montant ou le nom, en gardant son épargne. Une échéance doit toujours être dans le futur.

### `app/paiement.py` : l'orchestration du parcours
**`Compte`** regroupe tout l'état de Léa :
- profil ;
- transactions ;
- achats suspendus ;
- achats évités ;
- versements.

**`payer(compte, achat)`** renvoie `(nouveau_compte, résultat)` :

```
Achat déjà mémorisé ? (suspension.py)
├── oui, délai pas fini  → PAUSE   « Encore 20 min de réflexion… »
├── oui, délai fini      → ACCEPTÉ  enregistré + retiré des suspendus
└── non → règles (regles.py)
          ├── accepté → ACCEPTÉ  enregistré
          ├── refusé  → REFUSÉ   rien n'est stocké
          └── pause   → PAUSE    achat mémorisé
```

**Les deux autres fonctions :**
- **`renoncer()`** retire l'achat suspendu, l'enregistre comme achat évité et renvoie la proposition d'épargne.
- **`verser_epargne()`** met à jour l'objectif et enregistre le versement. « Ne rien épargner » n'est pas un versement.
- **`bilan_a_epargner()`** et **`epargner_bilan()`** : le bilan du dernier mois terminé est proposé une seule fois. Le mois traité est enregistré dans le `Compte` (côté serveur), donc recharger la page ne change rien.
- **`demarrer_nouvel_objectif()`** remplace l'objectif atteint ; les badges d'objectif déjà gagnés restent acquis.

### `app/score.py` : le tableau de score personnel (US4)
- **`series()`** parcourt les mois terminés : un mois réussi fait +1, un mois dépassé remet la série à 0. On retient la série en cours et le record.
- **`calculer_score()`** calcule :
  - les achats évités (nombre et montant) ;
  - le total épargné avec l'appli ;
  - la progression ;
  - les économies par mois, le meilleur mois et l'écart avec le mois précédent.
- **`badges()`** renvoie 6 badges positifs, obtenus ou à débloquer : premier achat évité, premier mois réussi, 3 mois de suite, 100 € épargnés, objectif à 25 % et à 50 %.

Il n'y a aucune comparaison avec d'autres utilisateurs et aucun badge négatif.

### `app/main.py` : l'API FastAPI
**`EtatDemo`** est le seul état en mémoire : le compte de Léa, les commerçants et l'horloge. `reinitialiser()` recharge les données d'origine.

**Les routes :**

| Route | Rôle |
|---|---|
| `GET /api/etat` | Profil, plan, progression, budget restant, achats en pause avec leur temps restant, libellés et délais conseillés |
| `POST /api/paiement` | Paiement. Reçoit seulement `{commercant, montant}` : **la catégorie est détectée automatiquement** à partir du commerçant, comme le ferait le code MCC d'une vraie transaction carte |
| `POST /api/renoncer` | Renoncer à un achat suspendu |
| `POST /api/epargner` | Verser vers l'objectif |
| `POST /api/bilan/epargner` | Épargner tout, une partie ou rien du bilan du mois terminé |
| `POST /api/objectif/nouveau` | Démarrer un nouveau projet quand l'objectif est atteint |
| `POST /api/objectif/modifier` | Ajuster l'objectif quand l'échéance est dépassée |
| `GET /api/bilan` | Bilan et historique |
| `GET /api/score` | Tableau de score |
| `PUT /api/profil` | Modifier le contrat |
| `/api/horloge/...` | Piloter le temps de la démo |
| `POST /api/reinitialiser` | Remettre la démo à zéro |

**Erreurs propres plutôt que plantages :**
- **404** : commerçant inconnu, ou rien à quoi renoncer ;
- **400** : temps en arrière ;
- **422** : donnée invalide, géré automatiquement par Pydantic.

Les montants sont envoyés en JSON sous forme de texte (`"89"`) pour garder l'exactitude des centimes.

---

## 5. Le front

HTML, CSS et JavaScript **sans framework**. Le JavaScript **ne fait aucun calcul métier** : il appelle l'API et affiche les réponses.

| Fichier | Rôle |
|---|---|
| `static/index.html` + `demo.js` | Page de démo : la boutique et le téléphone côte à côte (deux `iframe`), et la barre de contrôle de l'horloge (+1 / +5 / +30 min, fin du mois, réinitialiser) |
| `static/boutique.html` + `boutique.js` | Boutique fictive « Street Market » (4 produits). Elle envoie seulement le commerçant et le prix, puis affiche : commande confirmée, en attente de ta banque (avec « Relancer le paiement ») ou refusé |
| `static/banque.html` + `banque.js` | Appli de Léa en 4 onglets, décrits ci-dessous |
| `static/commun.js` | Appel de l'API, mise en forme des montants et des dates, `echapper()` |
| `static/style.css` | Style commun |

**Les 4 onglets de l'appli de Léa :**
- **Accueil** : achats en pause (raisons, temps restant, « Je renonce »), félicitations et épargne, carte de fin de mois, objectif, budget.
- **Bilan** : mois en cours et historique.
- **Mon score** : tuiles, barres par mois, badges.
- **Mon contrat** : revenus, dépenses obligatoires, budget, limites et délais avec la valeur conseillée, blocage strict, objectif.

**Choix techniques :**
- **Rafraîchissement :** l'appli interroge le serveur chaque seconde, comme une notification push simplifiée. Elle ne redessine que si la réponse a changé, pour ne pas perdre un clic.
- **Délégation d'événements :** un seul écouteur de clics par page, qui regarde quel bouton a été cliqué grâce à ses attributs `data-…`.
- **Sécurité :** tout texte venant du serveur passe par `echapper()` et n'est jamais interprété comme du HTML.
- **Temps de la démo :** l'horloge n'avance que par les boutons. Le temps restant se met à jour quand on avance l'heure, ce qui rend la démo reproductible.
- **Accès direct à un onglet :** `banque.html#score` ou `banque.html#bilan`.

---

## 6. Les tests

**149 tests pytest**, sur les données réelles de Léa et des cas concrets. On les lance avec `pytest`.

| Fichier | Tests | Ce qui est vérifié |
|---|---|---|
| `test_models.py` | 14 | Chargement des JSON, valeurs par défaut, erreurs claires (montant négatif, catégorie inconnue, limite > budget, délai ≥ 24 h…) |
| `test_horloge.py` | 10 | +30 min, passage de minuit, décembre → janvier, le temps ne recule pas |
| `test_regles.py` | 23 | Cas de référence (voir ci-dessous) |
| `test_suspension.py` | 13 | Les 5 règles de mémorisation, avec les cas limites (pile au déblocage, 23 h 59, 24 h pile) |
| `test_epargne.py` | 41 | Plan Livret A / PEA, seuil des 5 ans, échéance dépassée, somme conseillée, positions du curseur, bilans (dont un mois sans achat), nouveau projet, échéance dépassée |
| `test_paiement.py` | 13 | Variantes A et B, blocage strict, **démo complète avec l'horloge simulée**, bilan proposé à chaque fin de mois |
| `test_score.py` | 12 | Séries, score de départ, progression après renoncement, badges (conservés avec un nouveau projet) |
| `test_api.py` | 23 | Les variantes A et B par requêtes HTTP, bilan, nouveau projet, échéance dépassée, erreurs 404 / 400 / 422, pages servies |

**Les cas de référence demandés dans le cahier des charges :**

| Cas | Résultat attendu |
|---|---|
| Baskets 89 € en ligne | Pause de 30 min (raisons : confirmation et limite vêtements dépassée) |
| Même achat en magasin | Accepté |
| Loyer | Jamais de pause, même en blocage strict |
| Repaiement du même montant après le délai | Accepté |
| Repaiement avant la fin du délai | Toujours suspendu, avec le temps restant |
| Blocage strict activé et limite dépassée | Refus |

---

## 7. Pour le jury technique

**Pourquoi cette stack ?**
- Un seul langage pour toute la logique.
- Pydantic valide les données avec des erreurs claires.
- FastAPI s'appuie sur Pydantic et génère `/docs`.
- Pas de framework front : rien à compiler.
- Pas de base de données : l'état tient en mémoire, ce qui suffit pour un MVP.

**Difficultés surmontées :**
1. **Le paiement abandonné par le site marchand.** On ne peut pas « suspendre » un paiement pendant 30 minutes. La solution est de refuser le premier essai, de **mémoriser l'achat**, puis d'accepter le repaiement identique après le délai, avec une expiration à 24 h.
2. **Tester le temps.** L'horloge simulée, et le fait que le temps soit passé en paramètre, permettent de tester « 30 minutes plus tard » ou « fin du mois » instantanément, et de piloter la démo en direct.
3. **Les arrondis d'argent.** L'usage de `Decimal` évite les erreurs de centimes des nombres à virgule.
4. **Un bug trouvé en répétition.** Les boutons de l'appli ne réagissaient pas, car un `<button>` HTML sans attribut `type` est de type `submit` par défaut et était ignoré par l'écouteur de clics. La correction tient en une ligne : on ignore seulement les boutons du formulaire.

**Évolution des règles en cours de hackathon :**
- Une règle « achat nocturne » a d'abord été codée, puis abandonnée par l'équipe au profit d'une pause sur **tout** achat en ligne non nécessaire, quelle que soit l'heure.
- Grâce aux fonctions pures et aux tests, le changement a été fait et vérifié en quelques minutes.

**Utilisation de l'IA (transparence) :**
- Le code a été écrit par Axel avec l'aide de **Claude Code**, étape par étape.
- Chaque étape a été annoncée, expliquée, testée puis validée avant de passer à la suivante.
- L'historique Git suit ces étapes (un commit par étape, avec un message clair).

**Limites assumées :**
- Seuls les achats en ligne sont concernés.
- L'état est en mémoire, donc remis à zéro au redémarrage du serveur.
- Les données sont fictives.
- Le plan d'épargne est une suggestion, pas un conseil en investissement.
