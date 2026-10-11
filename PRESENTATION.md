# Jury technique — plan de la présentation (6 min)

Dimanche 11 octobre 2026, 11h30 · 6 min de présentation + 3 min de questions.

**Fil rouge :** on montre le parcours de Léa en direct, puis on explique comment c'est construit.
**Les attendus du jury à cocher :** démo sans crash · stack justifiée · Git · répartition des tâches · difficultés surmontées · transparence sur l'IA.

| Temps | Partie | Durée |
|---|---|---|
| 0:00 | 1. Accroche | 20 s |
| 0:20 | 2. Démo — les baskets : Léa renonce et épargne | 1 min 30 |
| 1:50 | 3. Démo — la pizza : questionnaire, Léa attend et achète | 1 min |
| 2:50 | 4. Démo — fin du mois : bilan et score | 50 s |
| 3:40 | 5. Architecture et technologies | 1 min 20 |
| 5:00 | 6. Tests, Git, équipe, difficultés, IA | 50 s |
| 5:50 | 7. Conclusion | 10 s |

> Légende : 🖱️ = ce qu'on fait à l'écran · 🎤 = ce qu'on dit · 👀 = ce qui doit s'afficher

---

## Avant de passer (5 min avant)

1. Terminal 1 : `.venv\Scripts\Activate.ps1` puis `uvicorn app.main:app` (sans `--reload` le jour J).
2. Navigateur : ouvrir **http://127.0.0.1:8000**, cliquer **« Réinitialiser la démo »**.
   👀 Vérifier l'heure en bas : **sam. 10 oct., 01:00**.
3. Terminal 2 : déjà dans le dossier `cap18`, environnement activé, `pytest` tapé mais **pas lancé**.
4. Onglets prêts : **http://127.0.0.1:8000/docs** et le **README** sur GitHub (schéma d'architecture).
5. Zoom du navigateur réglé pour que la boutique et le téléphone soient lisibles depuis le jury.

---

## 1. Accroche — 0:00 → 0:20

🎤
> « Bonjour. À 18 ans, on gagne la liberté de dépenser, et sur internet, tout s'achète en un clic, souvent la nuit, sans réfléchir.
> Cap 18 est une fonctionnalité de l'appli bancaire : chaque achat en ligne non nécessaire passe par une courte pause de réflexion, et l'argent qu'on n'a pas dépensé part vers un objectif d'épargne.
> Je vous montre le parcours de Léa, 18 ans, qui épargne pour son permis : à gauche un site marchand, à droite son appli bancaire. »

---

## 2. Démo — les baskets — 0:20 → 1:50

🖱️ Boutique : **« Payer 89 € »** sur les baskets.
👀 Boutique : « ⏳ Paiement en attente de ta banque ».

🎤
> « Il est 1 h du matin, Léa craque pour des baskets à 89 €. Au moment de payer, la banque met l'achat en pause. »

👀 Appli : carte **« ⏸ Pause de réflexion »** avec 3 raisons. Les montrer du doigt.

🎤
> « L'appli lui explique pourquoi, en langage clair :
> elle s'est fixé 30 minutes de réflexion pour les vêtements ;
> cet achat dépasse la limite de 60 € qu'elle s'est donnée ;
> et surtout, il représente 4,9 % de son objectif : le permis à 1 800 €.
> Ce sont des règles simples et explicables : il n'y a aucune IA dans le produit. »

🖱️ Appli : **« Je renonce à cet achat »**.
👀 « 🎉 Bien joué ! … Et si tu mettais 44 € de côté pour ton objectif ? »

🎤
> « Léa renonce. On la félicite, on ne la culpabilise jamais. L'appli lui propose d'épargner la moitié du montant évité, et elle peut choisir une autre part avec ce curseur. »

🖱️ Bouger le curseur à 75 % (👀 66 €), le remettre à **50 %**, cliquer **« Épargner 44 € »**.
👀 « 💰 C'est mis de côté … Tu en es à **10 %**. »

---

## 3. Démo — la pizza — 1:50 → 2:50

🖱️ Boutique : **« Payer 12 € »** sur la pizza.
👀 Appli : pause de **5 min**, raison « Ce serait ta 2e commande "livraison de repas" en 7 jours », et l'encadré **« 🤔 Pour t'aider à décider »**.

🎤
> « Plus tard, Léa commande une pizza. Pour un petit achat, au lieu d'un pourcentage, l'appli pose deux questions facultatives, adaptées à la catégorie. »

🖱️ Cliquer **« Peut-être »** sous « Ne penses-tu pas que c'est plutôt l'ennui ou la fatigue ? ».

🎤
> « Une réponse en un clic, une phrase bienveillante, et rien n'est enregistré : ses réponses ne quittent pas son téléphone. »

🖱️ Barre du bas : **« +5 min »**, puis boutique : **« Relancer le paiement »**.
👀 Boutique : « ✅ Commande confirmée ».

🎤
> « Léa reste libre. Après le délai, elle relance le paiement et il passe sans nouvelle pause, car la banque avait mémorisé l'achat : même commerçant, même montant. Ici, j'avance le temps avec l'horloge de démo pour ne pas vous faire attendre. »

---

## 4. Démo — fin du mois — 2:50 → 3:40

🖱️ Barre du bas : **« Fin du mois »**.
👀 Appli : « 📅 Ton bilan de fin de mois · octobre 2026 » — **37,79 €** dépensés, **82,21 €** économisés.

🎤
> « On passe au 1er novembre. Léa voit son bilan : 82 € économisés sur son budget en ligne. Elle choisit d'en épargner tout, une partie ou rien. »

🖱️ **« Tout épargner »**. 👀 Objectif à **15 %**.
🖱️ Onglet **« Mon score »**. 👀 1 achat évité · 126,21 € épargnés · badges « Premier achat évité », « Premier mois réussi », « 100 € épargnés ».

🎤
> « Et elle suit sa progression avec un score strictement personnel : aucune comparaison avec les autres, uniquement des encouragements. »

---

## 5. Architecture et technologies — 3:40 → 5:00

🖱️ Afficher le schéma du README sur GitHub (ou le dessiner : **front → API → Python**).

🎤
> « Comment c'est construit.
> Côté front-end : HTML, CSS et JavaScript, sans framework. Le JavaScript ne fait qu'afficher et transmettre les clics.
> Côté back-end : Python. FastAPI crée l'API, Uvicorn est le serveur qui la fait tourner, et Pydantic vérifie toutes les données qui entrent, par exemple un montant négatif est refusé. Les données fictives de Léa sont dans des fichiers JSON.
> Les deux pages ne se parlent jamais : la boutique envoie le paiement à l'API, le serveur décide et mémorise l'achat, et l'appli bancaire interroge le serveur chaque seconde. C'est le fonctionnement réel : le site demande l'autorisation à la banque, qui prévient le client, là où le 3-D Secure intervient déjà.
> Toutes les règles sont des fonctions pures en Python : même entrée, même résultat, et elles ne modifient rien. Elles reçoivent l'heure en paramètre, ce qui nous permet d'avancer le temps pendant la démo et de tout tester. »

🖱️ *(Option 10 s)* Ouvrir l'onglet **/docs**.

🎤
> « FastAPI génère aussi cette documentation de toutes nos routes.
> Nos choix : un seul langage, cinq dépendances dont deux pour les tests, et rien de caché. On a préféré un MVP simple et fiable à un projet surchargé. »

---

## 6. Tests, Git, équipe, difficultés, IA — 5:00 → 5:50

🖱️ Terminal 2 : lancer **`pytest`**. 👀 **170 passed**.

🎤
> « Nos règles sont couvertes par 170 tests automatiques, sur les vraies données de Léa et les cas du cahier des charges : les baskets à 1 h du matin, le même achat en magasin, le loyer, le repaiement avant et après le délai, le blocage strict.
> Le projet est versionné sur Git, avec un commit par étape.
> *[Répartition — à adapter :]* J'ai développé l'application ; [prénom] a travaillé sur les user stories, les maquettes et le pitch.
> Une difficulté : en répétant la démo, le bilan de fin de mois ne revenait plus après un mois sans achat. Ce mois n'apparaissait pas dans l'historique. On l'a corrigé et on a déplacé ce suivi du navigateur vers le serveur.
> Enfin, l'IA : on a codé avec Claude Code, étape par étape. Chaque étape était expliquée, testée puis validée avant d'être commitée, et les décisions métier sont les nôtres. »

---

## 7. Conclusion — 5:50 → 6:00

🎤
> « Cap 18 : dépenser, c'est facile. Choisir… ça s'apprend. Merci, nous sommes prêts pour vos questions. »

---

## Si on est en retard

À couper dans cet ordre :
1. le curseur dans la démo 1 (cliquer directement « Épargner 44 € ») ;
2. l'onglet `/docs` ;
3. l'onglet « Mon score » (le citer seulement) ;
4. la phrase sur le 3-D Secure.

## Si quelque chose plante

- Un écran ne réagit plus : **« Réinitialiser la démo »**, puis reprendre au début de la partie en cours.
- Le serveur s'arrête : relancer `uvicorn app.main:app` dans le terminal 1, tout repart du 10 octobre à 1 h.
- 🎤 Rester calme : « L'état est gardé en mémoire : au redémarrage, on repart des données de départ. C'est une limite assumée du MVP. »

---

## Questions probables (3 min) — réponses courtes

| Question | Réponse |
|---|---|
| **Pourquoi FastAPI ?** | Pour ne pas coder l'API à la main : on écrit des fonctions Python, il gère les requêtes, la validation et le JSON, et génère `/docs`. |
| **FastAPI et Uvicorn ?** | FastAPI est le framework qui crée l'API ; Uvicorn est le serveur qui l'exécute sur la machine. |
| **À quoi sert Pydantic ?** | À valider les données (types et contraintes) au chargement des JSON et à chaque requête. Pydantic **valide**, pytest **teste**. |
| **Que se passe-t-il au redémarrage ?** | L'état est en mémoire, on repart des JSON. Limite assumée ; en production, une base de données, et un seul endroit à modifier (`EtatDemo`). |
| **Comment l'historique évolue sans écrire dans le JSON ?** | Le JSON est copié en mémoire au démarrage ; les nouveaux achats s'ajoutent à cette copie, et tous les calculs l'utilisent. |
| **Fonction pure ?** | Même entrée → même résultat, et elle ne modifie rien (ex. `epargner()` renvoie un nouvel objectif). Facile à tester et à expliquer. |
| **Pourquoi `Decimal` ?** | Un `float` est approximatif (0,1 + 0,2 ≠ 0,3) ; `Decimal` garde les centimes exacts. |
| **Comment avancer le temps sans tricher ?** | Les règles reçoivent l'heure en paramètre ; seule l'API lit l'horloge de démo, fixée au 10/10/2026 à 1 h. |
| **Comment la banque reconnaît-elle l'achat relancé ?** | Elle a mémorisé commerçant, montant, date et heure de déblocage. Avant le délai : temps restant ; après : accepté ; autre montant ou plus de 24 h : nouvel achat. |
| **Comment la catégorie est-elle connue ?** | Par le commerçant, comme le code MCC de chaque vraie transaction carte. |
| **Et la sécurité / le RGPD ?** | Données fictives, entrées validées, textes échappés à l'affichage, réponses au questionnaire jamais envoyées au serveur. |
| **Quelle part pour l'IA ?** | Claude Code a écrit le code étape par étape ; chaque étape expliquée, testée, commitée ; décisions métier et tests de la démo faits par nous. |
