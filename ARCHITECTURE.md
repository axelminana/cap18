# Architecture et technologies — Cap 18

Document de référence pour le jury technique. Mis à jour à chaque étape du développement.

**Dernière mise à jour :** samedi 10 octobre 2026 — étape 2 (horloge simulable).

## 1. Vue d'ensemble

```
 Navigateur                          Serveur Python (FastAPI)
┌──────────────────────┐           ┌──────────────────────────────────────┐
│ boutique.html        │  fetch    │ main.py   (API JSON + fichiers       │
│ (fausse boutique)    │ ───────►  │            statiques)                │
│                      │           │    │                                 │
│ banque.html          │ ◄───────  │    ▼                                 │
│ (appli mobile Léa)   │   JSON    │ paiement.py (orchestration)          │
└──────────────────────┘           │    ├── regles.py     (déclencheurs)  │
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
| `app/regles.py` | Déclencheurs de la pause, blocage strict | à faire (étape 3) |
| `app/suspension.py` | Mémorisation des achats suspendus (déblocage, expiration 24 h) | à faire (étape 4) |
| `app/epargne.py` | Plan conseillé, somme conseillée, bilan mensuel | à faire (étape 5) |
| `app/paiement.py` | Enchaîne règles + suspension pour un paiement | à faire (étape 6) |
| `app/main.py` | API FastAPI + service du front | à faire (étape 7) |
| `static/` | `boutique.html`, `banque.html`, `style.css`, `app.js` | à faire (étape 8) |
| `tests/` | Un fichier de tests par module métier (`test_models.py` : 11 tests, `test_horloge.py` : 10 tests) | en cours |

## 4. Plan de développement

| Étape | Contenu | État |
|---|---|---|
| 0 | Environnement virtuel, dépendances, `.gitignore` | ✅ fait |
| 1 | Modèles Pydantic + données fictives | ✅ fait |
| 2 | Horloge simulable | ✅ fait |
| 3 | Moteur de déclenchement | à faire |
| 4 | Mémorisation des achats suspendus | à faire |
| 5 | Épargne : plan, somme conseillée, bilan | à faire |
| 6 | Orchestration d'un paiement | à faire |
| 7 | API FastAPI | à faire |
| 8 | Front statique + répétition de la démo | à faire |
| 9 | (facultatif) Tableau de score US4 | à faire |

## 5. Choix de conception

- **Le temps est un paramètre :** les fonctions métier reçoivent `maintenant` en argument et n'appellent jamais l'heure système. On peut donc tester « 1 h du matin » ou « 24 h plus tard » sans attendre, et avancer le temps pendant la démo.
- **Montants en `Decimal` :** un `float` stocke 0,1 de façon approchée ; `Decimal` garde les centimes exacts (9,99 € reste 9,99).
- **Catégories fermées (`Enum`) :** une catégorie inconnue est refusée dès le chargement. Les catégories obligatoires (loyer, factures) ne peuvent avoir ni limite ni délai.
- **Validation à deux niveaux :** chaque champ a ses contraintes (montant > 0, âge entre 18 et 25), puis un contrôle de cohérence du profil (une limite ne dépasse pas le budget en ligne).
- **Données de Léa :** revenus 850 €, obligatoires 490 €, budget en ligne 120 €, objectif permis 1 800 € pour octobre 2027. Septembre est volontairement un mois de dépassement (baskets à 1 h, livraisons répétées).
- **Horloge à deux modes :** réelle par défaut, ou simulée (heure fixée qui n'avance que sur demande : « +30 min », « mois suivant » au 1er à 9 h). Le temps ne peut pas reculer. Seule l'API l'utilise pour fournir `maintenant` aux fonctions métier.
- **État passé en paramètre :** la liste des achats suspendus est donnée à la fonction, qui renvoie la nouvelle liste. Seule l'API garde l'état en mémoire.

### Propositions en attente de validation par l'équipe
- Achat nocturne : 23 h – 6 h, au-delà de 20 €.
- Répétition : 3e livraison de repas sur 7 jours glissants.
- Plusieurs déclencheurs : tous affichés, délai = celui de la catégorie.

## 6. Lancer le projet

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```
