// Appli bancaire de Léa (vue mobile).
// Interroge le serveur chaque seconde et affiche ce qu'il renvoie. Aucun calcul métier ici.

let etat = null;             // dernière réponse de /api/etat
let bilan = null;            // dernière réponse de /api/bilan
let score = null;            // dernière réponse de /api/score
let dernierAffichage = "";   // pour ne redessiner que si quelque chose a changé
let proposition = null;      // dernière réponse de /api/renoncer (sommes du curseur d'épargne)
// Questionnaire : réponses de Léa, gardées seulement pour l'affichage (jamais envoyées au serveur).
const reponses = new Map();          // clé de l'achat -> { n° de question: n° du choix }
const questionnairesPasses = new Set(); // achats dont Léa a cliqué « Passer »

// --- Rafraîchissement ---

async function rafraichir() {
  try {
    [etat, bilan, score] = await Promise.all([api("etat"), api("bilan"), api("score")]);
  } catch (erreur) {
    return; // serveur momentanément injoignable : on réessaie à la seconde suivante
  }
  const empreinte = JSON.stringify([etat, bilan, score]);
  if (empreinte === dernierAffichage) return;
  dernierAffichage = empreinte;

  document.getElementById("heure").textContent = dateHeure(etat.maintenant);
  afficherNotifications();
  afficherBilanPret();
  afficherObjectif();
  afficherNouveauProjet();
  afficherEcheanceDepassee();
  afficherBudget();
  afficherHistorique();
  afficherScore();
}

// --- Accueil : achats en pause ---

function afficherNotifications() {
  document.getElementById("notifications").innerHTML = etat.suspendus.map((achat, index) => `
    <article class="carte notification">
      <h2>⏸ Pause de réflexion</h2>
      <p class="achat">${echapper(achat.commercant)} · <strong>${euros(achat.montant)}</strong></p>
      <ul class="raisons">
        ${achat.regles.map((regle) => `<li>${echapper(regle.message)}</li>`).join("")}
      </ul>
      ${achat.secondes_restantes > 0
        ? `<p class="compte-a-rebours">Encore <strong>${duree(achat.secondes_restantes)}</strong> avant de pouvoir valider.</p>`
        : `<p class="debloque">Délai terminé. Si tu le veux toujours, relance le paiement sur le site.</p>`}
      ${afficherQuestionnaire(achat, index)}
      <button class="bouton-principal" data-renoncer="${index}">Je renonce à cet achat</button>
    </article>
  `).join("");
}

function cleAchat(achat) {
  return `${achat.commercant}|${achat.montant}|${achat.date_essai}`;
}

// Questionnaire de réflexion : facultatif, réponses en un clic, « Passer » le ferme.
function afficherQuestionnaire(achat, index) {
  const cle = cleAchat(achat);
  if (!achat.questions.length || questionnairesPasses.has(cle)) return "";
  const choisis = reponses.get(cle) || {};
  const questions = achat.questions.map((question, q) => {
    const choix = choisis[q];
    return `
      <div class="question">
        <p>${echapper(question.texte)}</p>
        ${choix === undefined
          ? `<div class="choix">${question.choix.map((c, n) => `
               <button class="bouton-choix" data-question="${index}-${q}-${n}">${echapper(c.libelle)}</button>`).join("")}
             </div>`
          : `<p class="reponse">${echapper(question.choix[choix].reponse)}</p>`}
      </div>`;
  }).join("");
  return `
    <div class="questionnaire">
      <p class="questionnaire-titre">🤔 Pour t'aider à décider <small>(facultatif)</small></p>
      ${questions}
      <button class="lien" data-passer="${index}">Passer</button>
    </div>`;
}

async function renoncerA(achat) {
  proposition = await api("renoncer", "POST", { commercant: achat.commercant, montant: achat.montant });
  const sommeMaximale = Number(proposition.sommes_par_pourcentage[100]);
  // Curseur : choisir le pourcentage du montant évité à épargner (50 % par défaut).
  const contenu = sommeMaximale > 0
    ? `<label class="curseur-epargne">
         Part à épargner : <strong id="pourcentage-choisi"></strong>
         <input type="range" id="curseur-epargne" min="0" max="100" step="5"
                value="${proposition.pourcentage_conseille}" aria-label="Pourcentage à épargner">
       </label>
       ${sommeMaximale < Number(proposition.montant_evite)
         ? `<p class="mention">Plafonné à ${euros(sommeMaximale)} : ton budget en ligne restant ce mois-ci.</p>` : ""}
       <div class="boutons">
         <button class="bouton-principal" id="bouton-epargner-curseur" data-epargner-curseur></button>
         <button class="bouton-secondaire" data-fermer-felicitations>Pas cette fois</button>
       </div>`
    : `<div class="boutons"><button class="bouton-secondaire" data-fermer-felicitations>Fermer</button></div>`;
  document.getElementById("felicitations").innerHTML = `
    <article class="carte felicitations">
      <h2>🎉 Bien joué !</h2>
      <p>${echapper(proposition.message)}</p>
      ${contenu}
    </article>`;
  if (sommeMaximale > 0) afficherCurseur();
  rafraichir();
}

// Met à jour le texte du curseur : la somme vient du tableau calculé par le serveur.
function afficherCurseur() {
  const pourcentage = document.getElementById("curseur-epargne").value;
  const somme = proposition.sommes_par_pourcentage[pourcentage];
  document.getElementById("pourcentage-choisi").textContent = `${pourcentage} % · ${euros(somme)}`;
  const bouton = document.getElementById("bouton-epargner-curseur");
  bouton.textContent = `Épargner ${euros(somme)}`;
  bouton.disabled = Number(somme) === 0;
}

async function epargner(montant, zone, mois = null) {
  // Bilan de fin de mois : le serveur vérifie le mois et le montant, puis le marque comme traité.
  const reponse = mois
    ? await api("bilan/epargner", "POST", { annee: mois.annee, mois: mois.mois, montant: montant })
    : await api("epargner", "POST", { montant: montant });
  document.getElementById(zone).innerHTML = `
    <article class="carte felicitations">
      <h2>💰 C'est mis de côté</h2>
      <p>${euros(montant)} ajoutés à ton objectif « ${echapper(reponse.objectif.nom)} ».
         Tu en es à <strong>${reponse.progression} %</strong>.</p>
      <div class="boutons"><button class="bouton-secondaire" data-fermer-zone="${zone}">Fermer</button></div>
    </article>`;
  rafraichir();
}

// --- Accueil : bilan de fin de mois prêt ---

function afficherBilanPret() {
  const zone = document.getElementById("bilan-pret");
  const mois = bilan.a_epargner; // choisi par le serveur : dernier mois terminé, non traité, avec économies
  if (!mois) {
    if (!zone.querySelector(".felicitations")) zone.innerHTML = "";
    return;
  }
  zone.innerHTML = `
    <article class="carte bilan-pret">
      <h2>📅 Ton bilan de fin de mois · ${nomDuMois(mois.annee, mois.mois)}</h2>
      <p>Tu as dépensé ${euros(mois.depenses_en_ligne)} en ligne sur un budget de ${euros(mois.budget)} :
         tu as économisé <strong>${euros(mois.economies)}</strong>. Que veux-tu en faire ?</p>
      <div class="boutons">
        <button class="bouton-principal" data-epargner-bilan="${mois.economies}">
          Tout épargner (${euros(mois.economies)})</button>
      </div>
      <div class="partie">
        <input type="number" id="montant-partie" min="0" max="${mois.economies}" step="0.01"
               placeholder="Montant" aria-label="Montant à épargner">
        <button class="bouton-secondaire" data-epargner-partie>Épargner une partie</button>
      </div>
      <button class="lien" data-rien>Ne rien épargner ce mois-ci</button>
    </article>`;
}

// --- Accueil : objectif et budget ---

function afficherObjectif() {
  const objectif = etat.profil.objectif;
  document.getElementById("objectif").innerHTML = `
    <article class="carte">
      <h2>🎯 ${echapper(objectif.nom)}</h2>
      <div class="barre"><div class="barre-remplie" style="width: ${etat.progression}%"></div></div>
      <p class="progression"><strong>${euros(objectif.deja_epargne)}</strong> sur ${euros(objectif.montant)}
         · ${etat.progression} %</p>
      <p>${echapper(etat.plan.message)}</p>
      ${etat.plan.mentions.map((mention) => `<p class="mention">${echapper(mention)}</p>`).join("")}
    </article>`;
}

function afficherNouveauProjet() {
  const zone = document.getElementById("nouveau-projet");
  if (!etat.objectif_atteint) {
    zone.innerHTML = "";
    return;
  }
  if (zone.innerHTML !== "") return; // déjà affiché : on n'efface pas ce que Léa est en train de taper
  const surplus = Number(etat.surplus); // calculé par le serveur
  zone.innerHTML = `
    <article class="carte felicitations">
      <h2>🏁 Objectif atteint, bravo !</h2>
      <p>Prête pour ton prochain projet ?
         ${surplus > 0 ? `Les ${euros(surplus)} épargnés en plus seront reportés dessus.` : ""}</p>
      <form id="formulaire-projet">
        <label>Nom <input type="text" name="nom" required placeholder="Ex. : ma première voiture"></label>
        <label>Montant (€) <input type="number" name="montant" min="1" step="1" required></label>
        <label>Échéance <input type="date" name="echeance" required></label>
        <button type="submit" class="bouton-principal">Démarrer ce projet</button>
      </form>
      <p id="projet-message" class="message-formulaire erreur"></p>
    </article>`;
}

async function demarrerProjet(formulaire) {
  const valeur = (nom) => formulaire.elements[nom].value;
  try {
    await api("objectif/nouveau", "POST", {
      nom: valeur("nom"), montant: valeur("montant"), echeance: valeur("echeance"),
    });
    document.getElementById("nouveau-projet").innerHTML = "";
    rafraichir();
  } catch (erreur) {
    document.getElementById("projet-message").textContent = erreur.message;
  }
}

function afficherEcheanceDepassee() {
  const zone = document.getElementById("echeance-depassee");
  if (!etat.echeance_depassee) {
    zone.innerHTML = "";
    return;
  }
  if (zone.innerHTML !== "") return; // déjà affiché : on n'efface pas ce que Léa est en train de taper
  const objectif = etat.profil.objectif;
  zone.innerHTML = `
    <article class="carte notification">
      <h2>⏰ La date de ton objectif est passée</h2>
      <p>Tu as déjà épargné <strong>${euros(objectif.deja_epargne)}</strong> sur ${euros(objectif.montant)} :
         c'est un bon début ! Choisis une nouvelle date, ou ajuste ton objectif.</p>
      <form id="formulaire-echeance">
        <label>Nom <input type="text" name="nom" required value="${echapper(objectif.nom)}"></label>
        <label>Montant (€) <input type="number" name="montant" min="1" step="1" required value="${objectif.montant}"></label>
        <label>Nouvelle échéance <input type="date" name="echeance" required></label>
        <button type="submit" class="bouton-principal">Mettre à jour mon objectif</button>
      </form>
      <p id="echeance-message" class="message-formulaire erreur"></p>
    </article>`;
}

async function ajusterObjectif(formulaire) {
  const valeur = (nom) => formulaire.elements[nom].value;
  try {
    await api("objectif/modifier", "POST", {
      nom: valeur("nom"), montant: valeur("montant"), echeance: valeur("echeance"),
    });
    document.getElementById("echeance-depassee").innerHTML = "";
    rafraichir();
  } catch (erreur) {
    document.getElementById("echeance-message").textContent = erreur.message;
  }
}

function afficherBudget() {
  const restant = Number(etat.budget_restant);
  const texte = restant >= 0
    ? `Il te reste <strong>${euros(restant)}</strong> sur ${euros(etat.profil.budget_en_ligne)} ce mois-ci.`
    : `Ton budget de ${euros(etat.profil.budget_en_ligne)} est dépassé de ${euros(-restant)} ce mois-ci.`;
  document.getElementById("budget").innerHTML = `
    <article class="carte"><h2>🛒 Achats en ligne</h2><p>${texte}</p></article>`;
}

// --- Onglet Bilan ---

function afficherHistorique() {
  const enCours = bilan.mois_en_cours;
  const lignes = [...bilan.historique].reverse().map((mois) => `
    <li>
      <span>${nomDuMois(mois.annee, mois.mois)}</span>
      <span>${mois.budget_respecte
        ? `✅ ${euros(mois.economies)} économisés`
        : `Budget dépassé (${euros(mois.depenses_en_ligne)})`}</span>
    </li>`).join("");
  document.getElementById("onglet-bilan").innerHTML = `
    <article class="carte">
      <h2>Mois en cours · ${nomDuMois(enCours.annee, enCours.mois)}</h2>
      <p>${euros(enCours.depenses_en_ligne)} dépensés en ligne sur ${euros(enCours.budget)}.</p>
    </article>
    <article class="carte">
      <h2>Mois précédents</h2>
      <ul class="historique">${lignes || "<li>Pas encore de mois terminé.</li>"}</ul>
    </article>`;
}

// --- Onglet Mon score (US4) : strictement personnel, uniquement des encouragements ---

function afficherScore() {
  const s = score.score;
  const maximum = Math.max(...s.mois.map((m) => Number(m.economies)), 1);
  const barres = s.mois.map((m) => `
    <li>
      <span class="mois-nom">${nomDuMois(m.annee, m.mois)}</span>
      <span class="mois-barre"><span style="width: ${(Number(m.economies) / maximum) * 100}%"></span></span>
      <span class="mois-valeur">${m.budget_respecte ? euros(m.economies) : "dépassé"}</span>
    </li>`).join("");

  let comparaison = "";
  if (s.meilleur_mois) {
    comparaison += `<p>🏆 Meilleur mois : <strong>${nomDuMois(s.meilleur_mois.annee, s.meilleur_mois.mois)}</strong>
                    (${euros(s.meilleur_mois.economies)} économisés)</p>`;
  }
  if (s.ecart_mois_precedent !== null && Number(s.ecart_mois_precedent) > 0) {
    comparaison += `<p>📈 <strong>+${euros(s.ecart_mois_precedent)}</strong> d'économies par rapport au mois précédent.</p>`;
  }

  document.getElementById("onglet-score").innerHTML = `
    <div class="tuiles">
      <div class="tuile"><span class="valeur">🔥 ${s.serie_en_cours}</span>
        <span>mois réussi${s.serie_en_cours > 1 ? "s" : ""} de suite</span><small>record : ${s.meilleure_serie}</small></div>
      <div class="tuile"><span class="valeur">🛑 ${s.achats_evites}</span>
        <span>achat${s.achats_evites > 1 ? "s" : ""} évité${s.achats_evites > 1 ? "s" : ""}</span><small>${euros(s.montant_evite)} non dépensés</small></div>
      <div class="tuile"><span class="valeur">💰 ${euros(s.total_epargne)}</span>
        <span>épargnés avec Cap 18</span></div>
      <div class="tuile"><span class="valeur">🎯 ${s.progression} %</span>
        <span>de ton objectif</span></div>
    </div>
    <article class="carte">
      <h2>📊 Mes économies, mois par mois</h2>
      <ul class="mois-liste">${barres || "<li>Pas encore de mois terminé.</li>"}</ul>
      ${comparaison}
    </article>
    <article class="carte">
      <h2>🏅 Mes badges</h2>
      <ul class="badges">
        ${score.badges.map((b) => `
          <li class="${b.obtenu ? "obtenu" : "a-debloquer"}">
            <strong>${b.obtenu ? "🏅" : "🔒"} ${echapper(b.nom)}</strong>
            <small>${echapper(b.description)}</small>
          </li>`).join("")}
      </ul>
    </article>
    <p class="mention">Ton score est personnel : il n'est comparé à personne.</p>`;
}

// --- Onglet Mon contrat (US1) ---

function afficherContrat() {
  if (!etat) return; // données pas encore chargées
  const profil = etat.profil;
  const categories = Object.keys(etat.delais_conseilles);
  document.getElementById("formulaire-contrat").innerHTML = `
    <article class="carte">
      <h2>Mes revenus et dépenses obligatoires</h2>
      <label>Revenus mensuels (€) <input type="number" name="revenus" min="0" step="0.01" value="${profil.revenus_mensuels}"></label>
      ${profil.depenses_obligatoires.map((depense, index) => `
        <label>${echapper(depense.libelle)} (€)
          <input type="number" name="obligatoire-${index}" min="0.01" step="0.01" value="${depense.montant}"></label>`).join("")}
    </article>
    <article class="carte">
      <h2>Mes achats en ligne</h2>
      <label>Budget total par mois (€) <input type="number" name="budget" min="1" step="1" value="${profil.budget_en_ligne}"></label>
      <table class="regles-categories">
        <thead><tr><th>Catégorie</th><th>Limite (€)</th><th>Délai (min)</th></tr></thead>
        <tbody>
          ${categories.map((categorie) => `
            <tr>
              <td>${echapper(etat.libelles_categories[categorie])}</td>
              <td><input type="number" name="limite-${categorie}" min="1" step="1" value="${profil.limites[categorie] ?? ""}"></td>
              <td><input type="number" name="delai-${categorie}" min="0" step="1" value="${profil.delais_minutes[categorie] ?? ""}">
                  <small>conseillé : ${etat.delais_conseilles[categorie]}</small></td>
            </tr>`).join("")}
        </tbody>
      </table>
      <label class="case">
        <input type="checkbox" name="blocage" ${profil.blocage_strict ? "checked" : ""}>
        Blocage strict : refuser un achat qui dépasse une limite (désactivé par défaut)
      </label>
      <label class="case">
        <input type="checkbox" name="questionnaire" ${profil.questionnaire ? "checked" : ""}>
        Questions de réflexion pendant la pause (activées par défaut)
      </label>
    </article>
    <article class="carte">
      <h2>Mon objectif</h2>
      <label>Nom <input type="text" name="objectif-nom" value="${echapper(profil.objectif.nom)}"></label>
      <label>Montant (€) <input type="number" name="objectif-montant" min="1" step="1" value="${profil.objectif.montant}"></label>
      <label>Échéance <input type="date" name="objectif-echeance" value="${profil.objectif.echeance}"></label>
    </article>
    <button type="submit" class="bouton-principal">Enregistrer mon contrat</button>`;
  document.getElementById("contrat-message").textContent = "";
}

async function enregistrerContrat(formulaire) {
  const valeur = (nom) => formulaire.elements[nom].value;
  const profil = structuredClone(etat.profil);
  profil.revenus_mensuels = valeur("revenus");
  profil.depenses_obligatoires = profil.depenses_obligatoires.map(
    (depense, index) => ({ ...depense, montant: valeur(`obligatoire-${index}`) }));
  profil.budget_en_ligne = valeur("budget");
  profil.limites = {};
  profil.delais_minutes = {};
  for (const categorie of Object.keys(etat.delais_conseilles)) {
    if (valeur(`limite-${categorie}`) !== "") profil.limites[categorie] = valeur(`limite-${categorie}`);
    if (valeur(`delai-${categorie}`) !== "") profil.delais_minutes[categorie] = Number(valeur(`delai-${categorie}`));
  }
  profil.blocage_strict = formulaire.elements["blocage"].checked;
  profil.questionnaire = formulaire.elements["questionnaire"].checked;
  profil.objectif = {
    ...profil.objectif,
    nom: valeur("objectif-nom"),
    montant: valeur("objectif-montant"),
    echeance: valeur("objectif-echeance"),
  };

  const message = document.getElementById("contrat-message");
  try {
    await api("profil", "PUT", profil);
    message.className = "message-formulaire succes";
    message.textContent = "✅ Contrat enregistré.";
    rafraichir();
  } catch (erreur) {
    message.className = "message-formulaire erreur";
    message.textContent = erreur.message;
  }
}

// --- Navigation et clics (un seul écouteur, délégation d'événements) ---

function ouvrirOnglet(nom) {
  document.querySelectorAll(".onglets button").forEach((b) => b.classList.toggle("actif", b.dataset.onglet === nom));
  for (const onglet of ["accueil", "bilan", "score", "contrat"]) {
    document.getElementById(`onglet-${onglet}`).hidden = onglet !== nom;
  }
  if (nom === "contrat") afficherContrat();
}

document.body.addEventListener("click", async (evenement) => {
  const bouton = evenement.target.closest("button");
  // Les boutons des formulaires (« Mon contrat », nouveau projet, échéance) sont gérés par « submit » plus bas.
  if (!bouton || bouton.closest("form")) return;
  const d = bouton.dataset;
  try {
    if (d.onglet) ouvrirOnglet(d.onglet);
    else if (d.question !== undefined) {
      const [index, q, n] = d.question.split("-").map(Number);
      const cle = cleAchat(etat.suspendus[index]);
      reponses.set(cle, { ...reponses.get(cle), [q]: n });
      afficherNotifications();
    }
    else if (d.passer !== undefined) {
      questionnairesPasses.add(cleAchat(etat.suspendus[Number(d.passer)]));
      afficherNotifications();
    }
    else if (d.renoncer !== undefined) await renoncerA(etat.suspendus[Number(d.renoncer)]);
    else if (d.epargnerCurseur !== undefined) {
      const pourcentage = document.getElementById("curseur-epargne").value;
      await epargner(proposition.sommes_par_pourcentage[pourcentage], "felicitations");
    }
    else if (d.fermerFelicitations !== undefined) document.getElementById("felicitations").innerHTML = "";
    else if (d.fermerZone !== undefined) document.getElementById(d.fermerZone).innerHTML = "";
    else if (d.epargnerBilan !== undefined) await epargner(d.epargnerBilan, "bilan-pret", bilan.a_epargner);
    else if (d.epargnerPartie !== undefined) {
      const montant = document.getElementById("montant-partie").value;
      if (montant === "") return;
      await epargner(montant, "bilan-pret", bilan.a_epargner);
    }
    else if (d.rien !== undefined) {
      const mois = bilan.a_epargner;
      await api("bilan/epargner", "POST", { annee: mois.annee, mois: mois.mois, montant: 0 });
      document.getElementById("bilan-pret").innerHTML = "";
      rafraichir();
    }
  } catch (erreur) {
    alert(erreur.message);
  }
});

// Le curseur d'épargne déclenche « input » à chaque déplacement.
document.body.addEventListener("input", (evenement) => {
  if (evenement.target.id === "curseur-epargne") afficherCurseur();
});

document.body.addEventListener("submit", (evenement) => {
  evenement.preventDefault(); // pas de rechargement de page
  if (evenement.target.id === "formulaire-contrat") enregistrerContrat(evenement.target);
  if (evenement.target.id === "formulaire-projet") demarrerProjet(evenement.target);
  if (evenement.target.id === "formulaire-echeance") ajusterObjectif(evenement.target);
});

// On peut ouvrir directement un onglet par l'adresse, ex. banque.html#score
const ongletDemande = location.hash.slice(1);
if (["bilan", "score"].includes(ongletDemande)) ouvrirOnglet(ongletDemande);

rafraichir();
setInterval(rafraichir, 1000);
