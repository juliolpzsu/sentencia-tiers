/* Índice: filtros, orden y agrupación. Los datos van en <script id="data"> (JSON). */
(() => {
  const DATA = JSON.parse(document.getElementById('data').textContent);
  const T = DATA.t, L = DATA.list, TYPES = DATA.types, TC = DATA.typeColors;
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const state = { q: '', mode: 'base', sort: 'pos', dir: 1, group: 'tier', types: new Set(), tiers: new Set(), leg: false, slow: false, stun: false, regen: false };
  try { const s = JSON.parse(localStorage.getItem('st.state') || 'null'); if (s && s.mode) { state.mode = s.mode; state.group = s.group || 'tier'; state.sort = s.sort || 'pos'; } } catch (e) {}

  const typeChips = $('#types');
  for (const t of TYPES) {
    const b = document.createElement('button'); b.className = 'chip t'; b.style.setProperty('--tc', TC[t]); b.textContent = T.types[t]; b.dataset.t = t;
    b.onclick = () => { state.types.has(t) ? state.types.delete(t) : state.types.add(t); b.classList.toggle('on'); render(); };
    typeChips.appendChild(b);
  }
  for (const b of $$('#tiers .chip')) b.onclick = () => { const t = b.dataset.tier; state.tiers.has(t) ? state.tiers.delete(t) : state.tiers.add(t); b.classList.toggle('on'); render(); };
  for (const b of $$('#flags .chip')) b.onclick = () => { state[b.dataset.f] = !state[b.dataset.f]; b.classList.toggle('on'); render(); };
  for (const b of $$('#mode button')) b.onclick = () => { state.mode = b.dataset.m; $$('#mode button').forEach(x => x.classList.toggle('on', x === b)); render(); };
  $('#q').oninput = e => { state.q = e.target.value.trim().toLowerCase(); render(); };
  $('#sort').onchange = e => { state.sort = e.target.value; render(); };
  $('#dir').onclick = () => { state.dir = -state.dir; $('#dir').textContent = state.dir > 0 ? '↓' : '↑'; render(); };
  $('#group').onchange = e => { state.group = e.target.value; render(); };
  $('#shuffle').onclick = () => { state.sort = 'rnd'; $('#sort').value = 'rnd'; render(); };
  $$('#mode button').forEach(x => x.classList.toggle('on', x.dataset.m === state.mode));
  $('#sort').value = state.sort; $('#group').value = state.group;

  const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const v = p => p[state.mode];
  const SORTS = {
    pos: p => v(p).pos, name: p => norm(p.name), dex: p => p.dex, hordes: p => p.hordes || 9999,
    T: p => -v(p).c.T, U: p => -v(p).c.U, V: p => -v(p).c.V, A: p => -v(p).c.A, D: p => -v(p).c.D, S: p => -v(p).c.S, Z: p => -v(p).c.Z,
    hp: p => -p.hp, spd: p => -p.spd, rnd: p => p._r
  };
  function filtered() {
    let out = L.filter(p => {
      if (state.q && !(norm(p.name).includes(norm(state.q)) || String(p.dex).includes(state.q) || norm(p.alt || '').includes(norm(state.q)))) return false;
      if (state.types.size && !p.types.some(t => state.types.has(t))) return false;
      if (state.tiers.size && !state.tiers.has(v(p).tier)) return false;
      if (state.leg && !p.leg) return false;
      if (state.slow && !v(p).slow) return false;
      if (state.stun && !v(p).stun) return false;
      if (state.regen && !v(p).regen) return false;
      return true;
    });
    if (state.sort === 'rnd') out.forEach(p => { p._r = Math.random(); });
    const k = SORTS[state.sort] || SORTS.pos;
    out.sort((a, b) => { const x = k(a), y = k(b); return (x < y ? -1 : x > y ? 1 : 0) * state.dir; });
    return out;
  }
  function card(p) {
    const m = v(p);
    const tools = [m.slow ? `<span class="tool slow" title="${T.slow}">${T.slowS}</span>` : '', m.stun ? `<span class="tool stun" title="${T.stun}">${T.stunS}</span>` : '', m.regen ? `<span class="tool regen" title="${T.regen}">${T.regenS}</span>` : ''].join('');
    return `<a class="card cut" href="pokemon/${p.slug}/"><span class="pos">${m.pos}</span><span class="tier ${m.tier}">${m.tier}</span>
      <span class="pic"><img class="px" loading="lazy" src="../img/p/${p.dex}.png" alt="" width="80" height="80"></span>
      <span class="name">${p.name}</span><span class="dex">Nº ${String(p.dex).padStart(3, '0')}</span>
      <span class="types">${p.types.map(t => `<span class="type" style="--tc:${TC[t]}">${T.types[t]}</span>`).join('')}</span>
      <span class="tools">${tools}</span></a>`;
  }
  function render() {
    const list = filtered();
    $('#count').textContent = T.count.replace('{n}', list.length).replace('{m}', L.length);
    const groups = new Map();
    const keyOf = p => state.group === 'tier' ? v(p).tier : state.group === 'type' ? p.types[0] : state.group === 'leg' ? (p.leg ? 'leg' : 'nor') : 'all';
    for (const p of list) { const k = keyOf(p); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(p); }
    const order = state.group === 'tier' ? ['S', 'A', 'B', 'C', 'D'] : state.group === 'type' ? TYPES : state.group === 'leg' ? ['leg', 'nor'] : ['all'];
    const title = k => state.group === 'tier' ? `${T.tier} ${k}` : state.group === 'type' ? T.types[k] : state.group === 'leg' ? (k === 'leg' ? T.legs : T.nonlegs) : T.all;
    let html = '';
    for (const k of order) {
      const g = groups.get(k); if (!g) continue;
      html += `<section class="group"><div class="group-h"><h2>${title(k)}</h2><span class="n">${g.length}</span></div><div class="grid">${g.map(card).join('')}</div></section>`;
    }
    $('#out').innerHTML = html || `<div class="empty">${T.none}</div>`;
    try { localStorage.setItem('st.state', JSON.stringify({ mode: state.mode, group: state.group, sort: state.sort })); } catch (e) {}
  }
  render();
})();
