// Mundo aislado de la extensión: la página (advisor.js) no puede usar chrome.runtime,
// así que le pasa aquí la petición de datos y se la reenvía al service worker.
window.addEventListener('message', (e) => {
  const d = e.source === window && e.data;
  if (!d || d.staBridge !== 'data') return;
  const answer = (res) => window.postMessage({ staBridgeRes: 'data', id: d.id, res }, location.origin);
  try {
    chrome.runtime.sendMessage({ sta: 'data' }).then((r) => answer(r || { ok: false, err: 'sin respuesta' }), (err) => answer({ ok: false, err: String((err && err.message) || err) }));
  } catch (err) { answer({ ok: false, err: String((err && err.message) || err) }); }
});
