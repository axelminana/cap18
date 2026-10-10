# Architecture et technologies — Cap 18

Document de référence pour le jury technique. Mis à jour à chaque étape du développement.

**Dernière mise à jour :** samedi 10 octobre 2026 — étape 0 (mise en place).

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
| `data/` | `profil.json`, `commercants.json`, `transactions.json` | à faire (étape 1) |
| `app/models.py` | Modèles Pydantic + chargement des JSON | à faire (étape 1) |
| `app/horloge.py` | Horloge réelle ou simulée (avancer le temps, changer de mois) | à faire (étape 2) |
| `app/regles.py` | Déclencheurs de la pause, blocage strict | à faire (étape 3) |
| `app/suspension.py` | Mémorisation des achats suspendus (déblocage, expiration 24 h) | à faire (étape 4) |
| `app/epargne.py` | Plan conseillé, somme conseillée, bilan mensuel | à faire (étape 5) |
| `app/paiement.py` | Enchaîne règles + suspension pour un paiement | à faire (étape 6) |
| `app/main.py` | API FastAPI + service du front | à faire (étape 7) |
| `static/` | `boutique.html`, `banque.html`, `style.css`, `app.js` | à faire (étape 8) |
| `tests/` | Un fichier de tests par module métier | à faire (étapes 1 à 7) |

## 4. Plan de développement

| Étape | Contenu | État |
|---|---|---|
| 0 | Environnement virtuel, dépendances, `.gitignore` | ✅ fait |
| 1 | Modèles Pydantic + données fictives | à faire |
| 2 | Horloge simulable | à faire |
| 3 | Moteur de déclenchement | à faire |
| 4 | Mémorisation des achats suspendus | à faire |
| 5 | Épargne : plan, somme conseillée, bilan | à faire |
| 6 | Orchestration d'un paiement | à faire |
| 7 | API FastAPI | à faire |
| 8 | Front statique + répétition de la démo | à faire |
| 9 | (facultatif) Tableau de score US4 | à faire |

## 5. Choix de conception

- **Le temps est un paramètre :** les fonctions métier reçoivent `maintenant` en argument et n'appellent jamais l'heure système. On peut donc tester « 1 h du matin » ou « 24 h plus tard » sans attendre, et avancer le temps pendant la démo.
- **État passé en paramètre :** la liste des achats suspendus est donnée à la fonction, qui renvoie la nouvelle liste. Seule l'API garde l'état en mémoire.

### Propositions en attente de validation par l'équipe
- Montants en `Decimal` plutôt qu'en `float` (évite les erreurs d'arrondi).
- Achat nocturne : 23 h – 6 h, au-delà de 20 €.
- Répétition : 3e livraison de repas sur 7 jours glissants.
- Plusieurs déclencheurs : tous affichés, délai = celui de la catégorie.
- Démo : horloge simulée avec un bouton « avancer le temps ».

## 6. Lancer le projet

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```
