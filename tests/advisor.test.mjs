// Pruebas del Consejero (extension/advisor.js) con los datos reales del juego (data/game) y
// el advisor.json que genera la web. Uso: node --test tests/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const read = (p) => readFileSync(ROOT + p, 'utf8');

// Un navegador mínimo: el Consejero solo necesita window, localStorage y poco más.
function sandbox() {
  const store = new Map();
  const ctx = {
    console, Math, JSON, Date, Set, Map, Object, Array, String, Number, Promise,
    setTimeout: () => 0, setInterval: () => 0, clearTimeout: () => {},
    addEventListener: () => {}, removeEventListener: () => {}, postMessage: () => {},
    location: { origin: 'https://pokesurvivor.com' },
    localStorage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)) },
    document: { documentElement: { lang: 'es', classList: { contains: () => false } }, getElementById: () => null, querySelector: () => null, querySelectorAll: () => [], head: { appendChild() {} },
      createElement: () => ({ hidden: false, innerHTML: '' }), body: { appendChild(el) { ctx.__jd = el; } } },
    PS_LOCALES: { lang: 'es' },
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  // El juego: sus movimientos reales (moves.js define G.Moves).
  ctx.G = { U: {}, Stats: {} };
  vm.runInContext(read('data/game/js_data_moves.js'), ctx);
  vm.runInContext(read('extension/advisor.js'), ctx);
  const G = ctx.G;
  const NS = {
    LIFT: 1, U: {},
    Moves: G.Moves,
    Stats: { fit: (mon, cat) => (!cat || cat === mon.side ? 1 : 0.8) },
    LevelUp: { STATS: [['hp', 0], ['atk', 40], ['spd', 8], ['cd', 10], ['def', 12], ['rgn', 0], ['mag', 6], ['xp', 8], ['heal', 0]].map(([id, max]) => ({ id, title: id, max })) },
    Game: { st: { time: 0 } },
    T: (s) => s,
  };
  ctx.__stAdvisorCore.setNS(NS);
  ctx.__stAdvisorCore.setData(JSON.parse(read('docs/assets/advisor.json')));
  return { G, NS, ctx, core: ctx.__stAdvisorCore };
}

const S = sandbox();
const mv = (id, lvl = 1) => S.G.Moves.instance(id, lvl);
const maxed = (id) => mv(id, S.G.Moves.BY_ID[id].maxLvl);
function player(dex, types, side, moves, extra = {}) {
  const mon = { dex, types, side };
  return Object.assign({ dex, mon, moves, slots: moves.map((m) => [m]), maxMoves: 4, statsTaken: {}, hp: 100, maxHp: 100,
    level: 10, baseSpd: 100, spdMul: 1, cdMul: 1, dmgReduce: 0, banned: new Set() }, extra);
}
const card = (key, extra = {}) => ({ key, type: key.split(':')[0], ...extra });
const advise = (cards, pl, time = 600) => { S.NS.Game.st.time = time; return S.core.advise(cards, pl); };
const keyOfBest = (cards, pl, time) => cards[advise(cards, pl, time).best].key;

// Cloyster (91): build ice-beam (frenazo), freeze-dry (aturdimiento), ice-shard, aqua-ring.
const cloyster = (moves, extra) => player(91, ['water', 'ice'], 'physical', moves, extra);
// Magnezone (462): thunder-wave (aturdimiento), thunder-shock, nasty-plot, meteor-mash. Especial.
const magnezone = (moves, extra) => player(462, ['electric', 'steel'], 'special', moves, extra);

test('los datos cubren a Cloyster y Magnezone', () => {
  assert.equal(advise([card('stat:cd')], cloyster([mv('ice-beam')])).B.b.m[0][0], 'ice-beam');
  assert.ok(advise([card('stat:cd')], magnezone([mv('thunder-shock')])));
});

test('un ataque de la build va antes que una mejora de stat', () => {
  const cards = [card('stat:cd'), card('new:freeze-dry'), card('stat:hp')];
  assert.equal(keyOfBest(cards, cloyster([mv('ice-beam')])), 'new:freeze-dry');
});

test('un ataque fuera de la build que quita un hueco necesario se evita', () => {
  const pl = cloyster([mv('ice-beam')]);
  const a = advise([card('new:hyper-beam'), card('stat:mag'), card('new:metal-claw')], pl);
  assert.equal(a.best, 1);                         // mejor Imán que estropear la build
  assert.ok(a.out[0].s < 10 && a.out[2].s < 10);
});

test('si todas estorban, la menos mala es un ataque de su lado bueno', () => {
  const pl = magnezone([mv('thunder-wave'), mv('meteor-mash')]);
  const cards = [card('new:metal-claw'), card('new:hyper-beam'), card('new:swords-dance')];
  assert.equal(keyOfBest(cards, pl), 'new:hyper-beam');   // especial; Garra Metal es físico, Danza Espada potenciador
});

test('la evolución siempre es la recomendada', () => {
  const pl = cloyster([maxed('ice-beam'), mv('freeze-dry')], { statsTaken: { atk: 1 } });
  assert.equal(keyOfBest([card('stat:cd'), card('evo:ice-beam'), card('new:ice-shard')], pl), 'evo:ice-beam');
});

test('la mejora que desbloquea una evolución lista va primero', () => {
  const pl = cloyster([maxed('ice-beam'), mv('freeze-dry')]);
  assert.equal(keyOfBest([card('stat:cd'), card('stat:atk', { tag: 'Evoluciona Rayo Hielo', color: '#ffd23f' }), card('up:freeze-dry')], pl), 'stat:atk');
});

test('una evolución lejana solo da un empujón', () => {
  const pl = magnezone([mv('thunder-wave', 2), mv('meteor-mash')]);
  assert.equal(keyOfBest([card('up:thunder-wave'), card('stat:atk')], pl), 'up:thunder-wave');
});

test('Baya Zidra solo con poca vida', () => {
  const cards = [card('stat:heal'), card('stat:cd')];
  assert.equal(keyOfBest(cards, cloyster([mv('ice-beam')], { hp: 30 })), 'stat:heal');
  assert.equal(keyOfBest(cards, cloyster([mv('ice-beam')], { hp: 90 })), 'stat:cd');
});

test('Coraza no se recomienda cuando ya no suma (tope del 70 %)', () => {
  const cards = [card('stat:def'), card('stat:hp')];
  assert.equal(keyOfBest(cards, cloyster([mv('ice-beam')], { dmgReduce: 0.2 })), 'stat:def');
  const capped = advise(cards, cloyster([mv('ice-beam')], { dmgReduce: 0.7 }));
  assert.equal(capped.best, 1);
  assert.ok(capped.out[0].s < 10);
  // A medias: con un 68 % solo suma un 2 %.
  const part = advise(cards, cloyster([mv('ice-beam')], { dmgReduce: 0.68 }));
  assert.ok(part.out[0].s < 55 && part.out[0].s > 10);
});

test('Carrera según la velocidad real y su tope suave', () => {
  const cards = [card('stat:spd'), card('stat:hp')];
  assert.equal(keyOfBest(cards, cloyster([mv('ice-beam')], { baseSpd: 90 })), 'stat:spd');              // 90 → faltan cartas
  assert.equal(keyOfBest(cards, cloyster([mv('ice-beam')], { baseSpd: 100, spdMul: 1.4 })), 'stat:hp');   // 140: ya pasa de 130
});

test('Reflejos no sirve con la recarga ya en el mínimo', () => {
  const pl = cloyster([mv('ice-beam')], { cdMul: 0.01 });
  const a = advise([card('stat:cd'), card('stat:hp')], pl);
  assert.equal(a.best, 1);
});

test('el motivo lleva el contador de veces que sale cada mejora', () => {
  const pl = cloyster([mv('ice-beam')], { statsTaken: { cd: 3 } });
  assert.match(advise([card('stat:cd')], pl).out[0].why, /\(3\/10\)/);
});

test('objeto: los de la build primero, y la Cinta Elección al final', () => {
  const pl = magnezone([mv('thunder-wave')]);
  const s = (id) => S.core.itemScore(id, pl).s;
  assert.ok(s('leftovers') > s('focussash') && s('focussash') > s('assaultvest'));   // orden de la build de la web
  assert.ok(s('assaultvest') > s('quickclaw'));
  assert.ok(s('choiceband') < s('amuletcoin'));
});

test('vínculo: se fusiona antes el control que el resto', () => {
  const pl = magnezone([mv('thunder-wave'), mv('thunder-shock'), mv('nasty-plot'), mv('metal-claw')]);
  const r = (id) => S.core.bondRank(pl.moves.find((m) => m.id === id), pl);
  assert.ok(r('thunder-wave') > r('thunder-shock'));
  assert.ok(r('thunder-shock') > r('nasty-plot'));
  assert.ok(r('nasty-plot') > r('metal-claw'));      // fuera de la build, lo último
});

test('Sentencia: distancia a Arceus y aviso de control con legendarios encima', () => {
  const pl = magnezone([mv('thunder-shock'), mv('thunder-wave')], { x: 0, y: 0, active: 0, dead: false });
  pl.slots = [[pl.moves[0]], [pl.moves[1]]];
  const foes = [{ dex: 493, x: 150, y: 0 }, { boss: true, x: 100, y: 50 }, { boss: true, x: -80, y: 90 }];
  Object.assign(S.NS, { Judgment: { active: true, cinematic: false }, EnemyMgr: { all: () => foes } });
  S.NS.Game = { st: { time: 1900 }, state: 'playing', player: pl };
  S.core.judgmentTick();
  const html = S.ctx.__jd.innerHTML;
  assert.match(html, /150 px/);
  assert.match(html, /demasiado cerca/);
  assert.match(html, /2 legendarios cerca/);
  assert.match(html, /activa Onda Trueno \(2\)/);       // el aturdimiento está en el hueco 2 y no es el activo
  pl.active = 1;
  S.core.judgmentTick();
  assert.doesNotMatch(S.ctx.__jd.innerHTML, /activa/);   // ya lo tienes activo: sin aviso
  foes[0].x = 300;
  S.core.judgmentTick();
  assert.match(S.ctx.__jd.innerHTML, /buena distancia/);
});
