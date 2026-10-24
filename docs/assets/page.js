/* Ficha: pestañas Por defecto / Tienda Kecleon y, si hay partida cargada, el bloque "Tu partida". */
(() => {
  const tabs = [...document.querySelectorAll('.tabs button')], panels = [...document.querySelectorAll('.tab-panel')];
  if (tabs.length) {
    let cur = 'base';
    try { cur = localStorage.getItem('st.tab') || 'base'; } catch (e) {}
    const show = id => {
      tabs.forEach(b => { b.classList.toggle('on', b.dataset.tab === id); b.setAttribute('aria-selected', b.dataset.tab === id); });
      panels.forEach(p => p.classList.toggle('on', p.dataset.tab === id));
      try { localStorage.setItem('st.tab', id); } catch (e) {}
    };
    tabs.forEach(b => b.onclick = () => show(b.dataset.tab));
    show(panels.some(p => p.dataset.tab === cur) ? cur : 'base');
  }
  const me = document.getElementById('me');
  if (!me || !window.ST) return;
  const save = ST.load();
  if (!save) return;
  const d = me.dataset, dex = +d.dex, abils = JSON.parse(d.abils), names = JSON.parse(d.names), abs = JSON.parse(d.abs), natures = JSON.parse(d.natures), T = JSON.parse(d.t);
  const mine = save.owned.includes(dex), u = ST.upg(save, dex);
  ST.setNatures(natures.map(n => n.id));
  let { slot } = ST.score(save, dex, abils, abs, +d.sc);
  const nat = natures[ST.natureIdx(save, dex, natures)];
  const parts = [`<b>${mine ? T.owned : T.notOwned}</b>`];
  if (mine) parts.push(`${T.upgrades}: <b>${u}/${ST.UPG_MAX}</b>`);
  parts.push(`${T.ability}: <b>${names[slot] || abils[slot]}</b>${slot === 2 ? ' (' + T.hidden + ')' : ''}`);
  if (nat) parts.push(`${T.nature}: <b>${nat.n}</b>`);
  me.innerHTML = `<h3>${T.title.replace('{name}', save.name || '')}</h3><p>${parts.join(' · ')}</p><p id="me-rank" class="small muted">${T.loading}</p>`;
  me.hidden = false;
  fetch(d.scores).then(r => r.json()).then(S => {
    // puesto con su habilidad y naturaleza reales, dentro del ranking general
    const f = ST.fullScore(save, dex, abils, S);
    document.getElementById('me-rank').innerHTML = T.rank.replace('{n}', ST.rankOf(f ? f.sc : +d.sc, S, dex)).replace('{base}', d.pos);
  }).catch(() => { document.getElementById('me-rank').textContent = ''; });
})();
