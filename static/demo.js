// Barre de contrôle de la démo : affiche l'heure simulée et la fait avancer.

async function afficherHeure() {
  try {
    const horloge = await api("horloge");
    document.getElementById("heure-demo").textContent = dateHeure(horloge.maintenant);
  } catch (erreur) {
    document.getElementById("heure-demo").textContent = "serveur injoignable";
  }
}

document.querySelectorAll("[data-minutes]").forEach((bouton) => {
  bouton.addEventListener("click", async () => {
    await api("horloge/avancer", "POST", { minutes: Number(bouton.dataset.minutes) });
    afficherHeure();
  });
});

document.getElementById("mois-suivant").addEventListener("click", async () => {
  await api("horloge/mois-suivant", "POST");
  afficherHeure();
});

document.getElementById("reinitialiser").addEventListener("click", async () => {
  await api("reinitialiser", "POST");
  // On recharge les deux écrans pour repartir d'une page propre.
  document.getElementById("cadre-boutique").contentWindow.location.reload();
  document.getElementById("cadre-banque").contentWindow.location.reload();
  afficherHeure();
});

afficherHeure();
setInterval(afficherHeure, 1000);
