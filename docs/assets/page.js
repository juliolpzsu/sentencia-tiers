/* Ficha: pestañas Por defecto / Tienda Kecleon (recuerda la última elegida). */
(() => {
  const tabs = [...document.querySelectorAll('.tabs button')], panels = [...document.querySelectorAll('.tab-panel')];
  if (!tabs.length) return;
  let cur = 'base';
  try { cur = localStorage.getItem('st.tab') || 'base'; } catch (e) {}
  function show(id) {
    tabs.forEach(b => b.classList.toggle('on', b.dataset.tab === id));
    panels.forEach(p => p.classList.toggle('on', p.dataset.tab === id));
    try { localStorage.setItem('st.tab', id); } catch (e) {}
  }
  tabs.forEach(b => b.onclick = () => show(b.dataset.tab));
  show(panels.some(p => p.dataset.tab === cur) ? cur : 'base');
})();
