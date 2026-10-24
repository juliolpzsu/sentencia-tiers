// Baja los datos del Consejero de la web (se regeneran con el ranking, a diario).
// La página no puede pedirlos ella misma (otro sitio), por eso va por aquí.
const DATA_URL = 'https://juliolpzsu.github.io/sentencia-tiers/assets/advisor.json';

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (!msg || msg.sta !== 'data') return;
  fetch(DATA_URL, { cache: 'no-cache', credentials: 'omit' })
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status))))
    .then((data) => reply({ ok: true, data }))
    .catch((e) => reply({ ok: false, err: String((e && e.message) || e) }));
  return true; // respuesta asíncrona
});
