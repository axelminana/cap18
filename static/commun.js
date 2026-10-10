// Fonctions partagées par les pages : appel de l'API et mise en forme.
// Aucune règle métier ici : tous les calculs sont faits par le serveur Python.

async function api(chemin, methode = "GET", corps = null) {
  const options = { method: methode, headers: { "Content-Type": "application/json" } };
  if (corps !== null) options.body = JSON.stringify(corps);
  const reponse = await fetch("/api/" + chemin, options);
  const donnees = await reponse.json();
  if (!reponse.ok) throw new Error(messageErreur(donnees));
  return donnees;
}

function messageErreur(donnees) {
  // FastAPI renvoie un texte (erreurs 400 / 404) ou une liste d'erreurs de validation (422).
  if (typeof donnees.detail === "string") return donnees.detail;
  if (Array.isArray(donnees.detail)) {
    return donnees.detail.map((e) => e.msg.replace("Value error, ", "")).join(" ");
  }
  return "Erreur inattendue.";
}

// Les montants arrivent sous forme de texte ("89", "94.21") : on les convertit pour l'affichage.
function euros(montant) {
  const nombre = Number(montant);
  return nombre.toLocaleString("fr-FR", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: Number.isInteger(nombre) ? 0 : 2,
  });
}

function dateHeure(iso) {
  return new Date(iso).toLocaleString("fr-FR", {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

function nomDuMois(annee, mois) {
  return new Date(annee, mois - 1, 1).toLocaleString("fr-FR", { month: "long", year: "numeric" });
}

function duree(secondes) {
  const minutes = Math.floor(secondes / 60);
  const reste = secondes % 60;
  return reste ? `${minutes} min ${String(reste).padStart(2, "0")} s` : `${minutes} min`;
}

// Protège l'affichage : un texte venant du serveur n'est jamais interprété comme du HTML.
function echapper(texte) {
  const div = document.createElement("div");
  div.textContent = texte;
  return div.innerHTML;
}
