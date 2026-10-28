/* Índice: filtros, orden y agrupación. Estado en la URL (compartible). Partida opcional del jugador (ver save.js). */
(() => {
  const DATA = JSON.parse(document.getElementById('data').textContent);
  const T = DATA.t, L = DATA.list, TYPES = DATA.types, TC = DATA.typeColors, AN = DATA.an, NAT = DATA.natures, MV = DATA.mv;
  const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
  const state = { q: '', mode: 'base', sort: 'pos', dir: 1, group: 'tier', types: new Set(), tiers: new Set(), leg: false, slow: false, stun: false, regen: false, mine: false, tmday: false };
  let save = ST.load();
  const byDex = new Map(L.map(p => [p.dex, p]));

  // ---- estado ⇄ URL ----
  function readUrl() {
    const u = new URLSearchParams(location.search);
    if (!u.toString()) { try { const s = JSON.parse(localStorage.getItem('st.state') || 'null'); if (s && s.mode) Object.assign(state, { mode: s.mode, group: s.group || 'tier', sort: s.sort || 'pos' }); } catch (e) {} return; }
    if (u.get('q')) state.q = u.get('q');
    if (u.get('m') === 'shop') state.mode = 'shop';
    if (u.get('s')) state.sort = u.get('s');
    if (u.get('d') === 'desc') state.dir = -1;
    if (u.get('g')) state.group = u.get('g');
    (u.get('t') || '').split(',').filter(Boolean).forEach(t => state.types.add(t));
    (u.get('tier') || '').split(',').filter(Boolean).forEach(t => state.tiers.add(t));
    (u.get('f') || '').split(',').filter(Boolean).forEach(f => { if (f in state) state[f] = true; });
  }
  function writeUrl() {
    const u = new URLSearchParams();
    if (state.q) u.set('q', state.q);
    if (state.mode !== 'base') u.set('m', state.mode);
    if (state.sort !== 'pos') u.set('s', state.sort);
    if (state.dir < 0) u.set('d', 'desc');
    if (state.group !== 'tier') u.set('g', state.group);
    if (state.types.size) u.set('t', [...state.types].join(','));
    if (state.tiers.size) u.set('tier', [...state.tiers].join(','));
    const f = ['leg', 'slow', 'stun', 'regen', 'mine', 'tmday'].filter(k => state[k]); if (f.length) u.set('f', f.join(','));
    const qs = u.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
    try { localStorage.setItem('st.state', JSON.stringify({ mode: state.mode, group: state.group, sort: state.sort })); } catch (e) {}
  }
  readUrl();

  // ---- controles ----
  const typeChips = $('#types');
  for (const t of TYPES) {
    const b = document.createElement('button'); b.className = 'chip t' + (state.types.has(t) ? ' on' : ''); b.type = 'button'; b.style.setProperty('--tc', TC[t]); b.textContent = T.types[t]; b.dataset.t = t;
    b.setAttribute('aria-pressed', state.types.has(t));
    b.onclick = () => { state.types.has(t) ? state.types.delete(t) : state.types.add(t); toggle(b, state.types.has(t)); render(); };
    typeChips.appendChild(b);
  }
  function toggle(b, on) { b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); }
  for (const b of $$('#tiers .chip')) { toggle(b, state.tiers.has(b.dataset.tier)); b.onclick = () => { const t = b.dataset.tier; state.tiers.has(t) ? state.tiers.delete(t) : state.tiers.add(t); toggle(b, state.tiers.has(t)); render(); }; }
  for (const b of $$('#flags .chip')) { toggle(b, !!state[b.dataset.f]); b.onclick = () => { state[b.dataset.f] = !state[b.dataset.f]; toggle(b, state[b.dataset.f]); render(); }; }
  for (const b of $$('#mode button')) b.onclick = () => { state.mode = b.dataset.m; $$('#mode button').forEach(x => { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', x === b); }); render(); };
  $('#q').value = state.q;
  $('#q').oninput = e => { state.q = e.target.value.trim(); render(); };
  $('#sort').onchange = e => { state.sort = e.target.value; render(); };
  $('#dir').onclick = () => { state.dir = -state.dir; $('#dir').textContent = state.dir > 0 ? '↓' : '↑'; render(); };
  $('#group').onchange = e => { state.group = e.target.value; render(); };
  $('#more').onclick = () => { const c = $('.controls'), o = c.classList.toggle('open'); $('#more').setAttribute('aria-expanded', o); };
  $('#shuffle').onclick = () => { state.sort = 'rnd'; $('#sort').value = 'rnd'; render(); };
  $$('#mode button').forEach(x => { x.classList.toggle('on', x.dataset.m === state.mode); x.setAttribute('aria-pressed', x.dataset.m === state.mode); });
  $('#sort').value = state.sort; $('#group').value = state.group; $('#dir').textContent = state.dir > 0 ? '↓' : '↑';

  // ---- partida del jugador ----
  const dlg = $('#me-dlg');
  function meStatus() {
    const st = $('#me-status'), chip = $('#flag-mine');
    if (save) { st.textContent = T.meLoaded.replace('{name}', save.name || '?').replace('{n}', save.owned.length); chip.hidden = false; $('#me-btn').classList.add('on'); }
    else { st.textContent = ''; chip.hidden = true; state.mine = false; toggle(chip, false); $('#me-btn').classList.remove('on'); }
  }
  $('#me-btn').onclick = () => dlg.showModal();
  $('#me-close').onclick = () => dlg.close();
  $('#me-copy').onclick = async () => { try { await navigator.clipboard.writeText(ST.SNIPPET); $('#me-copy').textContent = T.copied; } catch (e) {} };
  $('#me-load').onclick = () => {
    try { save = ST.parse($('#me-text').value); ST.store(save); $('#me-text').value = ''; $('#me-err').textContent = ''; meStatus(); render(); dlg.close(); }
    catch (e) { $('#me-err').textContent = T.meError; }
  };
  $('#me-clear').onclick = () => { save = null; ST.clear(); meStatus(); render(); dlg.close(); };
  meStatus();

  // ---- MT a la venta hoy ----
  let today = null;
  function computeToday() {
    const learn = dex => { const p = byDex.get(dex); if (!p) return []; const taught = (save && save.ptm && save.ptm[dex]) || [];
      return DATA.tmAll.filter(id => p.tm.includes(DATA.tmIdx[id]) && !taught.includes(id)); };
    today = ST.dailyTms(DATA.tmAll, save && save.partner, learn);
    today.idx = new Set(today.list.map(id => DATA.tmIdx[id]));
    const use = id => L.filter(p => p.st.includes(DATA.tmIdx[id])).length;
    const d = today.date, date = d.slice(6) + '/' + d.slice(4, 6);
    $('#tmday').innerHTML = `<span class="lbl">${T.tmToday.replace('{d}', date)}</span>` + today.list.map(id => {
      const n = use(id), nm = DATA.tmIdx[id] >= 0 ? MV[DATA.tmIdx[id]] : id;
      return `<span class="tm${n ? ' hot' : ''}" title="${T.tmFor.replace('{n}', n)}">${nm} <b>${DATA.tmPrice[id]}</b>${n ? ` <i>${n}</i>` : ''}</span>`;
    }).join('') + (save && save.partner ? '' : `<span class="note8" title="${T.tm8}">*</span>`);
  }
  computeToday();
  $('#me-load').addEventListener('click', () => { computeToday(); render(); }); $('#me-clear').addEventListener('click', () => { computeToday(); render(); });

  // ---- orden y filtros ----
  const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const v = p => p[state.mode];
  ST.setNatures(NAT.map(n => n.id));
  let SC = null;
  function loadScores() { if (!save || SC) return; fetch('../assets/scores.json').then(r => r.json()).then(S => { SC = S; render(); }).catch(() => {}); }
  let youRank = null;
  function computeYouRank() {
    if (!save || !SC) { youRank = null; return; }
    youRank = new Map(L.map(p => { const f = ST.fullScore(save, p.dex, p.ab, SC); return [p.dex, f ? ST.rankOf(f.sc, SC, p.dex) : p.base.pos]; }));
  }
  const SORTS = {
    pos: p => v(p).pos, name: p => norm(p.name), dex: p => p.dex, hordes: p => p.hordes || 9999, you: p => youRank ? youRank.get(p.dex) : v(p).pos,
    T: p => -v(p).c.T, U: p => -v(p).c.U, A: p => -v(p).c.A, D: p => -v(p).c.D, S: p => -v(p).c.S, Z: p => -v(p).c.Z,
    hp: p => -p.hp, spd: p => -p.spd, rnd: p => p._r
  };
  function filtered() {
    let out = L.filter(p => {
      if (state.q) {
        const q = norm(state.q);
        const hit = norm(p.name).includes(q) || String(p.dex).includes(state.q) || norm(p.alt || '').includes(q)
          || (q.length >= 3 && (p.ab.some(a => a && norm(AN[a] || '').includes(q)) || p.bm.some(i => norm(MV[i]).includes(q)) || p.tm.some(i => norm(MV[i]).includes(q))));
        if (!hit) return false;
      }
      if (state.tmday && !(today && p.st.some(i => today.idx.has(i)))) return false;
      if (state.types.size && !p.types.some(t => state.types.has(t))) return false;
      if (state.tiers.size && !state.tiers.has(v(p).tier)) return false;
      if (state.leg && !p.leg) return false;
      if (state.slow && !v(p).slow) return false;
      if (state.stun && !v(p).stun) return false;
      if (state.regen && !v(p).regen) return false;
      if (state.mine && !(save && save.owned.includes(p.dex))) return false;
      return true;
    });
    if (state.sort === 'rnd') out.forEach(p => { p._r = Math.random(); });
    const k = SORTS[state.sort] || SORTS.pos;
    out.sort((a, b) => { const x = k(a), y = k(b); return (x < y ? -1 : x > y ? 1 : 0) * state.dir; });
    return out;
  }
  let drawn = 0;
  function card(p) {
    const m = v(p);
    const lazy = drawn++ < 32 ? 'eager' : 'lazy';
    const tools = [m.slow ? `<span class="tool slow" title="${T.slow}">${T.slowS}</span>` : '', m.stun ? `<span class="tool stun" title="${T.stun}">${T.stunS}</span>` : '', m.regen ? `<span class="tool regen" title="${T.regen}">${T.regenS}</span>` : ''].join('');
    let you = '';
    if (save) {
      const mine = save.owned.includes(p.dex), u = ST.upg(save, p.dex), r = youRank ? youRank.get(p.dex) : null;
      you = `<span class="you">${mine ? `<span class="tool own" title="${T.owned}">${T.ownedS}</span>` : ''}${u ? `<span class="tool upg" title="${T.upgrades}">${u}/${ST.UPG_MAX}</span>` : ''}${r && mine ? `<span class="tool yr" title="${T.yourRank}">${T.you} #${r}</span>` : ''}</span>`;
    }
    return `<a class="card" href="pokemon/${p.slug}/"><span class="pos">${m.pos}</span><span class="tier ${m.tier}">${m.tier}</span>
      <span class="pic"><img class="px" loading="${lazy}" src="../img/p/${p.dex}.png" alt="" width="64" height="64"></span>
      <span class="name">${p.name}</span><span class="dex">${document.documentElement.lang === 'es' ? 'Nº' : 'No.'} ${String(p.dex).padStart(3, '0')}${p.dl && p.dl[state.mode === 'shop' ? 1 : 0] ? `<span class="dl ${p.dl[state.mode === 'shop' ? 1 : 0] > 0 ? 'up' : 'down'}" title="${T.moved}">${p.dl[state.mode === 'shop' ? 1 : 0] > 0 ? '▲' : '▼'}${Math.abs(p.dl[state.mode === 'shop' ? 1 : 0])}</span>` : ''}</span>
      <span class="types">${p.types.map(t => `<span class="type" style="--tc:${TC[t]}">${T.types[t]}</span>`).join('')}</span>
      <span class="tools">${tools}</span>${you}</a>`;
  }
  function render() {
    computeYouRank();
    const list = filtered();
    $('#count').textContent = T.count.replace('{n}', list.length).replace('{m}', L.length);
    const groups = new Map();
    const keyOf = p => state.group === 'tier' ? v(p).tier : state.group === 'type' ? p.types[0] : state.group === 'leg' ? (p.leg ? 'leg' : 'nor') : 'all';
    for (const p of list) { const k = keyOf(p); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(p); }
    const order = state.group === 'tier' ? ['S', 'A', 'B', 'C', 'D'] : state.group === 'type' ? TYPES : state.group === 'leg' ? ['leg', 'nor'] : ['all'];
    const title = k => state.group === 'tier' ? `${T.tier} ${k}` : state.group === 'type' ? T.types[k] : state.group === 'leg' ? (k === 'leg' ? T.legs : T.nonlegs) : T.all;
    let html = '';
    drawn = 0;
    for (const k of order) {
      const g = groups.get(k); if (!g) continue;
      html += `<section class="group"><div class="group-h"><h2>${title(k)}</h2><span class="n">${g.length}</span></div><div class="grid">${g.map(card).join('')}</div></section>`;
    }
    $('#out').innerHTML = html || `<div class="empty">${state.tmday && list.length === 0 ? T.tmNone : T.none}</div>`;
    writeUrl();
  }
  render();
  loadScores();
  $('#me-load').addEventListener('click', loadScores);
})();
