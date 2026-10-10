# Architecture et technologies — Cap 18

Document de référence pour le jury technique. Mis à jour à chaque étape du développement.

**Dernière mise à jour :** samedi 10 octobre 2026 — étape 6 (orchestration d'un paiement). Toute la logique métier de la démo est écrite et testée.

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
  côté navigateur                  │    └── epargne.py    (plan, bilan)   │
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
| HTML / CSS / JS | — | Deux pages statiques | Pas de framework : rien à installer, rien à compiler |
| JSON | — | Données fictives | Lisible, modifiable à la main, suffisant pour un MVP |

**Ce qu'on n'utilise volontairement pas :** base de données (l'état tient en mémoire pour la démo), framework front (React, etc.), IA générative (tout est calculé par des règles explicables).

**Environnement :** environnement virtuel `.venv` (dépendances isolées du reste de la machine), versions figées dans `requirements.txt`.

## 3. Arborescence

| Chemin | Rôle | État |
|---|---|---|
| `requirements.txt` | Dépendances et versions | ✅ fait |
| `.gitignore` | Fichiers exclus de Git (venv, caches) | ✅ fait |
| `pytest.ini` | Configuration de pytest (les tests trouvent le paquet `app`) | ✅ fait |
| `data/` | `profil.json` (Léa), `commercants.json` (13 commerçants fictifs), `transactions.json` (août → 8 octobre 2026) | ✅ fait |
| `app/models.py` | Modèles Pydantic + chargement et validation des JSON | ✅ fait |
| `app/horloge.py` | Horloge réelle ou simulée (avancer le temps, changer de mois) | ✅ fait |
| `app/regles.py` | Pause de réflexion, raisons affichées, blocage strict | ✅ fait |
| `app/suspension.py` | Mémorisation des achats suspendus (déblocage, expiration 24 h) | ✅ fait |
| `app/epargne.py` | Plan conseillé, somme conseillée après renoncement, bilan mensuel, progression | ✅ fait |
| `app/paiement.py` | `Compte` (profil + transactions + achats suspendus), `payer`, `renoncer`, `verser_epargne` | ✅ fait |
| `app/main.py` | API FastAPI + service du front | à faire (étape 7) |
| `static/` | `boutique.html`, `banque.html`, `style.css`, `app.js` | à faire (étape 8) |
| `tests/` | Un fichier de tests par module métier (`test_models.py` : 12, `test_horloge.py` : 10, `test_regles.py` : 22, `test_suspension.py` : 12, `test_epargne.py` : 24, `test_paiement.py` : 10 — 90 tests) | en cours |

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
| 7 | API FastAPI | à faire |
| 8 | Front statique + répétition de la démo | à faire |
| 9 | (facultatif) Tableau de score US4 | à faire |

## 5. Choix de conception

- **Le temps est un paramètre :** les fonctions métier reçoivent `maintenant` en argument et n'appellent jamais l'heure système. On peut donc tester « 1 h du matin » ou « 24 h plus tard » sans attendre, et avancer le temps pendant la démo.
- **Montants en `Decimal` :** un `float` stocke 0,1 de façon approchée ; `Decimal` garde les centimes exacts (9,99 € reste 9,99).
- **Catégories fermées (`Enum`) :** une catégorie inconnue est refusée dès le chargement. Les catégories nécessaires (loyer, factures, courses) ne peuvent avoir ni limite ni délai, ne sont jamais mises en pause et ne comptent pas dans le budget en ligne.
- **Validation à deux niveaux :** chaque champ a ses contraintes (montant > 0, âge entre 18 et 25), puis un contrôle de cohérence du profil (une limite ne dépasse pas le budget en ligne).
- **Données de Léa :** revenus 850 €, obligatoires 490 €, budget en ligne 120 €, objectif permis 1 800 € pour octobre 2027. Septembre est volontairement un mois de dépassement (baskets à 1 h, livraisons répétées).
- **Horloge à deux modes :** réelle par défaut, ou simulée (heure fixée qui n'avance que sur demande : « +30 min », « mois suivant » au 1er à 9 h). Le temps ne peut pas reculer. Seule l'API l'utilise pour fournir `maintenant` aux fonctions métier.
- **Moteur de la pause (`evaluer_achat`) :** l'heure de l'achat n'a aucune importance. Ordre de décision : hors périmètre (magasin ou dépense nécessaire) → accepté ; sinon la règle « confirmation » s'applique toujours ; blocage strict + dépassement de limite ou de budget → refusé ; sinon → pause avec le délai de la catégorie (15 min par défaut).
- **Raisons supplémentaires affichées :** limite de catégorie dépassée, budget total en ligne du mois dépassé, « répétition » dès la 2e livraison de repas sur 7 jours glissants. Chaque règle a un `code` stable (pour le front et les tests) et un `message` en langage clair. La règle de nuit a été abandonnée (décision d'équipe).
- **Mémorisation (`suspension.py`) :** `verifier_tentative` renvoie l'un des 3 états : `nouvel_achat` (rien de mémorisé, montant ou commerçant différent, ou achat expiré), `toujours_suspendu` (avec les secondes restantes, pour le compte à rebours), `debloque`. `memoriser` ajoute l'achat (heure de déblocage = essai + délai) et nettoie les achats expirés ; `retirer` l'enlève une fois payé ou abandonné. Le temps est porté par l'achat (`date_heure`). Un délai de réflexion doit être inférieur à 24 h (contrôlé dans `Profil`), sinon l'achat expirerait avant d'être débloqué.
- **Épargne (`epargne.py`) :** plan conseillé = Livret A si moins de 5 ans (60 mois), PEA sinon (mention « capital non garanti ») ; versement mensuel = reste à épargner / mois restants, arrondi à l'euro supérieur (au moins 1 mois, jamais de division par zéro). Après un renoncement : félicitations + somme conseillée = 50 % du montant évité, arrondie à l'euro inférieur, plafonnée au budget en ligne restant (0 si dépassé). Bilan = budget − achats en ligne du mois (0 si négatif) ; l'historique ne contient que les mois terminés. `epargner` renvoie un nouvel objectif (tout, une partie ou rien). Le calcul « achats en ligne du mois » est partagé avec `regles.py` (`achats_en_ligne_du_mois`).
- **Orchestration (`paiement.py`) :** tout l'état de Léa tient dans un seul objet `Compte`. `payer(compte, achat)` renvoie `(nouveau_compte, résultat)` : achat déjà mémorisé et encore en délai → pause avec temps restant ; mémorisé et débloqué → accepté, enregistré et retiré des suspendus ; sinon on applique les règles → accepté (enregistré), refusé (rien n'est stocké) ou pause (mémorisé). `renoncer` retire l'achat suspendu et renvoie félicitations + somme conseillée ; `verser_epargne` met à jour l'objectif. Les tests jouent la démo de bout en bout avec l'horloge simulée.
- **État passé en paramètre :** la liste des achats suspendus est donnée à la fonction, qui renvoie la nouvelle liste. Seule l'API garde l'état en mémoire.


## 6. Lancer le projet

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```
