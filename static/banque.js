// Appli bancaire de Léa (vue mobile).
// Interroge le serveur chaque seconde et affiche ce qu'il renvoie. Aucun calcul métier ici.

let etat = null;             // dernière réponse de /api/etat
let bilan = null;            // dernière réponse de /api/bilan
let dernierAffichage = "";   // pour ne redessiner que si quelque chose a changé
const moisTraites = new Set(); // bilans de fin de mois déjà épargnés ou ignorés

// --- Rafraîchissement ---

async function rafraichir() {
  try {
    [etat, bilan] = await Promise.all([api("etat"), api("bilan")]);
  } catch (erreur) {
    return; // serveur momentanément injoignable : on réessaie à la seconde suivante
  }
  const empreinte = JSON.stringify([etat, bilan, [...moisTraites]]);
  if (empreinte === dernierAffichage) return;
  dernierAffichage = empreinte;

  document.getElementById("heure").textContent = dateHeure(etat.maintenant);
  afficherNotifications();
  afficherBilanPret();
  afficherObjectif();
  afficherBudget();
  afficherHistorique();
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
      <button class="bouton-principal" data-renoncer="${index}">Je renonce à cet achat</button>
    </article>
  `).join("");
}

async function renoncerA(achat) {
  const proposition = await api("renoncer", "POST", { commercant: achat.commercant, montant: achat.montant });
  const boutons = Number(proposition.somme_conseillee) > 0
    ? `<button class="bouton-principal" data-epargner="${proposition.somme_conseillee}">
         Épargner ${euros(proposition.somme_conseillee)}</button>
       <button class="bouton-secondaire" data-fermer-felicitations>Pas cette fois</button>`
    : `<button class="bouton-secondaire" data-fermer-felicitations>Fermer</button>`;
  document.getElementById("felicitations").innerHTML = `
    <article class="carte felicitations">
      <h2>🎉 Bien joué !</h2>
      <p>${echapper(proposition.message)}</p>
      <div class="boutons">${boutons}</div>
    </article>`;
  rafraichir();
}

async function epargner(montant, zone) {
  const reponse = await api("epargner", "POST", { montant: montant });
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

function dernierMoisTermine() {
  return bilan.historique.length ? bilan.historique[bilan.historique.length - 1] : null;
}

function afficherBilanPret() {
  const zone = document.getElementById("bilan-pret");
  const mois = dernierMoisTermine();
  const cle = mois ? `${mois.annee}-${mois.mois}` : null;
  if (!mois || Number(mois.economies) <= 0 || moisTraites.has(cle)) {
    if (!zone.querySelector(".felicitations")) zone.innerHTML = "";
    return;
  }
  zone.innerHTML = `
    <article class="carte bilan-pret">
      <h2>📅 Ton bilan de fin de mois · ${nomDuMois(mois.annee, mois.mois)}</h2>
      <p>Tu as dépensé ${euros(mois.depenses_en_ligne)} en ligne sur un budget de ${euros(mois.budget)} :
         tu as économisé <strong>${euros(mois.economies)}</strong>. Que veux-tu en faire ?</p>
      <div class="boutons">
        <button class="bouton-principal" data-epargner-bilan="${mois.economies}" data-mois="${cle}">
          Tout épargner (${euros(mois.economies)})</button>
      </div>
      <div class="partie">
        <input type="number" id="montant-partie" min="0" max="${mois.economies}" step="0.01"
               placeholder="Montant" aria-label="Montant à épargner">
        <button class="bouton-secondaire" data-epargner-partie data-mois="${cle}">Épargner une partie</button>
      </div>
      <button class="lien" data-rien data-mois="${cle}">Ne rien épargner ce mois-ci</button>
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
  for (const onglet of ["accueil", "bilan", "contrat"]) {
    document.getElementById(`onglet-${onglet}`).hidden = onglet !== nom;
  }
  if (nom === "contrat") afficherContrat();
}

document.body.addEventListener("click", async (evenement) => {
  const bouton = evenement.target.closest("button");
  if (!bouton || bouton.type === "submit") return;
  const d = bouton.dataset;
  try {
    if (d.onglet) ouvrirOnglet(d.onglet);
    else if (d.renoncer !== undefined) await renoncerA(etat.suspendus[Number(d.renoncer)]);
    else if (d.epargner !== undefined) await epargner(d.epargner, "felicitations");
    else if (d.fermerFelicitations !== undefined) document.getElementById("felicitations").innerHTML = "";
    else if (d.fermerZone !== undefined) document.getElementById(d.fermerZone).innerHTML = "";
    else if (d.epargnerBilan !== undefined) { moisTraites.add(d.mois); await epargner(d.epargnerBilan, "bilan-pret"); }
    else if (d.epargnerPartie !== undefined) {
      const montant = document.getElementById("montant-partie").value;
      if (montant === "" || Number(montant) < 0) return;
      moisTraites.add(d.mois);
      await epargner(montant, "bilan-pret");
    }
    else if (d.rien !== undefined) { moisTraites.add(d.mois); document.getElementById("bilan-pret").innerHTML = ""; rafraichir(); }
  } catch (erreur) {
    alert(erreur.message);
  }
});

document.getElementById("formulaire-contrat").addEventListener("submit", (evenement) => {
  evenement.preventDefault(); // pas de rechargement de page
  enregistrerContrat(evenement.target);
});

rafraichir();
setInterval(rafraichir, 1000);
