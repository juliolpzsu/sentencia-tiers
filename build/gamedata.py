"""Carga de los datos del juego (copias de js/data de PokéSurvivor en data/game) a estructuras Python.
Compartido por rank.py y gen.py.
"""
import json, re, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, 'data', 'game')
def rd(name): return open(os.path.join(GAME, name), encoding='utf-8', errors='ignore').read()

def js_obj_to_json(txt):
    txt = re.sub(r'//[^\n]*', '', txt)
    txt = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', txt)
    txt = txt.replace("'", '"')
    txt = re.sub(r',\s*([}\]])', r'\1', txt)
    return json.loads(txt)

def block(txt, start, end):
    i = txt.index(start) + len(start)
    return txt[i:txt.index(end, i)]

# ---- Pokédex ----
DEX = {}
for m in re.finditer(r'^\s*(\{"dex":.*\}),?\s*$', rd('js_data_pokedex.js'), re.M):
    d = json.loads(m.group(1)); DEX[d['dex']] = d

# ---- habilidades ----
_ab = rd('js_data_abilities.js')
DEX_ABIL = {int(m.group(1)): json.loads(m.group(2)) for m in re.finditer(r'^\s*(\d+):(\[.*\]),?\s*$', _ab, re.M)}
ABIL_NAMES = {m.group(1): json.loads(m.group(2)) for m in re.finditer(r'^\s*"([a-z0-9-]+)":(\[.*\]),?\s*$', _ab, re.M)}  # [es,en,fr,it,zh,zh]

# ---- naturalezas ----
NATURES = [json.loads(m.group(1)) for m in re.finditer(r'^\s*(\{"id":.*\}),?\s*$', rd('js_data_natures.js'), re.M)]
NAT_BY = {n['id']: n for n in NATURES}

# ---- MT ----
_tm = rd('js_data_tms.js')
TM_MOVES = json.loads('{' + block(_tm, 'G.TM_MOVES = {', '};') + '}')
TM_PRICE = json.loads('{' + block(_tm, 'G.TM_PRICE = {', '};') + '}')
TM_OF = defaultdict(list)
for mv, lst in TM_MOVES.items():
    for d in lst: TM_OF[d].append(mv)

# ---- movimientos ----
_mv = rd('js_data_moves.js')
LADDERS = js_obj_to_json('{' + block(_mv, 'const LADDERS = {', '\n  };') + '}')
RAW = js_obj_to_json('[' + block(_mv, 'const RAW = [', '\n  ];') + ']')
EVO_MODS = js_obj_to_json('{' + block(_mv, 'const EVO_MODS = {', '\n  };') + '}')
PHYSICAL = set(re.findall(r"'([a-z-]+)'", block(_mv, 'const PHYSICAL = new Set([', ']);')))
EVO = {}
for a, b in re.findall(r"'([a-z-]+)':\s*'([a-z]+)'", block(_mv, 'const EVO = {', '\n  };')): EVO[a] = b
NEED_NAME = dict(re.findall(r"(\w+): '([^']+)'", block(_mv, 'const NEED_NAME = {', '};')))
MULT = ['dmg', 'cd', 'speed', 'radius', 'dur', 'amount', 'arc', 'width', 'spread', 'life', 'size', 'rate', 'pull', 'knock', 'stun', 'charge']
ADD = ['count', 'pierce', 'stacks', 'bounce']
def apply_mods(s, m):
    for k, v in m.items():
        if k in MULT and s.get(k) is not None: s[k] *= v
        elif k in ADD: s[k] = s.get(k, 0) + v
        else: s[k] = v
MOVES = {}
POOL = defaultdict(list)
for m in RAW:
    m = dict(m)
    if m['kind'] == 'melee':
        m['dmg'] = round(m['dmg'] * 1.2); m['radius'] = round(m['radius'] * 1.25)
        if m.get('arc'): m['arc'] = min(3, round(m['arc'] * 1.25, 2))
    if m['kind'] in ('projectile', 'homing', 'bounce'):
        m.setdefault('count', 1); m.setdefault('spread', 0.12)
    m['cat'] = None if m['kind'] == 'buff' else ('physical' if m['id'] in PHYSICAL else 'special')
    MOVES[m['id']] = m
    POOL[m['type']].append(m['id'])
def maxed(mid):
    d = MOVES[mid]; s = dict(d)
    for up in LADDERS[d['kind']]: apply_mods(s, up['m'])
    if d['kind'] != 'buff' and d['kind'] in EVO_MODS: apply_mods(s, EVO_MODS[d['kind']]['m'])
    return s
def natural_pool(dex):
    ids = set(POOL['normal'])
    for t in DEX[dex]['types']: ids |= set(POOL[t])
    return ids
def tm_extra(dex):
    nat = natural_pool(dex)
    return sorted(mv for mv in TM_OF.get(dex, []) if mv in MOVES and mv not in nat)

# ---- sprites: tamaño del jugador ----
META = {int(m.group(1)): json.loads(m.group(2)) for m in re.finditer(r'^\s*(\d+): (\{.*\}),?\s*$', rd('js_data_sprites-meta.js'), re.M)}
PX, PLAYER_R, BIG_H, BIG_K = 2, 18, 36, 0.4
def clamp(x, a, b): return max(a, min(b, x))
def player_radius(dex):
    mt = META.get(dex, {}).get('a', {}).get('Idle')
    w = mt['w'] if mt else 32
    h = max(mt['ay'], mt['w'] * 0.55) if mt else 24
    scale = 1 if h <= BIG_H else round((BIG_H + (h - BIG_H) * BIG_K) / h * 16) / 16
    return min(PLAYER_R, clamp(w * 0.22, 5, 26) * PX * scale), scale

# ---- tabla de tipos suavizada ----
_ty = rd('js_data_types.js')
CHART = {}
for row in re.finditer(r"^\s*(\w+):\s*\{([^}]*)\}", block(_ty, 'const CHART = {', '\n  };'), re.M):
    CHART[row.group(1)] = {k: float(v) for k, v in re.findall(r'(\w+):\s*([\d.]+)', row.group(2))}
SOFT = {2.0: 1.6, 0.5: 0.6, 0.0: 0.3}
def tmult(atk, defs):
    m = 1.0
    for t in defs:
        v = CHART.get(atk, {}).get(t)
        if v is not None: m *= SOFT[v]
    return clamp(m, 0.3, 2.4)
def guard(d): return clamp((75 / max(5, d or 75)) ** 0.35, 0.78, 1.25)
TYPES = ['normal', 'fire', 'water', 'grass', 'electric', 'ice', 'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy']

# ---- SurvivorTiers (ranking en hordas, para la viabilidad hasta el minuto 30) ----
ST = {d['dex']: d for d in json.load(open(os.path.join(GAME, 'survivortiers-index.json'), encoding='utf-8'))}

# ---- diccionario inglés del juego (clave: texto español) ----
def _parse_dict(txt):
    out = {}
    pat = re.compile(r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")\s*:\s*('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")""")
    for m in pat.finditer(txt):
        k = m.group(1)[1:-1].replace("\\'", "'").replace('\\"', '"')
        v = m.group(2)[1:-1].replace("\\'", "'").replace('\\"', '"')
        out.setdefault(k, v)
    return out
EN = _parse_dict(rd('js_data_lang-en.js'))
def _pattern_dict(d):
    pats = []
    for k, v in d.items():
        if '{x}' in k:
            rx = re.escape(k).replace(r'\{x\}', '(.+?)')
            pats.append((re.compile('^' + rx + '$'), v))
    return pats
EN_PATS = _pattern_dict(EN)
def en(text):
    """Traduce un texto español del juego al inglés (frase exacta, patrón con {x}, o se deja igual)."""
    if text in EN: return EN[text]
    for rx, v in EN_PATS:
        m = rx.match(text)
        if m: return v.replace('{x}', en(m.group(1)))
    return text
TYPE_ES = {'normal': 'Normal', 'fire': 'Fuego', 'water': 'Agua', 'grass': 'Planta', 'electric': 'Eléctrico', 'ice': 'Hielo', 'fighting': 'Lucha', 'poison': 'Veneno',
           'ground': 'Tierra', 'flying': 'Volador', 'psychic': 'Psíquico', 'bug': 'Bicho', 'rock': 'Roca', 'ghost': 'Fantasma', 'dragon': 'Dragón', 'dark': 'Siniestro',
           'steel': 'Acero', 'fairy': 'Hada'}
TYPE_EN = {k: (en(v) if k != 'normal' else 'Normal') for k, v in TYPE_ES.items()}
