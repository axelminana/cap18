# Architecture et technologies — Cap 18

Document de référence pour le jury technique. Mis à jour à chaque étape du développement.

**Dernière mise à jour :** samedi 10 octobre 2026 — corrections après la répétition de la démo, règle des 3 % et questionnaire de réflexion (voir §4).

## 1. Vue d'ensemble

```
 Navigateur                          Serveur Python (FastAPI)
┌──────────────────────┐           ┌──────────────────────────────────────┐
│ boutique.html        │  fetch    │ main.py   (API JSON + fichiers       │
│ (fausse boutique)    │ ───────►  │            statiques)                │
│                      │           │    │                                 │
│ banque.html          │ ◄───────  │    ▼                                 │
│ (appli mobile Léa)   │   JSON    │ paiement.py (orchestration)          │
└──────────────────────┘           │    ├── regles.py     (pause, raisons)│
  Aucune logique métier            │    ├── suspension.py (achats mémo.)  │
  côté navigateur                  │    ├── questionnaire.py (questions)  │
                                   │    ├── epargne.py    (plan, bilan)   │
                                   │    └── score.py      (US4)           │
                                   │ horloge.py (temps simulable)         │
                                   │ models.py  (modèles Pydantic)        │
                                   │    ▲                                 │
                                   │    │ chargement + validation         │
                                   │ data/*.json (données fictives)       │
                                   └──────────────────────────────────────┘
```

**Principe :** toute la logique est en Python, sous forme de **fonctions pures** (mêmes entrées → même résultat, aucun effet de bord), testées avec pytest. L'API et le front ne font que les appeler et afficher le résultat.

## 2. Technologies

| Techno | Version | Rôle | Pourquoi ce choix |
|---|---|---|---|
| Python | 3.14 | Langage unique du projet | Décision d'équipe, lisible, toute la logique au même endroit |
| Pydantic | 2.14.0 | Modèles et validation des données | Les JSON sont vérifiés au chargement avec des erreurs claires (équivalent de Zod en JS) |
| pytest | 9.1.1 | Tests des fonctions métier | Standard Python, tests courts et lisibles |
| FastAPI | 0.143.0 | API JSON + service des pages | S'appuie sur Pydantic, peu de code, documentation auto (`/docs`) utile en démo |
| Uvicorn | 0.54.0 | Serveur qui exécute FastAPI | Serveur recommandé par FastAPI, une seule commande pour lancer |
| httpx | 0.28.1 | Requis par le `TestClient` de FastAPI | Tests de l'API uniquement ; aucun rôle dans l'application |
| HTML / CSS / JS | — | Deux pages statiques | Pas de framework : rien à installer, rien à compiler |
| JSON | — | Données fictives | Lisible, modifiable à la main, suffisant pour un MVP |

**Ce qu'on n'utilise volontairement pas :** base de données (l'état tient en mémoire pour la démo), framework front (React, etc.), IA générative (tout est calculé par des règles explicables).

**Environnement :** environnement virtuel `.venv` (dépendances isolées du reste de la machine), versions figées dans `requirements.txt`.

## 3. Arborescence

| Chemin | Rôle | État |
|---|---|---|
| `README.md` | Présentation du projet, lancement de la démo, explication du code module par module, tests, arguments pour le jury | ✅ fait |
| `requirements.txt` | Dépendances et versions | ✅ fait |
| `.gitignore` | Fichiers exclus de Git (venv, caches) | ✅ fait |
| `pytest.ini` | Configuration de pytest (les tests trouvent le paquet `app`) | ✅ fait |
| `data/` | `profil.json` (Léa), `commercants.json` (13 commerçants fictifs), `transactions.json` (août → 8 octobre 2026) | ✅ fait |
| `app/models.py` | Modèles Pydantic + chargement et validation des JSON | ✅ fait |
| `app/horloge.py` | Horloge réelle ou simulée (avancer le temps, changer de mois) | ✅ fait |
| `app/regles.py` | Pause de réflexion, raisons affichées, blocage strict | ✅ fait |
| `app/suspension.py` | Mémorisation des achats suspendus (déblocage, expiration 24 h) | ✅ fait |
| `app/epargne.py` | Plan conseillé, somme conseillée après renoncement, bilan mensuel, progression | ✅ fait |
| `app/paiement.py` | `Compte` (profil, transactions, achats suspendus, achats évités, versements), `payer`, `renoncer`, `verser_epargne` | ✅ fait |
| `app/questionnaire.py` | Questionnaire de réflexion : questions commune et par catégorie, choix des questions | ✅ fait |
| `app/score.py` | Tableau de score personnel : séries, achats évités, total épargné, comparaison entre mois, badges | ✅ fait |
| `app/main.py` | API FastAPI (routes `/api/...`) + service des pages de `static/` | ✅ fait |
| `static/` | `index.html` (démo côte à côte + barre de contrôle), `boutique.html`, `banque.html`, `style.css`, `commun.js`, `demo.js`, `boutique.js`, `banque.js` | ✅ fait |
| `tests/` | Un fichier de tests par module (`test_models.py` : 14, `test_horloge.py` : 10, `test_regles.py` : 30, `test_questionnaire.py` : 13, `test_suspension.py` : 13, `test_epargne.py` : 41, `test_paiement.py` : 13, `test_score.py` : 12, `test_api.py` : 24 — 170 tests) | ✅ fait |

## 4. Plan de développement

| Étape | Contenu | État |
|---|---|---|
| 0 | Environnement virtuel, dépendances, `.gitignore` | ✅ fait |
| 1 | Modèles Pydantic + données fictives | ✅ fait |
| 2 | Horloge simulable | ✅ fait |
| 3 | Moteur de la pause de réflexion | ✅ fait |
| 4 | Mémorisation des achats suspendus | ✅ fait |
| 5 | Épargne : plan, somme conseillée, bilan | ✅ fait |
| 6 | Orchestration d'un paiement | ✅ fait |
| 7 | API FastAPI | ✅ fait |
| 8 | Front statique | ✅ fait (répétition de la démo à faire par Axel) |
| 9 | Tableau de score US4 | ✅ fait |

**Corrections après la répétition de la démo :**

| Correction | État |
|---|---|
| Bilan de fin de mois proposé à chaque fin de mois (mois sans achat inclus, suivi côté serveur) | ✅ fait |
| Après un renoncement : curseur pour choisir le pourcentage épargné (50 % par défaut) | ✅ fait |
| Objectif atteint : démarrer un nouveau projet, le surplus est reporté | ✅ fait |
| Échéance dépassée : proposer de changer la date, le montant ou le nom de l'objectif | ✅ fait |
| Achat > 3 % de l'objectif : afficher le pourcentage du projet qu'il représente | ✅ fait |
| Achat ≤ 3 % de l'objectif : questionnaire de réflexion (activé par défaut, désactivable) | ✅ fait |

## 5. Choix de conception

- **Le temps est un paramètre :** les fonctions métier reçoivent `maintenant` en argument et n'appellent jamais l'heure système. On peut donc tester « 1 h du matin » ou « 24 h plus tard » sans attendre, et avancer le temps pendant la démo.
- **Montants en `Decimal` :** un `float` stocke 0,1 de façon approchée ; `Decimal` garde les centimes exacts (9,99 € reste 9,99).
- **Catégories fermées (`Enum`) :** une catégorie inconnue est refusée dès le chargement. Les catégories nécessaires (loyer, factures, courses) ne peuvent avoir ni limite ni délai, ne sont jamais mises en pause et ne comptent pas dans le budget en ligne.
- **Validation à deux niveaux :** chaque champ a ses contraintes (montant > 0, âge entre 18 et 25), puis un contrôle de cohérence du profil (une limite ne dépasse pas le budget en ligne).
- **Données de Léa :** revenus 850 €, obligatoires 490 €, budget en ligne 120 €, objectif permis 1 800 € pour octobre 2027. Septembre est volontairement un mois de dépassement (baskets à 1 h, livraisons répétées).
- **Horloge à deux modes :** réelle par défaut, ou simulée (heure fixée qui n'avance que sur demande : « +30 min », « mois suivant » au 1er à 9 h). Le temps ne peut pas reculer. Seule l'API l'utilise pour fournir `maintenant` aux fonctions métier.
- **Moteur de la pause (`evaluer_achat`) :** l'heure de l'achat n'a aucune importance. Ordre de décision : hors périmètre (magasin ou dépense nécessaire) → accepté ; sinon la règle « confirmation » s'applique toujours ; blocage strict + dépassement de limite ou de budget → refusé ; sinon → pause avec le délai de la catégorie (15 min par défaut).
- **Raisons supplémentaires affichées :** limite de catégorie dépassée, budget total en ligne du mois dépassé, « répétition » dès la 2e livraison de repas sur 7 jours glissants, « part_objectif » si l'achat dépasse 3 % du montant de l'objectif (ex. baskets 89 € = 4,9 % du permis de 1 800 € ; pas affiché si l'objectif est atteint ; jamais un motif de refus du blocage strict). Chaque règle a un `code` stable (pour le front et les tests) et un `message` en langage clair. La règle de nuit a été abandonnée (décision d'équipe).
- **Questionnaire de réflexion (`questionnaire.py`) :** pour un achat de 3 % de l'objectif ou moins (au-delà, c'est « part_objectif » qui s'affiche). Les questions sont des **données** (`Question` → 2 `Choix`, chacun avec son libellé et sa phrase de réponse bienveillante). `questions_pour(achat, profil, rang)` renvoie la question commune + une question de la catégorie, choisie à tour de rôle (`rang` = nombre de pauses déjà faites, `Compte.pauses`). Les questions sont mémorisées avec l'achat suspendu (`AchatSuspendu.questions`), comme ses raisons. Non intrusif : 2 questions maximum, réponses en un clic, « Passer », aucun délai ajouté, **aucune réponse envoyée au serveur** (gardées dans le navigateur pour l'affichage seulement). Activé par défaut, désactivable dans « Mon contrat » (`Profil.questionnaire`).
- **Mémorisation (`suspension.py`) :** `verifier_tentative` renvoie l'un des 3 états : `nouvel_achat` (rien de mémorisé, montant ou commerçant différent, ou achat expiré), `toujours_suspendu` (avec les secondes restantes, pour le compte à rebours), `debloque`. `memoriser` ajoute l'achat (heure de déblocage = essai + délai) et nettoie les achats expirés ; `retirer` l'enlève une fois payé ou abandonné. Le temps est porté par l'achat (`date_heure`). Un délai de réflexion doit être inférieur à 24 h (contrôlé dans `Profil`), sinon l'achat expirerait avant d'être débloqué.
- **Épargne (`epargne.py`) :** plan conseillé = Livret A si moins de 5 ans (60 mois), PEA sinon (mention « capital non garanti ») ; versement mensuel = reste à épargner / mois restants, arrondi à l'euro supérieur (au moins 1 mois, jamais de division par zéro). Après un renoncement : félicitations + somme conseillée = 50 % du montant évité, arrondie à l'euro inférieur, plafonnée au budget en ligne restant (0 si dépassé). Léa peut choisir un autre pourcentage avec un curseur (0 à 100 %, de 5 en 5, 50 % par défaut) : `sommes_par_pourcentage` calcule en Python la somme de chaque position du curseur, avec la même règle (arrondi, plafond) ; le JavaScript ne fait que lire la ligne du tableau. Bilan = budget − achats en ligne du mois (0 si négatif) ; l'historique contient tous les mois terminés depuis la première transaction, **y compris un mois sans aucun achat en ligne** (mois réussi, tout le budget est économisé). `epargner` renvoie un nouvel objectif (tout, une partie ou rien). Objectif atteint (`objectif_atteint`) : `nouvel_objectif` démarre le projet suivant en reportant le `surplus` (ce qui dépasse l'ancien montant, ex. 1 850 € pour 1 800 € → 50 € reportés) ; refusé tant que l'objectif n'est pas atteint. Échéance dépassée sans avoir atteint l'objectif (`echeance_depassee`) : le plan le signale au lieu de proposer de tout verser en un mois, et `modifier_objectif` change la date, le montant ou le nom en **gardant ce qui est déjà épargné**. Une nouvelle échéance doit être dans le futur (`verifier_echeance`, aussi pour un nouveau projet). Le calcul « achats en ligne du mois » est partagé avec `regles.py` (`achats_en_ligne_du_mois`).
- **Orchestration (`paiement.py`) :** tout l'état de Léa tient dans un seul objet `Compte`. `payer(compte, achat)` renvoie `(nouveau_compte, résultat)` : achat déjà mémorisé et encore en délai → pause avec temps restant ; mémorisé et débloqué → accepté, enregistré et retiré des suspendus ; sinon on applique les règles → accepté (enregistré), refusé (rien n'est stocké) ou pause (mémorisé). `renoncer` retire l'achat suspendu et renvoie félicitations + somme conseillée ; `verser_epargne` met à jour l'objectif. `bilan_a_epargner` renvoie le bilan du dernier mois terminé s'il a des économies et n'a pas encore été traité ; `epargner_bilan` verse tout, une partie ou rien (0) et marque le mois comme traité dans `Compte.bilans_traites` (refus si le mois est déjà traité ou si le montant dépasse les économies). Ce suivi est côté serveur : recharger la page ne fait ni réapparaître ni disparaître un bilan. `demarrer_nouvel_objectif` remplace l'objectif atteint et garde son nom dans `Compte.objectifs_atteints` ; `ajuster_objectif` applique `modifier_objectif` au compte. Les tests jouent la démo de bout en bout avec l'horloge simulée.
- **API (`main.py`) :** un seul objet `EtatDemo` en mémoire (compte de Léa + horloge, démo au 10/10/2026 à 1 h). Chaque route lit l'état, appelle une fonction métier, enregistre le nouvel état. La boutique n'envoie que le commerçant et le montant : la catégorie est **détectée automatiquement** via `commercants.json` (comme un code MCC). Erreurs renvoyées proprement : 404 (commerçant inconnu, aucun achat à abandonner), 400 (temps en arrière), 422 (donnée invalide, via Pydantic). Les montants `Decimal` sont envoyés en JSON sous forme de texte (`"89"`) pour garder les centimes exacts. Libellés lisibles des catégories (`LIBELLES_CATEGORIES`) pour les messages.
- **Front (`static/`) :** HTML + CSS + JavaScript sans framework. `index.html` place la boutique et le téléphone côte à côte dans deux `iframe`, avec une barre pour piloter l'horloge (+1 / +5 / +30 min, fin du mois, réinitialiser). La boutique n'envoie que commerçant + prix. L'appli bancaire interroge `/api/etat` et `/api/bilan` chaque seconde et ne redessine que si la réponse a changé ; elle affiche les achats en pause (raisons + temps restant + « Je renonce »), les félicitations avec le curseur du pourcentage à épargner, la carte de fin de mois (tout / une partie / rien), l'objectif, le budget, l'historique et le formulaire « Mon contrat ». Aucun calcul métier en JavaScript ; tout texte venant du serveur est échappé avant affichage. L'achat suspendu garde ses raisons (`AchatSuspendu.regles`) pour que l'appli puisse les afficher ; les délais conseillés (`DELAIS_CONSEILLES`) et libellés sont fournis par l'API.
- **Temps de la démo :** l'horloge simulée n'avance que par les boutons ; le temps restant affiché se met donc à jour quand on avance l'heure (pas de compte à rebours qui défile seul), ce qui rend la démo reproductible.
- **Tableau de score (`score.py`, US4) :** strictement personnel (aucune comparaison entre utilisateurs) et uniquement positif. Le `Compte` garde la trace des achats évités (à chaque renoncement) et des versements (montant > 0). `calculer_score` renvoie : série en cours et record de mois où le budget est respecté, nombre et montant des achats évités, total épargné avec l'appli, progression, économies de chaque mois terminé, meilleur mois, écart avec le mois précédent (affiché seulement s'il est positif), et 6 badges (premier achat évité, premier mois réussi, 3 mois de suite, 100 € épargnés, objectif à 25 % et 50 %), les badges non obtenus étant affichés « à débloquer ». Les badges « objectif à 25 % / 50 % » restent acquis quand Léa démarre un nouveau projet (on ne retire jamais un badge). Onglet « Mon score » dans l'appli ; `banque.html#score` ouvre directement l'onglet.
- **État passé en paramètre :** la liste des achats suspendus est donnée à la fonction, qui renvoie la nouvelle liste. Seule l'API garde l'état en mémoire.


## 6. Lancer le projet

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest                              # 170 tests
uvicorn app.main:app --reload       # puis http://127.0.0.1:8000
```

Documentation interactive de l'API : http://127.0.0.1:8000/docs

## 7. Routes de l'API

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/etat` | Profil, plan conseillé, progression, objectif atteint et surplus, échéance dépassée, budget restant, achats en pause (avec secondes restantes) |
| GET | `/api/commercants` | Commerçants de la boutique |
| GET | `/api/score` | Tableau de score personnel + badges |
| GET | `/api/bilan` | Historique des mois terminés + mois en cours + bilan à épargner (`a_epargner`, ou `null`) |
| PUT | `/api/profil` | Modifier le contrat (limites, délais, blocage strict, objectif) |
| POST | `/api/paiement` | `{commercant, montant, canal?}` → accepté / pause / refusé |
| POST | `/api/renoncer` | `{commercant, montant}` → félicitations + somme conseillée + somme pour chaque position du curseur |
| POST | `/api/epargner` | `{montant}` → objectif mis à jour + progression |
| POST | `/api/objectif/nouveau` | `{nom, montant, echeance}` → nouvel objectif (400 si l'actuel n'est pas atteint ou date passée) |
| POST | `/api/objectif/modifier` | `{nom, montant, echeance}` → objectif ajusté, épargne conservée (400 si date passée) |
| POST | `/api/bilan/epargner` | `{annee, mois, montant}` → épargne les économies du mois terminé (0 = rien) et marque le mois comme traité |
| GET | `/api/horloge` | Heure de la démo |
| POST | `/api/horloge/avancer` | `{minutes}` → avance le temps |
| POST | `/api/horloge/mois-suivant` | Passe au 1er du mois suivant à 9 h |
| POST | `/api/reinitialiser` | Remet la démo à zéro |
