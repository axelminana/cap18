# CLAUDE.md — Projet « Cap 18 » (Hackathon Sopra Steria 2026)

Ce fichier donne à Claude Code tout le contexte du projet. Lis-le en entier avant toute action.

## 0. État d'avancement (à mettre à jour au fil du hackathon)

- **Pivot du samedi midi :** on abandonne la partie « coût des vœux / changement de ville / aides à l'installation ». Le projet se concentre sur le **contrat personnel anti-achats impulsifs, au service de l'épargne**.
- **Décisions du samedi 14h30 :** délais de réflexion par catégorie (choisis par l'utilisateur, avec valeurs conseillées), mémorisation de l'achat suspendu, limites par catégorie + budget total en ligne, détection automatique des catégories évidentes, objectif d'épargne avec horizon et plan conseillé, option de blocage strict (désactivée par défaut).
- **Équipe code :** Axel code, avec l'aide de Claude Code. Le code doit rester compréhensible et explicable par Axel.
- Fait : concept, pitch d'une minute (voir §9), environnement installé, dépôt Git `cap18`.
- Samedi 10/10 après-midi : étapes 0 à 8 du plan terminées (voir `ARCHITECTURE.md`) : modèles, horloge, règles, mémorisation, épargne, orchestration, API FastAPI, front (boutique + appli bancaire + barre de démo). 113 tests pytest.
- Prochaine étape : Axel lance le serveur et répète la démo ; US4 (tableau de score) en option.

## 1. Contexte de l'événement

- Hackathon Sopra Steria 2026, thème « Banque de demain » : imaginer une banque plus utile, plus sûre et plus inclusive.
- Le PIC, Clermont-Ferrand, samedi 10 et dimanche 11 octobre 2026.
- Défi officiel : transformer un besoin réel en une expérience simple, explicable et démontrable, **avec des données fictives** et l'humain au centre.
- Objectif de notre équipe : **fidéliser une nouvelle clientèle jeune (18-25 ans)** en l'aidant à économiser et à épargner.

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

## 2. Le concept : Cap 18, dépenser c'est facile, choisir ça s'apprend

**Problème :** à 18-25 ans, on gagne sa liberté de dépenser, mais les achats en ligne se font en un clic, souvent la nuit, sans réfléchir. Résultat : découvert, et les projets (permis, voiture…) reculent.

**Solution :** une fonctionnalité intégrée à l'application bancaire (exemple de contexte : appli du Crédit Agricole).
1. **Mon contrat :** le jeune renseigne ses revenus et dépenses obligatoires, fixe un **budget total pour ses achats en ligne** et des **limites par catégorie**, et règle ses **délais de réflexion par catégorie** (valeurs conseillées proposées).
2. **Mon objectif :** il saisit un objectif (ex. : une voiture dans 2 ans, 3 000 €). Selon l'horizon (court ou long terme), l'appli conseille un plan d'épargne adapté et un montant mensuel.
3. **La pause de réflexion :** **tout achat en ligne non nécessaire**, à n'importe quelle heure, est suspendu pendant le délai de sa catégorie ; l'appli envoie une notification qui indique le délai et, le cas échéant, les règles dépassées (limite, budget, répétition).
4. **La récompense :** s'il renonce, l'appli le félicite et lui propose de verser une somme conseillée vers son objectif.
5. **Le bilan du mois :** il voit ce qu'il a économisé, choisit d'épargner ou non, et suit sa progression (tableau de score personnel).
6. **Option blocage strict (désactivée par défaut) :** si activée, un achat qui dépasse une limite est refusé, pas seulement suspendu. Par défaut, l'utilisateur peut toujours dépasser s'il le veut vraiment, après le délai.

**Périmètre :** uniquement les **paiements en ligne**, jamais les paiements en magasin. Les dépenses obligatoires ne sont jamais concernées.

**Arguments de faisabilité :**
- Les paiements en ligne par carte passent déjà par une validation dans l'appli bancaire (authentification forte, 3-D Secure) : la pause s'insère là où la banque intervient déjà.
- Chaque transaction carte porte un code de catégorie du commerçant (MCC) : il permet de reconnaître automatiquement les catégories évidentes.

**Persona :** Léa, 18 ans, premier appartement, premier job étudiant. Objectif : son permis de conduire (1 800 €, d'ici octobre 2027).

**Proposition de valeur pour la banque :** engagement quotidien d'un jeune client, image de banque bienveillante, et épargne qui reste dans la banque, sur un produit adapté à l'objectif.

## 3. User stories du MVP

**US1 — Créer mon contrat et mon objectif**
En tant que jeune client, je souhaite fixer mon budget d'achats en ligne, mes limites par catégorie, mes délais de réflexion et mon objectif d'épargne, afin de savoir ce que je peux dépenser et pour quoi j'épargne.
- Dépenses obligatoires et revenus pré-remplis (détectés ou fictifs pour la démo), modifiables.
- Délais par catégorie : valeur conseillée affichée, modifiable.
- Objectif : nom, montant, échéance → horizon court ou long terme → plan conseillé + versement mensuel suggéré.
- Option « blocage strict » : désactivée par défaut, activable.

**US2 — Pause de réflexion sur un achat en ligne**
En tant que jeune client, je souhaite qu'un achat en ligne impulsif soit suspendu pendant le délai que j'ai choisi, afin de prendre le temps de décider.
- Notification qui explique la règle déclenchée, en langage clair.
- Achat mémorisé par la banque (voir §5). Après le délai, s'il relance le paiement du même montant chez le même commerçant, il passe sans nouvelle pause.
- S'il renonce : félicitations + proposition de versement vers l'objectif, avec une somme conseillée.
- Si blocage strict activé et limite dépassée : refus, avec explication.

**US3 — Bilan de fin de mois**
En tant que jeune client, je souhaite voir chaque fin de mois ce que j'ai économisé et choisir de l'épargner, afin de me rapprocher de mon objectif.
- Économies du mois = budget en ligne − dépenses en ligne réelles (si positif).
- Choix : épargner tout, une partie, ou rien.
- Historique mois par mois + progression vers l'objectif.

**US4 (facultative) — Tableau de score personnel**
Séries de mois réussis, achats évités, montant total épargné, badges. **Strictement personnel : pas de comparaison entre amis.**

**Démo cible :** deux écrans côte à côte. À gauche, une fausse boutique en ligne (ex. baskets à 89 €, 1h du matin). À droite, l'appli bancaire de Léa en format mobile. « Payer » → notification de pause avec la raison → (variante A) elle renonce → félicitations et épargne ; (variante B) elle attend la fin du délai, repaie et l'achat passe. Puis on avance au bilan de fin de mois et à la progression vers l'objectif.

## 4. Données (toutes fictives)

- `profil.json` : Léa (revenus, dépenses obligatoires, budget total en ligne, limites par catégorie, délais par catégorie, option blocage strict, objectif).
- `commercants.json` : commerçants fictifs ou génériques avec leur catégorie (table de correspondance pour la détection automatique, inspirée des codes MCC).
- `transactions.json` : plusieurs mois de transactions fictives, avec canal (`en_ligne` / `magasin`), commerçant, catégorie, montant, date et heure.
- `achats_suspendus` : stockage des achats mémorisés (en mémoire ou en base).

## 5. Règles métier

### Catégories et délais conseillés (valeurs par défaut, modifiables par l'utilisateur)
| Catégorie | Délai conseillé | Raison |
|---|---|---|
| Livraison de repas | 2 à 5 min | Achat urgent, délai court |
| Vêtements / chaussures | 30 min | Moins urgent |
| Électronique | 60 min | Achat coûteux |
| Jeux vidéo | 30 min | |
| Abonnements | 10 min | |
| Autres (catégorie sans délai défini) | 15 min | Valeur par défaut |
Pour la démo, le temps est **avancé** avec l'horloge simulée (bouton « +30 min »), sans modifier les délais.

### Pause de réflexion (uniquement canal = en ligne)
**Tout achat en ligne non nécessaire est mis en pause, quelle que soit l'heure** (règle « confirmation ») : il faut confirmer après le délai de la catégorie. L'heure de l'achat n'a aucune importance. Sont nécessaires, donc jamais en pause et hors budget en ligne : loyer, factures, courses.

Raisons supplémentaires affichées dans le message :
- l'achat ferait dépasser la limite de sa catégorie ou le budget total en ligne du mois ;
- livraison de repas : à partir de la **2e commande sur 7 jours glissants**, le message est renforcé (règle « répétition »).
Chaque règle est formulée en langage clair ; toutes sont affichées ; le délai est celui de la catégorie. Le blocage strict ne refuse que les dépassements de limite ou de budget.
À chaque pause, le message de confirmation indique le délai avant validation. **Si l'utilisateur annule, l'appli l'incite à verser une somme conseillée sur son épargne.**

### Mémorisation de l'achat suspendu
Les sites marchands abandonnent le paiement s'il n'est pas validé rapidement. Donc :
1. Premier essai : la banque refuse le paiement et **mémorise** l'achat (commerçant, montant exact, date de l'essai, heure de déblocage = essai + délai de la catégorie).
2. Nouvel essai **avant** l'heure de déblocage : toujours suspendu, on affiche le temps restant.
3. Nouvel essai **après** l'heure de déblocage, même commerçant et même montant : accepté sans nouvelle pause.
4. Montant différent ou autre commerçant : traité comme un nouvel achat.
5. Un achat mémorisé **expire au bout de 24 h**. Passé ce délai, un nouvel essai est traité comme un nouvel achat.

### Blocage strict (option)
- Désactivé par défaut. Si activé : un achat qui dépasse une limite est refusé, sans possibilité de passer après le délai.
- Ne s'applique jamais aux dépenses obligatoires.
- La désactivation prend **effet immédiatement**.

### Objectif et plan d'épargne conseillé
- Horizon = échéance − aujourd'hui.
- **Moins de 5 ans = court terme** → incitation à alimenter un **Livret A**.
- **5 ans ou plus = long terme** → incitation à alimenter un **PEA** (plan d'épargne en actions).
- Versement mensuel suggéré = (montant de l'objectif − déjà épargné) / nombre de mois restants.
- Le produit est toujours présenté comme une **suggestion**, pas un conseil en investissement. Pour le PEA, mentionner que le capital n'est pas garanti.

### Somme conseillée après un renoncement
Règle simple et explicable (ex. 50 % du montant évité, arrondi), sans dépasser le budget en ligne restant.

## 6. Stack et principes techniques

- **Langage : Python** (décision d'équipe). Toute la logique métier est en Python.
- **Stack validée :**
  - **Données** : fichiers JSON.
  - **Modèles et validation** : **Pydantic** (équivalent Python de Zod) ; les JSON sont validés au chargement, avec des erreurs claires.
  - **Logique métier** : modules Python séparés, fonctions pures, testées avec **pytest**.
  - **API** : **FastAPI**, qui expose la logique en JSON.
  - **Front statique** : HTML, CSS et un peu de JavaScript (aucune logique métier côté front), servi par FastAPI. Deux pages : la fausse boutique en ligne et la vue mobile de l'appli bancaire. Le JS sert uniquement à appeler l'API, afficher les notifications et le compte à rebours.
  - Pas de site 100 % statique : l'achat mémorisé et les délais exigent un serveur qui garde l'état.
- **Arborescence indicative :**
  ```
  cap18/
  ├── CLAUDE.md
  ├── requirements.txt
  ├── data/            # profil.json, commercants.json, transactions.json
  ├── app/
  │   ├── models.py    # modèles Pydantic
  │   ├── regles.py    # déclencheurs de la pause, blocage strict
  │   ├── suspension.py# mémorisation des achats suspendus
  │   ├── epargne.py   # somme conseillée, plan d'épargne, bilan mensuel
  │   ├── horloge.py   # horloge simulable pour la démo
  │   └── main.py      # API FastAPI + service du front statique
  ├── static/          # boutique.html, banque.html, style.css, app.js
  └── tests/           # tests pytest des modules métier
  ```
- **Pas d'IA générative dans le produit** : tout est calculé par des règles explicables.
- Le moteur de déclenchement, la mémorisation des achats, la somme conseillée, le plan d'épargne et le bilan mensuel doivent être des **fonctions pures, testées** sur des cas concrets :
  - baskets 89 € à 1h du matin en ligne → pause de 30 min ;
  - même achat en magasin → pas de pause ;
  - loyer → jamais de pause ;
  - repaiement du même montant après le délai → accepté ;
  - repaiement avant la fin du délai → toujours suspendu ;
  - blocage strict activé et limite dépassée → refus.
- Le temps doit pouvoir être **simulé** (horloge de démo, changement de mois).
- Dépendances minimales. Chaque ajout de librairie doit être justifié.
- Git dès le début, commits fréquents et lisibles.

## 7. Comment travailler avec moi (consignes pour Claude Code)

- Avancer **par petites étapes**. Avant chaque étape, annoncer ce qui va être fait ; après, expliquer brièvement le code produit pour qu'Axel puisse le défendre devant le jury.
- Préférer du code simple et lisible à du code astucieux.
- Ne pas ajouter de fonctionnalités hors du périmètre ci-dessus sans demander.
- Priorité absolue : une démo qui tourne sans crash. En cas de manque de temps, couper dans cet ordre : US4, option blocage strict, détection automatique (garder du pré-rempli), raisons secondaires (garder « confirmation » et « dépassement de limite »).
- Répondre en français.
- Tenir `ARCHITECTURE.md` à jour à la fin de chaque étape (technologies, arborescence, état d'avancement, choix de conception).
- **Routine de travail, à chaque étape du plan :**
  1. une seule étape à la fois ;
  2. coder l'étape, puis expliquer le code à Axel ;
  3. lancer les tests (`pytest`) ;
  4. si tout passe : mettre à jour `ARCHITECTURE.md` et faire un commit avec un message clair ;
  5. toutes les deux ou trois étapes réussies : `git push` vers GitHub (`origin`, branche `main`).

## 8. Vigilance (à mentionner au jury)

- Autonomie : c'est le jeune qui fixe ses règles et ses délais ; par défaut il peut toujours acheter après le délai ; le blocage strict est un choix volontaire.
- Ton : jamais moralisateur ni culpabilisant ; on félicite, on ne punit pas.
- RGPD : données de transactions déjà détenues par la banque, utilisées uniquement pour le service choisi par le client.
- Conseil encadré : le plan d'épargne est une suggestion, pas un conseil en investissement.
- Limite assumée : seuls les achats en ligne sont concernés.

## 9. Pitch d'une minute (samedi 15h30)

« Léa, 18 ans. Premier appart. Premier job étudiant. Et un rêve tout simple : se payer son permis.
1 h du matin. Elle scrolle. Des baskets à 89 €. Un clic.
Le lendemain ? Un Uber Eats. Puis un autre.
Le 20 du mois, Léa est à découvert. Et son permis, lui, attendra encore.
Léa n'a rien fait de grave. Elle a juste tout acheté… sans y penser.
À 18 ans, on nous donne la liberté de dépenser. Mais personne ne nous apprend à choisir.
Notre solution : Cap 18, directement dans l'appli bancaire.
Léa y entre ses dépenses obligatoires et fixe sa propre limite.
À 1 h du matin, avant de valider ses baskets, l'appli lui laisse quelques minutes de réflexion pour confirmer ou non son achat.
Si elle renonce, l'appli la félicite et lui propose de mettre une partie du budget prévu en épargne, avec une somme conseillée.
Et chaque fin de mois, elle voit ce qu'elle a épargné… et à quel point elle se rapproche de son permis.
Cap 18. Dépenser, c'est facile. Choisir… ça s'apprend. »

## 10. Questions ouvertes (à trancher)

- (aucune pour l'instant)

Tranché le samedi 14h45-14h50 : seuil court/long terme à 5 ans (Livret A / PEA), validité d'un achat mémorisé 24 h, désactivation du blocage strict immédiate, code en Python, stack JSON + Pydantic + FastAPI + front statique.

Tranché le samedi après-midi : persona Léa, 18 ans ; objectif de démo = permis 1 800 € pour octobre 2027 ; délais par catégorie (§5) ; montants en `Decimal` ; pause sur tout achat en ligne non nécessaire quelle que soit l'heure (règle de nuit abandonnée), courses considérées comme nécessaires ; message renforcé dès la 2e livraison de repas sur 7 jours ; démo avec horloge simulée.
