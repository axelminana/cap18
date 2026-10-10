// Fausse boutique en ligne : affiche des produits et envoie les paiements à la banque.
// La boutique ne connaît que le commerçant et le prix : la banque détecte la catégorie.

const PRODUITS = [
  { nom: "Baskets Air Street", commercant: "Sneak'Air", prix: 89, visuel: "👟" },
  { nom: "Sweat à capuche", commercant: "Mode Urbaine", prix: 45, visuel: "🧥" },
  { nom: "Pizza 4 fromages livrée", commercant: "Pizza Minute", prix: 12, visuel: "🍕" },
  { nom: "Écouteurs sans fil", commercant: "TechnoPlus", prix: 39, visuel: "🎧" },
];

function afficherProduits() {
  document.getElementById("produits").innerHTML = PRODUITS.map((produit, index) => `
    <article class="produit">
      <div class="visuel">${produit.visuel}</div>
      <h2>${echapper(produit.nom)}</h2>
      <p class="vendeur">Vendu par ${echapper(produit.commercant)}</p>
      <p class="prix">${euros(produit.prix)}</p>
      <button class="bouton-payer" data-produit="${index}">Payer ${euros(produit.prix)}</button>
    </article>
  `).join("");
}

async function payer(produit) {
  try {
    const resultat = await api("paiement", "POST", { commercant: produit.commercant, montant: produit.prix });
    afficherResultat(produit, resultat);
  } catch (erreur) {
    afficherPanneau("erreur", `<p>${echapper(erreur.message)}</p>`);
  }
}

function afficherResultat(produit, resultat) {
  if (resultat.statut === "accepte") {
    afficherPanneau("accepte", `
      <h2>✅ Commande confirmée</h2>
      <p>${echapper(produit.nom)} — ${euros(produit.prix)}. Merci pour ta commande !</p>`);
  } else if (resultat.statut === "pause") {
    afficherPanneau("pause", `
      <h2>⏳ Paiement en attente de ta banque</h2>
      <p>${echapper(resultat.message)}</p>
      <p>Consulte ton appli bancaire.</p>
      <button class="bouton-payer" data-relancer>Relancer le paiement</button>`);
  } else {
    afficherPanneau("refuse", `
      <h2>❌ Paiement refusé par ta banque</h2>
      <p>${echapper(resultat.message)}</p>`);
  }
}

function afficherPanneau(type, contenu) {
  const panneau = document.getElementById("paiement");
  panneau.className = "paiement " + type;
  panneau.innerHTML = contenu + `<button class="fermer" data-fermer aria-label="Fermer">×</button>`;
  panneau.hidden = false;
}

// Un seul écouteur pour tous les boutons de la page (délégation d'événements).
let dernierProduit = null;
document.body.addEventListener("click", (evenement) => {
  const bouton = evenement.target.closest("button");
  if (!bouton) return;
  if (bouton.dataset.produit !== undefined) {
    dernierProduit = PRODUITS[Number(bouton.dataset.produit)];
    payer(dernierProduit);
  } else if (bouton.dataset.relancer !== undefined && dernierProduit) {
    payer(dernierProduit);
  } else if (bouton.dataset.fermer !== undefined) {
    document.getElementById("paiement").hidden = true;
  }
});

afficherProduits();
