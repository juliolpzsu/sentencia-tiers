/* Partida del jugador (opcional): se guarda solo en este navegador (localStorage) y no se envía a ningún sitio.
   Replica el sorteo de habilidad y naturaleza del juego (js/systems/mons.js): hash FNV con la fecha de creación de la partida. */
window.ST = (() => {
  const KEY = 'st.save';
  function hash(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995); h ^= h >>> 15;
    return (h >>> 0) / 4294967296;
  }
  function load() { try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; } }
  function store(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }
  function clear() { try { localStorage.removeItem(KEY); } catch (e) {} }
  function parse(text) {
    const o = JSON.parse(text.trim());
    if (!o || typeof o !== 'object' || !o.owned || !o.created) throw new Error('formato');
    return { created: o.created, owned: Object.keys(o.owned).map(Number), pupg: o.pupg || {}, pabil: o.pabil || {}, pnat: o.pnat || {},
             partner: o.partner || null, name: o.name || '', shiny: Object.keys(o.shiny || {}).map(Number) };
  }
  const UPG_MAX = 92;
  function upg(s, dex) { const u = s.pupg[dex]; return u ? Object.values(u).reduce((a, b) => a + (+b || 0), 0) : 0; }
  function abilSlot(s, dex, abils) {
    const p = s.pabil[dex];
    if (p && abils[p[0]]) return p[0];
    const roll = salt => hash(s.created + ':' + dex + ':' + salt);
    if (abils[2] && roll('hid') < 1 / 20) return 2;
    return abils[1] && roll('abil') < 0.5 ? 1 : 0;
  }
  function natureIdx(s, dex, natures) {
    const p = s.pnat[dex];
    if (p) { const i = natures.findIndex(n => n.id === p[0]); if (i >= 0) return i; }
    return Math.floor(hash(s.created + ':' + dex + ':nat') * natures.length);
  }
  /** Puntuación con la habilidad que le tocó: la de su hueco (si el hueco 2 repite al 1, la del 1). */
  function score(s, dex, abils, abs, base) {
    let slot = abilSlot(s, dex, abils);
    if (slot === 1 && abils[1] === abils[0]) slot = 0;
    return { slot, sc: abs[slot] != null ? abs[slot] : base };
  }
  return { hash, load, store, clear, parse, upg, abilSlot, natureIdx, score, UPG_MAX,
           SNIPPET: "copy(localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('ps.cloud.'))))" };
})();
