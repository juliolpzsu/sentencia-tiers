// Sentencia Tiers · Consejero: en cada subida de nivel de PokéSurvivor marca qué
// carta conviene coger según la build de la Sentencia de Arceus del Pokémon que
// juegas (la de https://juliolpzsu.github.io/sentencia-tiers/).
//
// Convive con PokeSurvivor Plus:
//  - Las dos necesitan el objeto privado del juego (Camera, LevelUp, RunUI...).
//    PokeSurvivor Plus lo deja en window.__psmodNS; si no está, esta extensión
//    lo atrapa con el mismo truco (un setter de un solo uso en Object.prototype),
//    encadenado con el que hubiera para no quitarle el suyo a nadie.
//  - Solo envuelve G.LevelUp.offer (devuelve la misma lista, sin tocarla) y
//    nunca reescribe las cartas: añade una etiqueta absoluta dentro de cada una
//    (PokeSurvivor Plus les fija la altura) y una línea debajo de la caja.
//  - Clases y ids con prefijo "sta-"; estado en localStorage con "sta:".
// Corre en el mundo de la página (MAIN) en document_start, antes del juego.
(() => {
  'use strict';
  if (window.__stAdvisor) return;
  window.__stAdvisor = true;

  const LS = 'sta:';
  const load = (k, d) => { try { const v = localStorage.getItem(LS + k); return v == null ? d : JSON.parse(v); } catch { return d; } };
  const save = (k, v) => { try { localStorage.setItem(LS + k, JSON.stringify(v)); } catch { /* sin almacenamiento */ } };
  const SITE = 'https://juliolpzsu.github.io/sentencia-tiers';
  const log = (...a) => { if (load('debug', false)) console.log('[Consejero]', ...a); };

  // ---------------- el objeto del juego ----------------
  let NS = null;
  const isNS = (o) => o && typeof o === 'object' && 'LIFT' in o && 'U' in o;
  (function trapCamera() {
    const prev = Object.getOwnPropertyDescriptor(Object.prototype, 'Camera');
    function set(v) {
      if (prev && prev.set) prev.set.call(this, v);   // el de PokeSurvivor Plus (u otro), primero
      if (!Object.prototype.hasOwnProperty.call(this, 'Camera')) {
        Object.defineProperty(this, 'Camera', { value: v, writable: true, configurable: true, enumerable: true });
      }
      if (!NS && isNS(this)) {
        NS = this;
        // Fuera la trampa (si sigue siendo la nuestra: la de otro no se toca).
        const d = Object.getOwnPropertyDescriptor(Object.prototype, 'Camera');
        if (d && d.set === set) {
          if (prev && prev.set) Object.defineProperty(Object.prototype, 'Camera', prev);
          else delete Object.prototype.Camera;
        }
      }
    }
    try {
      Object.defineProperty(Object.prototype, 'Camera', {
        configurable: true,
        get() { return prev && prev.get ? prev.get.call(this) : undefined; },
        set,
      });
    } catch (_) { /* si no se puede, queda window.__psmodNS */ }
  })();
  const ns = () => NS || (isNS(window.__psmodNS) ? (NS = window.__psmodNS) : null);

  function waitFor(test, fn, ms = 250, tries = 480) {
    const tick = () => {
      let ok = false;
      try { ok = !!test(); } catch (_) { ok = false; }
      if (ok) { try { fn(); } catch (err) { console.warn('[Consejero] no se pudo iniciar:', err); } return; }
      if (--tries > 0) setTimeout(tick, ms);
      else console.warn('[Consejero] el juego no expone lo que necesito (¿ha cambiado?): sin recomendaciones.');
    };
    tick();
  }

  // ---------------- datos de la web ----------------
  let DATA = window.__stAdvisorData || null;   // copia de serie (data.js)
  // La extensión pide una vez al día los datos actualizados de la web (bridge.js → background.js).
  (function refresh() {
    const cached = load('data', null);
    if (cached && cached.mons && (!DATA || cached.generated >= DATA.generated)) DATA = cached;
    if (cached && Date.now() - (load('dataAt', 0)) < 20 * 3600e3) return;
    const id = Math.random().toString(36).slice(2);
    const onMsg = (e) => {
      const d = e.source === window && e.data;
      if (!d || d.staBridgeRes !== 'data' || d.id !== id) return;
      removeEventListener('message', onMsg);
      const r = d.res;
      if (r && r.ok && r.data && r.data.mons && r.data.v === 1) {
        if (!DATA || r.data.generated >= DATA.generated) DATA = r.data;
        save('data', r.data); save('dataAt', Date.now());
        log('datos de la web', r.data.generated);
      } else log('sin datos nuevos', r && r.err);
    };
    addEventListener('message', onMsg);
    setTimeout(() => postMessage({ staBridge: 'data', id }, location.origin), 1500);
  })();

  // ---------------- idioma ----------------
  const lang = () => {
    const l = (window.PS_LOCALES && window.PS_LOCALES.lang) || document.documentElement.lang || 'es';
    return String(l).startsWith('es') ? 'es' : 'en';
  };
  const TXT = {
    es: {
      best: 'RECOMENDADA', least: 'LA MENOS MALA', ok: 'también vale', bad: 'evitar',
      reroll: 'las tres estropean la build: mejor cambia las cartas (R).',
      head: 'Consejero', ficha: 'ficha', off: 'Consejero apagado (Alt + J para encenderlo)',
      noData: 'sin datos de este Pokémon',
      evo: 'evoluciona el ataque: siempre merece la pena',
      newBuild: (m, r) => `${m} es de su build (${r})`,
      newFill: (n) => `ataque fuera de la build, pero te sobran ${n === 1 ? 'un hueco' : n + ' huecos'}`,
      newBad: (miss) => `ocupa un hueco que pide ${miss}`,
      newBuff: 'potenciador fuera de la build',
      up: (m, r) => `sube ${m} (${r})`,
      upOff: (m) => `${m} no es de la build`,
      upEvo: (s) => `y al máximo evoluciona (ya tienes ${s})`,
      stat: {
        cd: 'Reflejos: encadena frenazos y aturdimientos',
        spd: (n) => `Carrera: ${n === 1 ? 'falta 1' : 'faltan ' + n} para el tope suave de 130`,
        spdDone: 'Carrera: ya llegas al tope suave de 130',
        cdFloor: 'Reflejos: tus ataques ya están en la recarga mínima (0,12 s)',
        defCap: 'Coraza: ya estás en el tope del 70 %, no suma nada',
        defPart: (g) => `Coraza: solo suma un ${g} % (tope del 70 %)`,
        def: 'Coraza: lo que más vida ahorra ante los legendarios',
        hp: 'Vigor: margen contra los golpes que escalan',
        rgn: 'Síntesis: lo único que compensa el daño % de Arceus',
        heal: (p) => `Baya Zidra: estás al ${p} % de vida`,
        healFull: 'Baya Zidra: con la vida alta se desperdicia',
        atk: 'Potencia: en la Sentencia el daño apenas cuenta',
        atkEarly: 'Potencia: ayuda a limpiar hordas antes del minuto 30',
        mag: 'Imán: solo si no hay nada mejor',
        xp: 'Aprendizaje: compensa al principio de la partida',
        xpLate: 'Aprendizaje: a estas alturas rinde poco',
        evoNeed: (s, m) => `${s}: la pide ${m} para evolucionar`,
        evoLater: (m) => `además ${m} la pedirá para evolucionar`,
      },
      role: { slow: 'frenazo', stun: 'aturdimiento', primary: 'ataque principal', second: 'segundo ataque', buff: 'potenciador', aquaring: 'regeneración', agility: 'velocidad' },
    },
    en: {
      best: 'RECOMMENDED', least: 'LEAST BAD', ok: 'also fine', bad: 'avoid',
      reroll: 'all three hurt the build: better reroll the cards (R).',
      head: 'Advisor', ficha: 'page', off: 'Advisor off (Alt + J to turn it on)',
      noData: 'no data for this Pokémon',
      evo: 'evolves the move: always worth it',
      newBuild: (m, r) => `${m} is in its build (${r})`,
      newFill: (n) => `off-build move, but you have ${n === 1 ? 'a slot' : n + ' slots'} to spare`,
      newBad: (miss) => `takes a slot that ${miss} needs`,
      newBuff: 'off-build booster',
      up: (m, r) => `upgrades ${m} (${r})`,
      upOff: (m) => `${m} is not in the build`,
      upEvo: (s) => `and evolves at max (you already have ${s})`,
      stat: {
        cd: 'Reflexes: chains slows and stuns',
        spd: (n) => `Sprint: ${n} more to the soft cap of 130`,
        spdDone: 'Sprint: you already reach the soft cap of 130',
        cdFloor: 'Reflexes: your moves are already at the minimum cooldown (0.12 s)',
        defCap: 'Armor: already at the 70% cap, adds nothing',
        defPart: (g) => `Armor: only adds ${g}% (70% cap)`,
        def: 'Armor: saves the most HP against the legendaries',
        hp: 'Vigor: margin against the scaling hits',
        rgn: 'Synthesis: the only answer to Arceus’ % damage',
        heal: (p) => `Sitrus Berry: you are at ${p}% HP`,
        healFull: 'Sitrus Berry: wasted at high HP',
        atk: 'Power: damage barely matters in the Judgment',
        atkEarly: 'Power: helps clear hordes before minute 30',
        mag: 'Magnet: only if nothing better',
        xp: 'Learning: pays off early in the run',
        xpLate: 'Learning: worth little this late',
        evoNeed: (s, m) => `${s}: ${m} needs it to evolve`,
        evoLater: (m) => `${m} will also need it to evolve`,
      },
      role: { slow: 'slow', stun: 'stun', primary: 'main attack', second: 'second attack', buff: 'booster', aquaring: 'regeneration', agility: 'speed' },
    },
  };
  const T = () => TXT[lang()];

  // ---------------- la recomendación ----------------
  // Importancia de cada papel de la build en la Sentencia (frenazo y aturdimiento primero).
  const ROLE_NEW = { slow: 96, stun: 94, aquaring: 88, primary: 86, second: 72, buff: 66, agility: 62 };
  const ROLE_UP = { slow: 74, stun: 72, aquaring: 60, primary: 68, second: 56, buff: 50, agility: 46 };

  const moveName = (id) => {
    const N = ns(), d = N && N.Moves && N.Moves.BY_ID[id];
    if (!d) return id;
    try { return N.T ? N.T(d.name, 'move') : d.name; } catch { return d.name; }
  };
  const statTitle = (id) => {
    const N = ns(), s = N && N.LevelUp && (N.LevelUp.STATS || []).find((x) => x.id === id);
    if (!s) return id;
    try { return N.T ? N.T(s.title) : s.title; } catch { return s.title; }
  };

  /** La build que toca: la de la Tienda Kecleon si ya enseñaste sus MT, si no la base. */
  function buildFor(pl) {
    if (!DATA && window.__stAdvisorData) DATA = window.__stAdvisorData;
    const e = DATA && DATA.mons && DATA.mons[String(pl.dex || (pl.mon && pl.mon.dex))];
    if (!e) return null;
    let b = e.b, shop = false;
    if (e.k && e.k.tm && e.k.tm.length) {
      const N = ns();
      let pool = [];
      try { pool = N.Moves.poolFor(pl.mon); } catch (_) { /* sin pool */ }
      if (e.k.tm.every((id) => pool.includes(id))) { b = e.k; shop = true; }
    }
    const banned = pl.banned || new Set();
    const role = {};
    for (const [id, r] of b.m) role[id] = r;
    return { e, b, shop, role, moves: b.m.map(([id]) => id).filter((id) => !banned.has(id)) };
  }

  function score(c, pl, B, ctx) {
    const t = T(), S = t.stat;
    const [type, id] = String(c.key || '').split(':');
    if (type === 'evo') return { s: 100, why: t.evo };
    if (type === 'new') {
      const r = B.role[id];
      if (r) return { s: ROLE_NEW[r] || 70, why: t.newBuild(moveName(id), t.role[r]) };
      const def = ns().Moves.BY_ID[id] || {};
      const spare = ctx.free - ctx.missing.length;
      if (spare > 0) {
        if (def.kind === 'buff') return { s: 24, why: t.newBuff };
        let fit = 1;
        try { fit = ns().Stats.fit(pl.mon, def.cat); } catch (_) { /* 1 */ }
        return { s: 34 + (fit >= 0.999 ? 8 : 0), why: t.newFill(spare) };
      }
      // Estorba a la build: si no hay otra cosa, mejor un ataque de su lado bueno que un potenciador.
      let fit = 1;
      try { fit = ns().Stats.fit(pl.mon, def.cat); } catch (_) { /* 1 */ }
      return { s: def.kind === 'buff' ? 3 : 4 + (fit >= 0.999 ? 2 : 0), why: t.newBad(ctx.missing.map(moveName).join(' / ')) };
    }
    if (type === 'up') {
      const r = B.role[id], m = (pl.moves || []).find((x) => x.id === id);
      if (!r) return { s: 28, why: t.upOff(moveName(id)) };
      let s = ROLE_UP[r] || 50, why = t.up(moveName(id), t.role[r]);
      if (m && m.def && m.lvl + 1 >= m.def.maxLvl) {
        const need = (B.b.e || {})[id];
        if (need && pl.statsTaken && pl.statsTaken[need]) { s += 10; why += ' ' + t.upEvo(statTitle(need)); }
        else s += 4;
      }
      return { s, why };
    }
    if (type === 'stat') {
      const taken = pl.statsTaken || {}, min = ctx.time / 60;
      // ¿Algún ataque de la build que ya tienes la pide para evolucionar? Cerca del máximo, va primero;
      // lejos, solo un empujón (se puede coger más adelante).
      const owned = (mv) => (pl.moves || []).find((x) => x.id === mv && !x.evolved);
      const needs = Object.entries(B.b.e || {}).filter(([mv, st]) => st === id && !taken[st] && owned(mv));
      const near = needs.find(([mv]) => { const m = owned(mv); return m.def && m.lvl >= m.def.maxLvl - 2; });
      const needBy = near || null, far = needs[0] || null;
      // Carta dorada: un ataque ya al máximo espera esta mejora para evolucionar.
      const N = ns();
      const ready = (pl.moves || []).find((m) => { try { const ev = N.Moves.evoInfo(m, taken); return ev && !ev.ready && ev.needs === id; } catch { return false; } });
      if (ready) return { s: 90, why: S.evoNeed(statTitle(id), moveName(ready.id)) };
      if (needBy) return { s: 80, why: S.evoNeed(statTitle(id), moveName(needBy[0])) };
      const hp = pl.maxHp ? pl.hp / pl.maxHp : 1;
      const r = statScore(id, S, taken, B, min, hp, pl);
      if (far) { r.s += 8; r.why += ' · ' + S.evoLater(moveName(far[0])); }
      return r;
    }
    return { s: 30, why: '' };
  }

  // Lo que de verdad suma cada mejora en esta partida. El juego deja de ofrecer una mejora al
  // llegar a su tope de veces (Potencia 40, Carrera 8, Reflejos 10, Coraza 12, Imán 6,
  // Aprendizaje 8), pero algunas dejan de servir antes:
  //  - Coraza: cada carta hace min(70 %, actual + 6 %). Con reducción de Mejoras (2 % por nivel)
  //    o el Chaleco Asalto (+20 %) se llega al 70 % antes de las 12 cartas y las demás no dan nada.
  //  - Carrera: en la Sentencia la velocidad pasa de 130 solo al 25 % (tope suave).
  //  - Reflejos: ningún ataque baja de 0,12 s de recarga.
  const DEF_CAP = 0.7, SPD_SOFT = 130, CD_FLOOR = 0.12;
  function statMax(id) {
    const N = ns(), s = N && N.LevelUp && (N.LevelUp.STATS || []).find((x) => x.id === id);
    return s && s.max ? s.max : 0;
  }
  function statScore(id, S, taken, B, min, hp, pl) {
    const max = statMax(id), n = taken[id] || 0;
    const count = (r) => { if (max && r.why) r.why += ` (${n}/${max})`; return r; };
    switch (id) {
      case 'heal': return hp < 0.4 ? { s: 92, why: S.heal(Math.round(hp * 100)) } : hp < 0.6 ? { s: 58, why: S.heal(Math.round(hp * 100)) } : { s: 12, why: S.healFull };
      case 'cd': {
        const atk = (pl.moves || []).filter((m) => m.kind !== 'buff' && m.cd);
        if (atk.length && pl.cdMul && atk.every((m) => m.cd * pl.cdMul * 0.92 <= CD_FLOOR + 1e-9)) return count({ s: 8, why: S.cdFloor });
        return count({ s: 64, why: S.cd });
      }
      case 'spd': {
        // Con tu velocidad real (Mejoras, objeto...); si no se puede leer, la cuenta de la web.
        let left = Math.max(0, (B.b.sp || 0) - n);
        if (pl.baseSpd && pl.spdMul) left = Math.max(0, Math.ceil(Math.log(SPD_SOFT / (pl.baseSpd * pl.spdMul)) / Math.log(1.07)));
        if (max) left = Math.min(left, max - n);
        return count(left ? { s: 63, why: S.spd(left) } : { s: min < 30 ? 36 : 26, why: S.spdDone });
      }
      case 'def': {
        if (typeof pl.dmgReduce === 'number') {
          const gain = Math.min(DEF_CAP, pl.dmgReduce + 0.06) - pl.dmgReduce;
          if (gain < 0.005) return count({ s: 3, why: S.defCap });
          if (gain < 0.0599) return count({ s: Math.round(20 + 41 * gain / 0.06), why: S.defPart(Math.round(gain * 100)) });
        }
        return count({ s: 61, why: S.def });
      }
      case 'hp': return { s: 55, why: S.hp };
      case 'rgn': return { s: 53 + (min >= 25 ? 4 : 0), why: S.rgn };
      case 'atk': return count(min < 20 ? { s: 46, why: S.atkEarly } : { s: 32, why: S.atk });
      case 'xp': return count(min < 8 ? { s: 44, why: S.xp } : { s: 14, why: S.xpLate });
      case 'mag': return count({ s: 16, why: S.mag });
    }
    return { s: 30, why: '' };
  }

  function advise(list, pl) {
    const B = buildFor(pl);
    if (!B) return null;
    const N = ns();
    const have = new Set((pl.moves || []).map((m) => m.id));
    const free = Math.max(0, (pl.maxMoves || 4) - ((pl.slots && pl.slots.length) || 0));
    // Los de la build que aún te faltan y que pueden salir (en tu pool).
    let pool = null;
    try { pool = new Set(N.Moves.poolFor(pl.mon)); } catch (_) { /* sin pool */ }
    const missing = B.moves.filter((id) => !have.has(id) && (!pool || pool.has(id)));
    const ctx = { free, missing, time: (N.Game && N.Game.st && N.Game.st.time) || 0 };
    const out = list.map((c) => { try { return score(c, pl, B, ctx); } catch (err) { log(err); return { s: 0, why: '' }; } });
    const best = out.reduce((bi, x, i) => (x.s > out[bi].s ? i : bi), 0);
    return { B, out, best };
  }

  // ---------------- en pantalla ----------------
  let last = null;        // { list, pl }
  let enabled = load('on', true);

  function css() {
    if (document.getElementById('sta-css')) return;
    const st = document.createElement('style');
    st.id = 'sta-css';
    st.textContent = `
#cards > .card.sta-c{position:relative}
#cards > .card .sta-b{position:absolute;top:7px;right:12px;z-index:3;pointer-events:none;font:700 10px/1.2 system-ui,sans-serif;letter-spacing:.06em;padding:2px 6px;border-radius:4px;background:rgba(0,0,0,.55);color:#cfd8e6;white-space:nowrap;text-shadow:none}
#cards > .card.sta-best{box-shadow:inset 0 0 0 2px #fcee0a,0 0 14px rgba(252,238,10,.35)}
#cards > .card.sta-best .sta-b{background:#fcee0a;color:#000}
#cards > .card.sta-bad .sta-b{background:rgba(255,0,60,.75);color:#fff}
#sta-why{text-shadow:none;margin:8px 0 0;padding:6px 10px;border-left:3px solid #fcee0a;background:rgba(0,0,0,.35);font:12px/1.35 system-ui,sans-serif;color:#e8eef8;text-align:left}
#sta-why b{color:#fcee0a}
#sta-why .sta-k{color:#00e5ff;text-decoration:none;margin-left:6px}
#sta-why .sta-m{color:#9fb1c9}
@media (max-height:520px){#sta-why{font-size:11px;padding:4px 8px;margin-top:4px}}`;
    document.head.appendChild(st);
  }

  function whyBox() {
    let el = document.getElementById('sta-why');
    if (el) return el;
    const box = document.querySelector('#scr-levelup .box');
    if (!box) return null;
    el = document.createElement('div');
    el.id = 'sta-why';
    box.appendChild(el);
    return el;
  }

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  const rerollOpen = () => { const r = document.getElementById('lvl-reroll'); return !!r && !r.classList.contains('hidden'); };

  function clear() {
    document.querySelectorAll('#cards > .card .sta-b').forEach((b) => b.remove());
    document.querySelectorAll('#cards > .card.sta-c').forEach((el) => el.classList.remove('sta-c', 'sta-best', 'sta-bad'));
    const w = document.getElementById('sta-why');
    if (w) w.hidden = true;
  }

  function decorate() {
    const box = document.getElementById('cards');
    if (!box || !last) return;
    const cards = box.querySelectorAll(':scope > .card');
    clear();
    const w = whyBox();
    if (!enabled) { if (w) { w.hidden = false; w.innerHTML = `<span class="sta-m">${esc(T().off)}</span>`; } return; }
    if (cards.length !== last.list.length) return;
    const t = T();
    const a = advise(last.list, last.pl);
    if (!a) { if (w) { w.hidden = false; w.innerHTML = `<b>${t.head}</b> <span class="sta-m">· ${t.noData}</span>`; } return; }
    css();
    cards.forEach((el, i) => {
      const x = a.out[i];
      el.classList.add('sta-c');
      const tag = document.createElement('span');
      tag.className = 'sta-b';
      if (i === a.best) { el.classList.add('sta-best'); tag.textContent = x.s < 10 ? t.least : '★ ' + t.best; }
      else if (x.s < 10) { el.classList.add('sta-bad'); tag.textContent = t.bad; }
      else if (a.out[a.best].s - x.s <= 6) tag.textContent = t.ok;
      else { tag.remove(); return; }
      tag.title = x.why;
      el.appendChild(tag);
    });
    if (w) {
      const e = a.B.e, L = lang();
      const link = `${SITE}/${L}/pokemon/${e.s}/`;
      w.hidden = false;
      w.innerHTML = `<b>${t.head} · ${a.best + 1}</b> ${esc(a.out[a.best].why)}` +
        `<span class="sta-m"> · ${L === 'es' ? 'Sentencia' : 'Judgment'} ${e.t} #${e.p}${a.B.shop ? (L === 'es' ? ' · build de tienda' : ' · shop build') : ''}</span>` +
        (a.out[a.best].s < 10 && rerollOpen() ? `<br><b>↻</b> ${esc(t.reroll)}` : '') +
        `<a class="sta-k" href="${link}" target="_blank" rel="noopener">${t.ficha} ↗</a>`;
    }
    log('cartas', last.list.map((c) => c.key), a.out);
  }

  function setup() {
    const N = ns();
    // Una sola envoltura, que no cambia nada: anota qué cartas salen y para quién.
    const offer = N.LevelUp.offer;
    if (!offer.__sta) {
      const wrapped = function (pl) {
        const r = offer.apply(this, arguments);
        if (Array.isArray(r)) { last = { list: r, pl: pl || (N.Game && N.Game.player) }; setTimeout(decorate, 0); }
        return r;
      };
      wrapped.__sta = true;
      N.LevelUp.offer = wrapped;
    }
    // Cada vez que el juego pinta las cartas (nivel nuevo o cambiar cartas), se marcan.
    const box = document.getElementById('cards');
    new MutationObserver(() => decorate()).observe(box, { childList: true });
    // Alt + J: encender / apagar.
    addEventListener('keydown', (e) => {
      if (e.altKey && !e.ctrlKey && !e.metaKey && (e.code === 'KeyJ')) {
        enabled = !enabled; save('on', enabled); decorate();
        e.preventDefault(); e.stopPropagation();
      }
    }, true);
    window.__stAdvisorApi = { advise: () => last && advise(last.list, last.pl), data: () => DATA, ns };
    log('listo');
  }

  waitFor(() => { const N = ns(); return N && N.LevelUp && N.LevelUp.offer && N.RunUI && document.getElementById('cards'); }, setup);
})();
