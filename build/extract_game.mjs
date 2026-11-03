// Saca los datos de PokéSurvivor de su bundle ofuscado (js/app.min.js) SIN ejecutarlo.
//
// Desde el 30-10-2026 el juego solo publica ese bundle. Es obfuscator.io sobre esbuild: los
// módulos siguen en su orden, con los datos como literales y las cadenas en una tabla. Aquí:
//   1. se lee el fichero con un parser (acorn) y se reconstruye la tabla de cadenas a mano:
//      base64 con su alfabeto y una rotación que se averigua comprobando que los `Math[...]`
//      del código decodifican a miembros de verdad de Math;
//   2. un intérprete mínimo evalúa solo literales y expresiones constantes (nunca eval ni vm);
//   3. se escriben los ficheros de data/game con el formato que leen gamedata.py, abilfx.py,
//      icons.py y las pruebas, y RULES.sha con una huella de cada módulo de reglas.
//
// Si algo no tiene la forma esperada, sale con error: mejor una Action en rojo que un ranking
// viejo en verde.
//
//   node build/extract_game.mjs <app.min.js> <carpeta de salida>
//   node build/extract_game.mjs <app.min.js> --dump <Módulo>   texto legible del módulo, para leer un diff de reglas (no se sube)
//   node build/extract_game.mjs <app.min.js> --hooks           JSON con la huella de los módulos que usa el Consejero (build/check_hooks.py)
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { parse, tokenizer } from './vendor/acorn.mjs';

const OPTS = { ecmaVersion: 'latest', sourceType: 'script' };
// Módulos cuyas reglas replica rank.py a mano (o describe gen.py): si cambian, REVISAR REGLAS.
const RULE_MODULES = ['Judgment', 'Combat', 'Enemy', 'Player', 'Stats', 'Hazards', 'Items', 'Upgrades'];
// Módulos a los que se engancha el Consejero (extension/advisor.js): si cambian, build/check_hooks.py avisa.
const HOOK_MODULES = ['LevelUp', 'RunUI', 'Game', 'Player', 'Moves'];

function fail(msg) { console.error('ERROR extract_game: ' + msg); process.exit(1); }
function need(cond, msg) { if (!cond) fail(msg); return cond; }

function walk(node, fn) {
  if (!node || typeof node.type !== 'string') return;
  fn(node);
  for (const k in node) {
    const v = node[k];
    if (Array.isArray(v)) for (const x of v) walk(x, fn);
    else if (v && typeof v.type === 'string') walk(v, fn);
  }
}

// ---- tabla de cadenas ----
const ALPHA = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';
function b64(s) {
  const out = []; let bits = 0, i = 0;
  for (const ch of s) {
    const c = ALPHA.indexOf(ch);
    if (c < 0) continue;
    bits = i % 4 ? bits * 64 + c : c;
    if (i++ % 4) out.push(255 & bits >> (-2 * i & 6));
  }
  return Buffer.from(out).toString('utf8');
}

function open(src) {
  const body = parse(src, OPTS).body;
  const fns = body.filter(n => n.type === 'FunctionDeclaration').sort((a, b) => (b.end - b.start) - (a.end - a.start));
  need(fns.length === 2, `se esperaban 2 funciones (tabla y decodificador) y hay ${fns.length}: ¿ha cambiado el ofuscador?`);
  const [tableFn, decFn] = fns;
  let table = null;
  walk(tableFn, n => { if (n.type === 'ArrayExpression' && n.elements.length > 100) table = n.elements.map(e => e.value); });
  need(table, 'no aparece la tabla de cadenas');
  const off = /=_0x\w+-(0x[0-9a-f]+);/.exec(src.slice(decFn.start, decFn.end));
  need(off, 'no aparece el desplazamiento del decodificador');
  const offset = parseInt(off[1]);
  const stmt = body.filter(n => n.type === 'ExpressionStatement').sort((a, b) => (b.end - b.start) - (a.end - a.start))[0];
  const aliases = new Set([decFn.id.name]);
  for (let i = 0; i < 3; i++) walk(stmt, n => {
    if (n.type === 'VariableDeclarator' && n.init?.type === 'Identifier' && aliases.has(n.init.name) && n.id.type === 'Identifier') aliases.add(n.id.name);
  });
  const isStr = c => c?.type === 'CallExpression' && c.callee.type === 'Identifier' && aliases.has(c.callee.name) && c.arguments[0]?.type === 'Literal';
  const anchors = [];
  walk(stmt, n => {
    if (n.type === 'MemberExpression' && n.computed && n.object.name === 'Math' && isStr(n.property)) anchors.push(n.property.arguments[0].value - offset);
  });
  need(anchors.length >= 20, 'muy pocos Math[...] para hallar la rotación de la tabla');
  const math = new Set(Object.getOwnPropertyNames(Math)), N = table.length;
  let shift = -1;
  for (let r = 0; r < N && shift < 0; r++) if (anchors.every(a => math.has(b64(table[(a + r) % N])))) shift = r;
  need(shift >= 0, 'no se encontró la rotación de la tabla de cadenas');
  const str = v => b64(table[(v - offset + shift) % N]);
  return { src, stmt, aliases, isStr, str };
}

// ---- estructura: el espacio G y sus módulos ----
function structure(b) {
  const seq = b.stmt.expression.expressions || [b.stmt.expression];
  const iife = seq.find(e => e.type === 'CallExpression' && /Function/.test(e.callee.type));
  need(iife, 'no aparece la función principal del bundle');
  const stmts = iife.callee.body.body;
  const gDecl = stmts.flatMap(s => (s.type === 'VariableDeclaration' ? s.declarations : [])).find(d => d.init?.type !== 'Identifier');
  need(gDecl, 'no aparece el objeto interno del juego');
  const G = gDecl.id.name;
  const keyOf = m => (m.computed ? (b.isStr(m.property) ? b.str(m.property.arguments[0].value) : m.property.value) : m.property.name);
  const keyName = p => (p.computed ? (b.isStr(p.key) ? b.str(p.key.arguments[0].value) : p.key.value) : (p.key.name ?? String(p.key.value)));
  const isG = n => n?.type === 'MemberExpression' && n.object.name === G;
  const mods = new Map();
  const visit = (e, owner) => {
    if (e.type === 'SequenceExpression') return e.expressions.forEach(x => visit(x, owner));
    if (e.type === 'AssignmentExpression' && isG(e.left)) {
      const k = keyOf(e.left);
      if (!mods.has(k)) mods.set(k, { node: owner || e, value: e.right });
      return;
    }
    if (e.type === 'CallExpression' && /Function/.test(e.callee.type) && e.callee.body.type === 'BlockStatement') {
      for (const s of e.callee.body.body) if (s.type === 'ExpressionStatement') visit(s.expression, e);
    }
  };
  for (const s of stmts) if (s.type === 'ExpressionStatement') visit(s.expression, null);
  // var G = {BUILT: ...} (compilaciones de antes del 31-10) también vale
  return { G, mods, keyOf, keyName };
}

// ---- intérprete de expresiones constantes ----
class Unknown extends Error {}
const FN = Symbol('función');
function evaluator(b, st, Gval) {
  const ev = (n, env) => {
    switch (n.type) {
      case 'Literal': return n.value;
      case 'TemplateLiteral': return n.quasis.map((q, i) => q.value.cooked + (i < n.expressions.length ? ev(n.expressions[i], env) : '')).join('');
      case 'ArrayExpression': return n.elements.flatMap(e => (e.type === 'SpreadElement' ? ev(e.argument, env) : [ev(e, env)]));
      case 'ObjectExpression': {
        const o = {};
        for (const p of n.properties) {
          if (p.type === 'SpreadElement') { Object.assign(o, ev(p.argument, env)); continue; }
          const k = st.keyName(p);
          if (p.kind !== 'init' || p.method) { o[k] = FN; continue; }
          try { o[k] = ev(p.value, env); } catch (e) { if (e instanceof Unknown) o[k] = FN; else throw e; }
        }
        return o;
      }
      case 'UnaryExpression': {
        const v = ev(n.argument, env);
        if (n.operator === '!') return !v;
        if (n.operator === '-') return -v;
        if (n.operator === '+') return +v;
        throw new Unknown(n.operator);
      }
      case 'BinaryExpression': {
        const x = ev(n.left, env), y = ev(n.right, env);
        switch (n.operator) { case '+': return x + y; case '-': return x - y; case '*': return x * y; case '/': return x / y; }
        throw new Unknown(n.operator);
      }
      case 'ConditionalExpression': return ev(n.test, env) ? ev(n.consequent, env) : ev(n.alternate, env);
      case 'Identifier': {
        if (n.name === 'undefined') return undefined;
        if (n.name === st.G) return Gval();
        if (n.name in env) return env[n.name]();
        throw new Unknown(n.name);
      }
      case 'ArrowFunctionExpression': case 'FunctionExpression': return { [FN]: n, env };
      case 'NewExpression':
        if (n.callee.name === 'Set') return new Set(ev(n.arguments[0], env));
        throw new Unknown('new');
      case 'MemberExpression': {
        const o = ev(n.object, env);
        const k = n.computed && !b.isStr(n.property) ? ev(n.property, env) : st.keyOf(n);
        if (o == null || !(k in Object(o))) throw new Unknown(String(k));
        return o[k];
      }
      case 'CallExpression': {
        if (b.isStr(n)) return b.str(n.arguments[0].value);
        const args = n.arguments.map(a => ev(a, env));
        if (n.callee.type === 'MemberExpression') {
          const k = st.keyOf(n.callee);
          if (n.callee.object.name === 'Math' && k === 'round') return Math.round(args[0]);
          if (n.callee.object.name === 'Object' && k === 'assign') return Object.assign(...args);
          throw new Unknown(String(k));
        }
        return apply(ev(n.callee, env), args);
      }
      default: throw new Unknown(n.type);
    }
  };
  const apply = (f, args) => {
    const fn = f?.[FN];
    if (!fn || fn.body.type === 'BlockStatement') throw new Unknown('llamada');
    const env = Object.create(f.env);
    fn.params.forEach((p, i) => {
      const id = p.type === 'AssignmentPattern' ? p.left : p;
      const v = args[i] !== undefined ? args[i] : p.type === 'AssignmentPattern' ? ev(p.right, f.env) : undefined;
      env[id.name] = () => v;
    });
    return ev(fn.body, env);
  };
  return ev;
}

// const locales de un IIFE como entorno perezoso (nombre → valor), en orden
function locals(iife, ev) {
  const env = Object.create(null), order = [];
  for (const s of iife.callee.body.body) {
    if (s.type !== 'VariableDeclaration') continue;
    for (const d of s.declarations) {
      if (d.id.type !== 'Identifier' || !d.init) continue;
      let done = false, val;
      env[d.id.name] = () => { if (!done) { val = ev(d.init, env); done = true; } return val; };
      order.push(d);
    }
  }
  return { env, order };
}
function tryLocal(env, name) { try { return env[name](); } catch (e) { if (e instanceof Unknown) return undefined; throw e; } }

// ---- texto decodificado de un trozo del bundle ----
function decodedText(b, node) {
  const reps = [];
  const alias = d => d.init?.type === 'Identifier' && b.aliases.has(d.init.name);
  walk(node, n => {
    if (b.isStr(n)) reps.push([n.start, n.end, JSON.stringify(b.str(n.arguments[0].value))]);
    else if (n.type === 'VariableDeclaration') {
      const keep = n.declarations.filter(d => !alias(d));
      if (!keep.length) reps.push([n.start, n.end, '']);
      else if (keep.length < n.declarations.length) n.declarations.forEach((d, i) => { if (alias(d)) reps.push([d.start, n.declarations[i + 1]?.start ?? d.end, '']); });
    }
  });
  reps.sort((x, y) => x[0] - y[0] || y[1] - x[1]);
  let out = '', p = node.start;
  for (const [s, e, r] of reps) { if (s < p) continue; out += b.src.slice(p, s) + r; p = e; }
  return out + b.src.slice(p, node.end);
}

// Huella estable entre compilaciones: el ofuscador cambia nombres, comillas y `["x"]` frente a `.x`; eso no cuenta.
function canonical(code) {
  const toks = [...tokenizer(code, OPTS)], o = [];
  for (let i = 0; i < toks.length; i++) {
    const t = toks[i], l = t.type.label;
    if (l === '[' && o.length && /[\w$)\]]$/.test(o[o.length - 1])) {           // x["y"] y x[("y")] → x.y
      let j = i + 1, par = 0;
      while (toks[j].type.label === '(') { j++; par++; }
      if (toks[j].type.label === 'string' && /^[A-Za-z_$][\w$]*$/.test(toks[j].value)) {
        let k = j + 1, cl = 0;
        while (cl < par && toks[k].type.label === ')') { k++; cl++; }
        if (cl === par && toks[k].type.label === ']') { o.push('.', toks[j].value); i = k; continue; }
      }
    }
    if (l === 'string') o.push(JSON.stringify(t.value));
    else if (l === 'num') o.push(String(t.value));
    else if (l === 'name' && /^(a0)?_0x/.test(t.value)) o.push('v');
    else o.push(code.slice(t.start, t.end));
  }
  return o.join(' ');
}
const fingerprint = code => crypto.createHash('sha256').update(canonical(code)).digest('hex').slice(0, 12);

// ---- escritura en el formato que leen build/*.py ----
const J = v => JSON.stringify(v);
const SQ = s => "'" + String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
const HEAD = n => `/* ${n}: generado por build/extract_game.mjs a partir de js/app.min.js de PokéSurvivor. No editar a mano. */\n`;
const plain = v => JSON.parse(JSON.stringify(v, (k, x) => (typeof x === 'symbol' ? undefined : x)));

function movesFile(b, st, ev) {
  const mod = st.mods.get('Moves');
  need(mod && mod.node.type === 'CallExpression', 'no aparece el módulo Moves');
  const iife = mod.node, { env, order } = locals(iife, ev);
  const out = {};
  const objs = order.map(d => ({ d, v: tryLocal(env, d.id.name) })).filter(x => x.v !== undefined);
  const has = (o, ...ks) => o && typeof o === 'object' && ks.every(k => k in o);
  const pick = (name, test) => {
    const hit = objs.filter(x => test(x.v));
    need(hit.length === 1, `Moves: ${name} aparece ${hit.length} veces`);
    out[name] = hit[0];
  };
  pick('LADDERS', v => has(v, 'projectile', 'melee') && Array.isArray(v.melee));
  pick('EVO_MODS', v => has(v, 'projectile', 'melee') && !Array.isArray(v.melee) && has(v.melee, 't', 'm'));
  pick('RAW', v => Array.isArray(v) && v.length > 100 && has(v[0], 'id', 'kind', 'type'));
  pick('PHYSICAL', v => v instanceof Set && v.has('tackle'));
  pick('EVO', v => has(v, 'tackle') && typeof v.tackle === 'string');
  pick('NEED_NAME', v => has(v, 'hp', 'atk') && typeof v.atk === 'string');
  const byDecl = new Map(Object.entries(out).map(([k, x]) => [x.d, k]));
  const fmt = {
    LADDERS: v => `{\n${Object.entries(v).map(([k, l]) => `    ${J(k)}: [\n${l.map(x => '      ' + J(x)).join(',\n')}\n    ]`).join(',\n')}\n  };`,
    EVO_MODS: v => `{\n${Object.entries(v).map(([k, x]) => `    ${J(k)}: ${J(x)}`).join(',\n')}\n  };`,
    RAW: v => `[\n${v.map(x => '    ' + J(x)).join(',\n')}\n  ];`,
    PHYSICAL: v => `new Set([${[...v].map(SQ).join(', ')}]);`,
    EVO: v => `{\n${Object.entries(v).map(([k, x]) => `    ${SQ(k)}: ${SQ(x)}`).join(',\n')}\n  };`,
    NEED_NAME: v => `{ ${Object.entries(v).map(([k, x]) => `${k}: ${SQ(x)}`).join(', ')} };`,
  };
  const lines = [];
  for (const s of iife.callee.body.body) {
    if (s.type === 'VariableDeclaration') {
      for (const d of s.declarations) {
        if (b.aliases.has(d.init?.name)) continue;
        const name = byDecl.get(d);
        if (name) lines.push(`  const ${name} = ${fmt[name](plainMove(out[name].v))}`);
        else lines.push(`  ${s.kind} ${decodedText(b, d)};`);
      }
    } else lines.push('  ' + decodedText(b, s));
  }
  let text = lines.join('\n');
  for (const [name, x] of Object.entries(out)) text = text.replaceAll(x.d.id.name, name);
  text = text.replaceAll(st.G, 'G');
  return HEAD('moves') + `(() => {\n${text}\n})();\n`;
}
const plainMove = v => (v instanceof Set ? v : plain(v));

function abilityFxFile(b, st, ev) {
  const mod = st.mods.get('AbilityFX');
  need(mod?.value.type === 'CallExpression', 'no aparece el módulo AbilityFX');
  const { env, order } = locals(mod.value, ev);
  const fx = order.map(d => d.init).find(i => i?.type === 'ObjectExpression' && i.properties.length > 50);
  need(fx, 'AbilityFX: no aparece la tabla de habilidades');
  const rows = [];
  let lost = 0;
  for (const p of fx.properties) {
    const id = st.keyName(p);
    let v = null;
    try { v = ev(p.value, env); } catch (e) { if (!(e instanceof Unknown)) throw e; }
    if (typeof v?.d !== 'string') { lost++; console.error('aviso: habilidad sin descripción legible:', id); continue; }
    rows.push(`    ${SQ(id)}: { d: ${SQ(v.d)}${v.plus === true ? ', plus: true' : ''} }`);
  }
  need(rows.length > 50 && lost <= 5, `AbilityFX: ${lost} habilidades sin descripción`);
  return HEAD('ability-fx') + `  const FX = {\n${rows.join(',\n')}\n  };\n  FX['pure-power'] = FX['huge-power'];\n`;
}

function iconsFile(st, ev) {
  const mod = st.mods.get('Icons');
  need(mod?.value.type === 'CallExpression', 'no aparece el módulo Icons');
  const { env, order } = locals(mod.value, ev);
  const vals = order.map(d => tryLocal(env, d.id.name)).filter(v => v && typeof v === 'object' && !(FN in v));
  const ui = vals.find(v => v.heart?.pal && v.heart?.rows);
  const glyph = vals.filter(v => Object.values(v).length > 5 && Object.values(v).every(x => Array.isArray(x) && x.every(r => typeof r === 'string')));
  const typeG = glyph.find(v => 'fire' in v && 'water' in v), kindG = glyph.find(v => v !== typeG);
  need(ui && typeG && kindG, 'Icons: no aparecen las tablas de iconos');
  const row = (k, r) => `    ${k}: [${r.map(SQ).join(', ')}],`;
  const uiRows = Object.entries(ui).filter(([, d]) => d.pal && d.rows).map(([k, d]) =>
    `    ${k}: { pal: { ${Object.entries(d.pal).map(([c, h]) => `${c}: ${SQ(h)}`).join(', ')} }, rows: [${d.rows.map(SQ).join(', ')}]${d.outline ? ', outline: true' : ''} },`);
  return HEAD('icons') + `  const UI = {\n${uiRows.join('\n')}\n  };\n  const TYPE_GLYPH = {\n${Object.entries(typeG).map(([k, r]) => row(k, r)).join('\n')}\n  };\n  const KIND_GLYPH = {\n${Object.entries(kindG).map(([k, r]) => row(k, r)).join('\n')}\n  };\n`;
}

function main() {
  const [inp, outDir, arg] = process.argv.slice(2);
  need(inp && outDir, 'uso: node build/extract_game.mjs <app.min.js> <carpeta>');
  const b = open(fs.readFileSync(inp, 'utf8'));
  const st = structure(b);
  if (outDir === '--dump') {
    need(st.mods.has(arg), `no aparece G.${arg}`);
    process.stdout.write(decodedText(b, st.mods.get(arg).node).replaceAll(st.G, 'G') + '\n');
    return;
  }
  if (outDir === '--hooks') {
    const hooks = {};
    for (const m of HOOK_MODULES) {
      need(st.mods.has(m), `no aparece el módulo del Consejero ${m}`);
      hooks[m] = fingerprint(decodedText(b, st.mods.get(m).node));
    }
    process.stdout.write(JSON.stringify(hooks) + '\n');
    return;
  }
  let gcache = null;
  const ev = evaluator(b, st, () => (gcache ??= { U: ev(st.mods.get('U').value, Object.create(null)) }));
  const lit = name => { need(st.mods.has(name), `no aparece G.${name}`); return plain(ev(st.mods.get(name).value, Object.create(null))); };
  fs.mkdirSync(outDir, { recursive: true });
  const put = (name, text) => fs.writeFileSync(path.join(outDir, name), text);

  const DEX = lit('DEX');
  need(Array.isArray(DEX) && DEX.length > 900 && DEX[0].dex === 1, 'G.DEX no tiene la forma esperada');
  put('js_data_pokedex.js', HEAD('pokedex') + DEX.map(d => '  ' + J(d) + ',').join('\n') + '\n');

  const ABIL = lit('ABIL'), DEX_ABIL = lit('DEX_ABIL');
  put('js_data_abilities.js', HEAD('abilities') + Object.entries(ABIL).map(([k, v]) => `  ${J(k)}:${J(v)},`).join('\n') + '\n' +
    Object.entries(DEX_ABIL).map(([k, v]) => `  ${k}:${J(v)},`).join('\n') + '\n');

  const NATURES = lit('NATURES');
  need(NATURES.length === 25, 'G.NATURES no tiene 25 naturalezas');
  put('js_data_natures.js', HEAD('natures') + NATURES.map(n => '  ' + J(n) + ',').join('\n') + '\n');

  const tbl = v => Object.entries(v).map(([k, x]) => `  ${J(k)}:${J(x)}`).join(',\n');
  put('js_data_tms.js', HEAD('tms') + `G.TM_MOVES = {\n${tbl(lit('TM_MOVES'))}\n};\nG.TM_PRICE = {\n${tbl(lit('TM_PRICE'))}\n};\n`);

  const META = lit('SPRITE_META');
  put('js_data_sprites-meta.js', HEAD('sprites-meta') + Object.entries(META).map(([k, v]) => `  ${k}: ${J(v)},`).join('\n') + '\n');

  const types = st.mods.get('Types');
  need(types?.value.type === 'CallExpression', 'no aparece G.Types');
  const tl = locals(types.value, ev);
  const CHART = tl.order.map(d => tryLocal(tl.env, d.id.name)).find(v => v?.fire && v?.normal);
  need(CHART, 'no aparece la tabla de tipos');
  put('js_data_types.js', HEAD('types') + `  const CHART = {\n${Object.entries(CHART).map(([k, v]) => `    ${k}: { ${Object.entries(v).map(([a, x]) => `${a}: ${x}`).join(', ')} },`).join('\n')}\n  };\n`);

  const en = [];
  walk(b.stmt, n => {
    if (n.type !== 'CallExpression' || n.callee.type !== 'MemberExpression' || n.arguments[0]?.type !== 'ObjectExpression') return;
    const recv = n.callee.object;                                     // G.I18n.add({...}): puede haber varias llamadas
    if (st.keyOf(n.callee) === 'add' && recv.type === 'MemberExpression' && recv.object.name === st.G && st.keyOf(recv) === 'I18n') en.push(n.arguments[0]);
  });
  need(en.length >= 1, 'no aparece el diccionario inglés');
  const pairs = {};
  for (const o of en) Object.assign(pairs, plain(ev(o, Object.create(null))));
  need(Object.keys(pairs).length > 500, 'diccionario inglés demasiado corto');
  put('js_data_lang-en.js', HEAD('lang-en') + `G.I18n.add({\n${Object.entries(pairs).filter(([, v]) => typeof v === 'string').map(([k, v]) => `  ${J(k)}: ${J(v)},`).join('\n')}\n});\n`);

  put('js_data_moves.js', movesFile(b, st, ev));
  put('js_data_ability-fx.js', abilityFxFile(b, st, ev));
  put('js_ui_icons.js', iconsFile(st, ev));

  const rules = {};
  for (const m of RULE_MODULES) {
    need(st.mods.has(m), `no aparece el módulo de reglas ${m}`);
    rules[m] = fingerprint(decodedText(b, st.mods.get(m).node));
  }
  put('RULES.sha', JSON.stringify(rules, null, 1) + '\n');
  console.log(`extraído: ${DEX.length} Pokémon, ${Object.keys(pairs).length} textos en inglés, ${Object.keys(rules).length} módulos de reglas`);
}

main();
