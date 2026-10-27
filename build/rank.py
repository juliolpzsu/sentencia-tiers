"""Ranking de los 966 Pokémon de PokéSurvivor para la Sentencia de Arceus.

Genera data/ranking.json: la guía que después usa gen.py para la web.
Reglas replicadas del código del juego (JPTER78/pokesurvivor, commit del 23-10-2026):
  - judgment.js (Arceus, pilares, legendarios cada 5 s, tope suave de velocidad 130)
  - enemy.js / combat.js (aturdir ×0,35 en jefes, remolino ×0,25, empuje ×0, frenazo ×1, veneno/quemadura 1,5 fijo)
  - player.js / stats.js / types.js (defensas, tabla suavizada, monotipo +20 %)
  - ability-fx.js (habilidades) · moves.js (escalera de mejoras y evoluciones)
Dos variantes por Pokémon:
  base  habilidad por defecto (la primera), naturaleza neutra, sólo sus ataques naturales
  shop  Tienda Kecleon: mejor habilidad (Cápsula / Cápsula Oculta), mejor naturaleza (Menta) y MT
Uso: python -I rank.py
"""
import json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata import *

# Pool de legendarios que acuden a la Sentencia (todos los `leg` con sprite, menos Arceus).
LEGS = [DEX[d] for d in sorted(DEX) if DEX[d].get('leg') and d != 493 and d in META]
LEG_ATK = defaultdict(int)
for L in LEGS: LEG_ATK[L['types'][0]] += 1

# ---------------- habilidades ----------------
ABSORB = {'water-absorb': 'water', 'storm-drain': 'water', 'volt-absorb': 'electric', 'lightning-rod': 'electric', 'motor-drive': 'electric',
          'flash-fire': 'fire', 'well-baked-body': 'fire', 'sap-sipper': 'grass', 'earth-eater': 'ground', 'dry-skin': 'water'}
def in_mul(ab, atype, cls, defs):
    k, dodge = 1.0, 0.0
    if ab in ABSORB and ABSORB[ab] == atype: return 0.0, 0.0
    if ab == 'dry-skin' and atype == 'fire': k = 1.25
    if ab == 'levitate' and atype == 'ground': k = 0.3
    if ab == 'thick-fat' and atype in ('fire', 'ice'): k = 0.6
    if ab in ('heatproof', 'water-bubble', 'water-veil') and atype == 'fire': k = 0.5
    if ab in ('multiscale', 'shadow-shield'): k = 0.8
    if ab in ('filter', 'solid-rock', 'prism-armor') and tmult(atype, defs) > 1: k = 0.75
    if ab == 'fur-coat' and cls == 'p': k = 0.6
    if ab == 'fluffy' and cls == 'p': k = 0.7
    if ab == 'ice-scales' and cls == 's': k = 0.6
    if ab in ('shell-armor', 'battle-armor', 'pressure', 'unaware'): k = 0.92
    if ab == 'intimidate' and cls == 'p': k = 0.88
    if ab == 'overcoat' and cls == 's': k = 0.95
    if ab == 'soundproof' and cls == 's': k = 0.9
    if ab == 'big-pecks' and cls == 'p': k = 0.92
    if ab == 'bulletproof' and cls == 's': k = 0.85
    if ab == 'magic-bounce' and cls == 's': k = 0.85; dodge = 0.1
    if ab in ('friend-guard', 'unnerve'): k = 0.94
    if ab == 'wonder-guard': k = 1.5 if tmult(atype, defs) > 1 else 0.35
    if ab == 'stance-change': k = 0.9
    if ab == 'moody': k = 0.975
    if ab == 'no-guard': k = 1.1
    if ab == 'telepathy': dodge = 0.08
    if ab in ('anticipation', 'forewarn'): dodge = 0.06
    return k, dodge
REGEN_AB = {'regenerator': 0.006, 'natural-cure': 0.003, 'healer': 0.003, 'shed-skin': 0.004}
HEALMUL = {'gluttony': 1.4, 'harvest': 1.3}
# Habilidades con efecto propio en el juego (las demás dan +8 % con el tipo principal). Las `plus` suman ambos.
PLUS = {'keen-eye', 'frisk', 'magnet-pull', 'sticky-hold', 'illuminate', 'sand-veil', 'snow-cloak', 'gluttony', 'harvest', 'unnerve', 'infiltrator', 'telepathy',
        'anticipation', 'forewarn', 'weak-armor', 'steadfast', 'rattled', 'hydration', 'overcoat', 'shed-skin', 'natural-cure', 'healer', 'leaf-guard', 'mold-breaker',
        'damp', 'rivalry', 'synchronize', 'prankster', 'early-bird', 'shield-dust', 'sweet-veil', 'unburden', 'unaware', 'defiant', 'competitive', 'soundproof',
        'big-pecks', 'water-veil', 'pickpocket', 'analytic', 'klutz', 'hyper-cutter', 'contrary', 'quick-feet', 'bulletproof', 'magic-bounce', 'friend-guard',
        'stench', 'justified', 'aftermath', 'moody', 'tangled-feet', 'skill-link', 'protosynthesis', 'zen-mode'}
OWN_FX = {'overgrow','blaze','torrent','swarm','steelworker','steely-spirit','dragons-maw','transistor','water-bubble','technician','huge-power','hustle','guts','adaptability','protean',
          'sheer-force','serene-grace','tough-claws','reckless','iron-fist','strong-jaw','mega-launcher','sharpness','punk-rock','tinted-lens','scrappy','sand-force','solar-power','sniper',
          'super-luck','compound-eyes','moxie','chilling-neigh','grim-neigh','beast-boost','speed-boost','swift-swim','chlorophyll','sand-rush','slush-rush','run-away','drought',
          'orichalcum-pulse','drizzle','sand-stream','snow-warning','rain-dish','ice-body','dry-skin','levitate','thick-fat','heatproof','water-absorb','storm-drain','volt-absorb',
          'lightning-rod','motor-drive','flash-fire','well-baked-body','sap-sipper','earth-eater','multiscale','shadow-shield','filter','solid-rock','prism-armor','fur-coat','fluffy',
          'ice-scales','shell-armor','battle-armor','intimidate','pressure','sturdy','regenerator','magic-guard','stamina','limber','own-tempo','oblivious','inner-focus','clear-body',
          'white-smoke','full-metal-body','insomnia','vital-spirit','static','flame-body','poison-point','cute-charm','effect-spore','rough-skin','iron-barbs','poison-touch','pickup',
          'honey-gather','truant','slow-start','defeatist','wonder-guard','schooling','stance-change','imposter','pure-power','libero','plus','minus','no-guard','anger-point','cursed-body'} | PLUS
def is_generic(ab): return ab not in OWN_FX or ab in PLUS

def out_mul(ab, m, types):
    k = 1.0; t = m['type']; c = m['cat']; base = MOVES[m['id']]
    boost = {'steelworker': 'steel', 'steely-spirit': 'steel', 'dragons-maw': 'dragon', 'transistor': 'electric'}
    if ab in boost and t == boost[ab]: k *= 1.2
    if ab == 'water-bubble' and t == 'water': k *= 1.4
    if ab == 'technician' and base['dmg'] <= 12: k *= 1.35
    if ab in ('huge-power', 'pure-power') and c == 'physical': k *= 1.5
    if ab == 'hustle' and c == 'physical': k *= (1.25 * 5 + 0.3) / 6
    if ab == 'adaptability' and t in types: k *= 1.25
    if ab in ('protean', 'libero'): k *= 1.12
    if ab == 'sheer-force' and (base.get('burn') or base.get('poison') or base.get('slow') or base.get('knock')): k *= 1.25
    if ab == 'tough-claws' and m['kind'] in ('melee', 'dash'): k *= 1.25
    if ab == 'reckless' and m['kind'] == 'dash': k *= 1.25
    if ab == 'iron-fist' and 'punch' in m['id']: k *= 1.25
    if ab == 'strong-jaw' and re.search(r'bite|fang|crunch|jaw', m['id']): k *= 1.3
    if ab == 'mega-launcher' and re.search(r'pulse|aura-sphere', m['id']): k *= 1.3
    if ab == 'sharpness' and re.search(r'cut|slash|blade|razor|scissor|sword', m['id']): k *= 1.3
    if ab == 'punk-rock' and re.search(r'voice|buzz|boom|noise|sing|echo|uproar|snarl', m['id']): k *= 1.3
    if ab == 'sniper': k *= 1.3 / 1.15
    if ab == 'super-luck': k *= 1.2 / 1.15
    if ab == 'compound-eyes': k *= 1.18 / 1.15
    if ab in ('moxie', 'chilling-neigh', 'grim-neigh', 'beast-boost'): k *= 1.15
    if ab == 'mold-breaker': k *= 1.12
    if ab == 'analytic': k *= 1.07
    if ab == 'defeatist': k *= 1.05
    if ab == 'truant': k *= 1.35 / 1.6
    if ab == 'schooling': k *= 1.4
    if ab == 'stance-change': k *= 1.1
    if ab == 'no-guard': k *= 1.15
    if ab in ('plus', 'minus') and c == 'special': k *= 1.1
    if ab == 'hyper-cutter' and c == 'physical': k *= 1.06
    if ab == 'skill-link' and ((m.get('count') or 1) > 2 or m.get('bounce')): k *= 1.25
    if ab == 'zen-mode' and c == 'special': k *= 1.1
    if ab == 'guts' and c == 'physical': k *= 1.1
    pinch = {'overgrow': 'grass', 'blaze': 'fire', 'torrent': 'water', 'swarm': 'bug'}
    if ab in pinch and t == pinch[ab]: k *= 1.08
    if is_generic(ab) and t == types[0]: k *= 1.08
    if ab == 'tinted-lens':
        ks = [tmult(t, L['types']) for L in LEGS]; k *= sum(1.0 if x < 1 else x for x in ks) / sum(ks)
    return k

# ---------------- constantes del modelo ----------------
UPG_SPD, UPG_HP, CARD_SPD, CARD_HP = 1.24, 80, 1.07 ** 8, 20 * 15   # mejoras al máximo y cartas típicas al minuto 30
CD_MUL = 0.76 * 0.92 ** 10                                        # Reflejos al máximo + 10 cartas
def cap_spd(s): return s if s <= 130 else 130 + (s - 130) * 0.25
SLOW_COVER = {'beam': 1.0, 'aura': 0.95, 'nova': 0.9, 'homing': 0.85, 'meteor': 0.85, 'projectile': 0.7, 'bounce': 0.7, 'chain': 0.7,
              'cone': 0.6, 'melee': 0.5, 'mine': 0.65, 'trail': 0.4, 'orbit': 0.6, 'dash': 0.4, 'stun': 0.8, 'vortex': 0.7}
CLOSE = {'melee', 'spin', 'aura', 'dash', 'orbit', 'trail'}
def single_hits(s):
    k = s['kind']; c = s.get('count') or 1
    return {'projectile': c * 0.75, 'homing': c * 0.95, 'bounce': 1.2, 'beam': 1, 'charge': 1, 'chain': 1, 'nova': min(c, 3) * 0.6,
            'meteor': c * 0.7, 'boomerang': c * 1.6, 'spin': c, 'melee': 1, 'dash': 1, 'quake': c * 0.45, 'shove': 1, 'stun': 1,
            'cone': c * 0.7, 'mine': c * 0.4, 'orbit': c * 0.9, 'aura': 1, 'trail': 0.3, 'turret': 0, 'vortex': 0}.get(k, 1)
def move_dps(s):
    k = s['kind']
    if k == 'buff': return 0
    if k == 'turret': return s['dmg'] * s.get('count', 1) * (s['dur'] / s['rate']) / (s['cd'] / CD_MUL) * 0.35
    if k == 'vortex': return s['dmg'] * (s['dur'] / 0.4) / s['cd']
    if k == 'orbit': return s['dmg'] * s['count'] * 0.6 / 0.3 * 0.5
    if k == 'aura': return s['dmg'] / s['cd']
    return s['dmg'] * single_hits(s) / s['cd']
# Sólo lo que aguanta en la Sentencia: el ranking en hordas (llegar al minuto 30) se enseña en la ficha, pero no puntúa (decisión del 24-10-2026).
W = dict(V=0.0, T=0.36, U=0.32, A=0.10, D=0.10, S=0.08, Z=0.04)
TIERS = [(30, 'S'), (120, 'A'), (320, 'B'), (620, 'C'), (10 ** 6, 'D')]
def tier_of(pos): return next(t for lim, t in TIERS if pos <= lim)

def mon_with_nature(dex, nat):
    b = DEX[dex]; m = dict(b)
    if nat and nat['up']: m[nat['up']] = b[nat['up']] * 1.1
    if nat and nat['down']: m[nat['down']] = b[nat['down']] * 0.9
    m['atk'] = max(m['pa'], m['sa'])
    return m

LEG_TK = {}   # (type, cat) -> multiplicador medio de tus ataques contra el pool
for t in TYPES:
    for cat in ('physical', 'special'):
        LEG_TK[(t, cat)] = sum(tmult(t, L['types']) * guard(L['df'] if cat == 'physical' else L['sd']) for L in LEGS) / len(LEGS)

def raw_components(dex, ab, nat, pool, natural=None):
    """Componentes en bruto (sin normalizar) para una configuración.
    Los empates se deshacen a favor del movimiento natural (sin MT) y, después, por nombre: resultado determinista."""
    b = DEX[dex]; mon = mon_with_nature(dex, nat); types = b['types']
    natural = natural if natural is not None else pool
    pool = sorted(pool, key=lambda m: (m not in natural, m))
    tot = 0.0; by_type = defaultdict(float)
    for L in LEGS:
        at = L['types'][0]; cls = 'p' if L['pa'] >= L['sa'] else 's'
        k, dodge = in_mul(ab, at, cls, types)
        g = guard(mon['df'] if cls == 'p' else mon['sd'])
        v = tmult(at, types) * g * k * (1 - dodge)
        tot += v; by_type[at] += v
    T_mult = tot / len(LEGS)
    ehp = (b['hp'] + UPG_HP + CARD_HP) * (1.25 if ab == 'sturdy' else 1.0)
    serene = 2 if ab == 'serene-grace' else (0 if ab == 'sheer-force' else 1)
    best_slow, slow_mv = 0.0, None; stun_sc, stun_mv = 0.0, None; heal = 0.0
    for mid in pool:
        d = MOVES[mid]
        # Frenazos: sólo a distancia (Lengüetazo obliga a estar pegado a los legendarios, justo lo que no se quiere).
        if d.get('slow') and d['kind'] not in CLOSE:
            v = min(0.8, d['slow'] * serene) * SLOW_COVER.get(d['kind'], 0.6)
            if v > best_slow: best_slow, slow_mv = v, mid
        if d['kind'] == 'stun':
            s = maxed(mid); v = min(1.0, (s['stun'] * 0.35) / (s['cd'] * CD_MUL))
            if v > stun_sc: stun_sc, stun_mv = v, mid
        if mid == 'aqua-ring': heal = max(heal, 0.6)
        # (Beso Drenaje cura 1 PS por golpe: no cuenta.)
    U = 0.55 * (best_slow / 0.8) + 0.45 * stun_sc
    best_d, best_dmv = 0.0, None
    dps = {}
    for mid in pool:
        d = MOVES[mid]
        if d['kind'] == 'buff': continue
        s = maxed(mid)
        atk = mon['pa'] if d['cat'] == 'physical' else mon['sa']
        mono = 1.2 if len(types) == 1 and d['type'] == types[0] else 1.0
        v = move_dps(s) * atk * mono * LEG_TK[(d['type'], d['cat'])] * out_mul(ab, d, types) * (0.5 if d['kind'] in CLOSE else 1.0)
        dps[mid] = v
        if v > best_d and d['kind'] != 'turret': best_d, best_dmv = v, mid
    A = REGEN_AB.get(ab, 0) * 100 + heal * 3 + (1.0 if ab == 'sturdy' else 0) + (0.3 if ab in HEALMUL else 0)
    spd_mul = 1.3 if ab == 'speed-boost' else 1.08 if ab == 'run-away' else 1.0
    S = cap_spd(mon['spd'] * UPG_SPD * CARD_SPD * spd_mul)
    r, scale = player_radius(dex)
    Z = 1 / ((44 + 0.6 * r) ** 2)
    surv = ST.get(dex, {}).get('v', {}).get('s', 100)
    return dict(T=ehp / T_mult, T_mult=T_mult, ehp=ehp, by_type=dict(by_type), U=U, slow=slow_mv, slow_v=best_slow, stun=stun_mv, stun_v=stun_sc,
                heal=heal, D=best_d, dmv=best_dmv, dps=dps, A=A, S=S, Z=Z, r=r, scale=scale, surv=surv, mon=mon)

class Norm:
    """Normalización fijada con la pasada base, para comparar variantes con la misma escala."""
    def __init__(self, rows):
        self.b = {}
        for k, f in (('T', lambda r: math.log(r['T'])), ('A', lambda r: math.log1p(r['A'])), ('D', lambda r: math.log(max(1e-6, r['D']))), ('S', lambda r: r['S']), ('Z', lambda r: r['Z'])):
            vals = [f(r) for r in rows]; self.b[k] = (min(vals), max(vals), f)
    def comp(self, r):
        c = {'V': clamp((r['surv'] - 90) / 110, 0, 1), 'U': r['U']}
        for k, (lo, hi, f) in self.b.items(): c[k] = clamp((f(r) - lo) / (hi - lo), 0, 1) if hi > lo else 0
        return c
    def score(self, r):
        c = self.comp(r); return sum(W[k] * c[k] for k in W), c

# Enemigos que alcanza de media cada tipo de ataque en las hordas (para ordenar el grupo que farmea).
def farm_hits(s):
    k = s['kind']; c = s.get('count') or 1; pi = s.get('pierce') or 0
    return {'projectile': c * (0.9 + 0.6 * pi), 'homing': c, 'bounce': 3, 'beam': 3, 'charge': 3, 'chain': max(c, 3), 'nova': c * 0.7,
            'meteor': c * 1.5, 'boomerang': c * 2, 'spin': c * 2, 'melee': 2, 'dash': 2, 'quake': c, 'shove': 3, 'stun': 2,
            'cone': c * 0.8, 'mine': c * 0.6, 'orbit': c * 1.2, 'aura': 3, 'trail': 1.5, 'vortex': 4}.get(k, 1)
def farm_dps(s):
    if s['kind'] in ('buff', 'turret'): return 0
    if s['kind'] == 'vortex': return s['dmg'] * (s['dur'] / 0.4) / s['cd'] * 2
    if s['kind'] == 'orbit': return s['dmg'] * s['count'] * 0.6 / 0.3 * 0.5 * 2
    if s['kind'] == 'aura': return s['dmg'] / s['cd'] * 3
    return s['dmg'] * farm_hits(s) / s['cd']

# ---------------- la build ----------------
BUFF_FOR = {'physical': 'swords-dance', 'special': 'nasty-plot'}
def choose_build(dex, ab, nat, pool, raw, natural=None):
    """La build en huecos, con un motivo (código + parámetros) por movimiento (27-10-2026, como juegan los mejores):
      hueco 1  los ataques que más farmean de su lado y su potenciador, para fusionarlos en las grietas
               (hasta 4 en un grupo): lo que más explica la Sentencia es el nivel con el que llegas al minuto 30
      hueco 2  Ataque Rápido: cada embestida deja 0,3 s invulnerable (con Reflejos y Garra Rápida, sin pausa)
               contra las hordas y los legendarios que acuden (no contra Arceus)
      huecos 3-4  frenazo y aturdimiento para los legendarios (a Arceus no le afectan) y, con los huecos llenos,
               dejan de salir ataques nuevos en las cartas
    `natural`: pool sin MT; las MT solo entran como ataque claramente mejor (30 %) o como control."""
    mon = raw['mon']; side = 'special' if mon['sa'] > mon['pa'] else 'physical'
    natural = natural if natural is not None else pool
    dps = raw['dps']; chosen = []; reasons = {}
    def add(mid, code, slot, **p):
        if mid and mid not in chosen:
            chosen.append(mid); reasons[mid] = dict(code=code, slot=slot, **p)
    serene = 2 if ab == 'serene-grace' else 1
    ranked = sorted((mid for mid in dps if MOVES[mid]['kind'] not in ('turret',)), key=lambda m: -dps[m])
    far = [m for m in ranked if MOVES[m]['kind'] not in CLOSE]
    best_nat = max((dps[m] for m in (far or ranked) if m in natural), default=0)
    ranked = [m for m in ranked if m in natural or dps[m] >= best_nat * 1.3]
    far = [m for m in far if m in natural or dps[m] >= best_nat * 1.3]
    # el grupo que farmea se ordena por daño en hordas (cuántos enemigos alcanza), no contra un solo legendario
    def fd(m):
        d = MOVES[m]; atk = mon['pa'] if d['cat'] == 'physical' else mon['sa']
        return farm_dps(maxed(m)) * atk * (1.2 if len(DEX[dex]['types']) == 1 and d['type'] == DEX[dex]['types'][0] else 1.0) * out_mul(ab, d, DEX[dex]['types'])
    attacks = sorted((m for m in (far or ranked) if m != 'quick-attack'), key=lambda m: (-fd(m), m))
    # hueco 1: principal, potenciador de su lado y dos ataques más (un grupo fusionado admite 4)
    primary = attacks[0] if attacks else None
    if primary:
        d = MOVES[primary]; add(primary, 'primary', 1, kind=d['kind'], cat=d['cat'], fit=round((mon['pa'] if d['cat'] == 'physical' else mon['sa']) / mon['atk'], 2))
    buff = 'dragon-dance' if side == 'physical' and 'dragon-dance' in pool else BUFF_FOR[side]
    if buff in pool: add(buff, 'buff', 1, side=side)
    for m in attacks[1:]:
        if sum(1 for r in reasons.values() if r['slot'] == 1) >= 4: break
        if m in natural: add(m, 'second', 1, kind=MOVES[m]['kind'])
    # hueco 2: Ataque Rápido (lo aprenden todos)
    if 'quick-attack' in pool: add('quick-attack', 'dash', 2)
    # huecos 3-4: control y regeneración
    nxt = lambda: 3 + sum(1 for r in reasons.values() if r['slot'] >= 3)
    if raw['slow'] and nxt() <= 4:
        d = MOVES[raw['slow']]; pct = round(min(0.8, d['slow'] * serene) * 100)
        add(raw['slow'], 'slow', nxt(), pct=pct, left=100 - pct, kind=d['kind'])
    if raw['stun'] and nxt() <= 4:
        s_ = maxed(raw['stun']); add(raw['stun'], 'stun', nxt(), secs=round(s_['stun'] * 0.35, 2))
    if 'aqua-ring' in pool and nxt() <= 4: add('aqua-ring', 'aquaring', nxt())
    atk_moves = [m for m in chosen if MOVES[m]['kind'] != 'buff' and m != 'quick-attack']
    start = primary if primary in atk_moves else (atk_moves[0] if atk_moves else None)
    start2 = next((m for m in atk_moves if m != start and reasons[m]['slot'] == 1), None)
    bans = [m for m in ('tackle', 'body-slam', 'rapid-spin', 'hyper-voice', 'harden') if m in pool and m not in chosen][:3]
    evos = [{'move': m, 'need': EVO[m], 'needName': NEED_NAME[EVO[m]]} for m in atk_moves if m in EVO]
    spd_cards = 0
    if DEX[dex]['spd'] * UPG_SPD < 130:
        spd_cards = min(8, math.ceil(math.log(130 / (mon['spd'] * UPG_SPD)) / math.log(1.07)))
    # objetos: Garra Rápida primero (Ataque Rápido sin pausa y más daño por segundo), luego aguante
    items = ['quickclaw', 'leftovers', 'focussash']
    order = sorted(chosen, key=lambda m: (reasons[m]['slot'], chosen.index(m)))
    return dict(moves=[{'id': m, **reasons[m]} for m in order], side=side, start=start, start2=start2, bans=bans, evos=evos, spd_cards=spd_cards, items=items)

NAT_CANDIDATES = None
def nature_candidates(mon):
    weak = 'pa' if mon['sa'] > mon['pa'] else 'sa'            # el lado de ataque que no usa
    out = [None]
    for n in NATURES:
        if n['up'] in ('df', 'sd', 'spd') and n['down'] == weak: out.append(n)
    return out

def evaluate(dex, norm=None):
    b = DEX[dex]; abils = [a for a in DEX_ABIL.get(dex, [0, 0, 0])]
    base_ab = abils[0] or ''
    pool_nat = natural_pool(dex)
    raw = raw_components(dex, base_ab, None, pool_nat)
    out = dict(dex=dex, name=b['name'], nameEn=ST.get(dex, {}).get('nameEn', b['name']), types=b['types'], leg=bool(b.get('leg')), rarity=b['rarity'], gen=b['gen'], bst=b['bst'],
               stats=dict(hp=b['hp'], spd=b['spd'], pa=b['pa'], sa=b['sa'], atk=b['atk'], df=b['df'], sd=b['sd']), guard=dict(p=round(guard(b['df']), 3), s=round(guard(b['sd']), 3)),
               r=round(raw['r'], 1), scale=raw['scale'], abils=abils, hordes=dict(rank=ST.get(dex, {}).get('r', [None, '?'])[0], tier=ST.get(dex, {}).get('r', [None, '?'])[1], surv=raw['surv']),
               tm=[{'id': m, 'price': TM_PRICE.get(m, 400)} for m in tm_extra(dex)],
               incoming=dict(sorted(((t, round(v / LEG_ATK[t], 3)) for t, v in raw['by_type'].items()), key=lambda x: -x[1])))
    out['_raw_base'] = raw
    if norm is None: return out
    sc, comp = norm.score(raw)
    out['base'] = dict(score=round(sc, 4), comp={k: round(v, 3) for k, v in comp.items()}, ability=base_ab, abilitySlot=0, nature=None,
                       T_mult=round(raw['T_mult'], 3), ehp=round(raw['ehp']), S=round(raw['S']), slow=raw['slow'], slow_v=round(raw['slow_v'], 2), stun=raw['stun'], stun_v=round(raw['stun_v'], 2),
                       heal=raw['heal'], dmv=raw['dmv'], build=choose_build(dex, base_ab, None, pool_nat, raw))
    # Tienda Kecleon: mejor habilidad × mejor naturaleza, con MT
    pool_shop = pool_nat | set(m['id'] for m in out['tm'])
    best = None
    ab_opts = []
    for slot, ab in enumerate(abils):
        if not ab or (slot == 1 and ab == abils[0]): continue
        ab_opts.append((slot, ab))
    # Puntuación base con cada una de sus habilidades (naturaleza neutra, pool natural): para personalizar en la web
    # con la habilidad que le tocó a cada cuenta sin portar el modelo a JavaScript.
    out['abil_scores'] = {str(slot): round(norm.score(raw_components(dex, ab, None, pool_nat))[0], 4) for slot, ab in ab_opts}
    # y con cada naturaleza (orden de G.NATURES), en enteros ×10000: "Tu puesto" con la habilidad y la naturaleza de cada cuenta
    out['an_scores'] = {str(slot): [round(norm.score(raw_components(dex, ab, n if (n['up'] or n['down']) else None, pool_nat))[0] * 10000) for n in NATURES] for slot, ab in ab_opts}
    for slot, ab in ab_opts:
        for nat in nature_candidates(mon_with_nature(dex, None)):
            r2 = raw_components(dex, ab, nat, pool_shop, natural=pool_nat)
            s2, c2 = norm.score(r2)
            if best is None or s2 > best[0]: best = (s2, c2, slot, ab, nat, r2)
    s2, c2, slot, ab, nat, r2 = best
    bld = choose_build(dex, ab, nat, pool_shop, r2, natural=pool_nat)
    used_tm = [t for t in out['tm'] if t['id'] in [m['id'] for m in bld['moves']]]
    out['shop'] = dict(score=round(s2, 4), comp={k: round(v, 3) for k, v in c2.items()}, ability=ab, abilitySlot=slot, nature=nat['id'] if nat else None,
                       capsule=None if slot == 0 else ('caph' if slot == 2 else 'cap'),
                       T_mult=round(r2['T_mult'], 3), ehp=round(r2['ehp']), S=round(r2['S']), slow=r2['slow'], slow_v=round(r2['slow_v'], 2), stun=r2['stun'], stun_v=round(r2['stun_v'], 2),
                       heal=r2['heal'], dmv=r2['dmv'], build=bld, tms=used_tm)
    return out

def main():
    t0 = time.time()
    dexes = [d for d in sorted(DEX) if d in META]
    pre = [evaluate(d) for d in dexes]
    norm = Norm([p['_raw_base'] for p in pre])
    rows = []
    for i, d in enumerate(dexes):
        rows.append(evaluate(d, norm))
        if i % 100 == 0: print(f'  {i}/{len(dexes)}  {time.time() - t0:.0f}s', flush=True)
    for r in rows: r.pop('_raw_base', None)
    for key in ('base', 'shop'):
        order = sorted(rows, key=lambda r: -r[key]['score'])
        for i, r in enumerate(order):
            r[key]['pos'] = i + 1; r[key]['tier'] = tier_of(i + 1)
    rows.sort(key=lambda r: r['base']['pos'])
    vfile = os.path.join(GAME, 'VERSION')
    game_commit = open(vfile, encoding='utf-8').read().strip() if os.path.exists(vfile) else '5a23d49 (2026-10-23)'
    doc = dict(generated=time.strftime('%Y-%m-%d'), game_commit=game_commit, weights=W, tiers=[[lim, t] for lim, t in TIERS[:-1]] + [[966, 'D']],
               legendary_pool=[dict(dex=L['dex'], name=L['name'], types=L['types'], side='physical' if L['pa'] >= L['sa'] else 'special') for L in LEGS],
               model=dict(upgrades='Vitalidad +80, Zancada ×1,24, Reflejos ×0,76, Golpe Crítico 30 %', cards='15 Vigor, 8 Carrera, 10 Reflejos', spd_cap=130),
               pokemon=rows)
    # Orden final: empírico + modelo (blend.py). Los puestos por puntuación del modelo quedan en model_pos.
    for key in ('base', 'shop'):
        for r in rows: r[key]['model_pos'] = r[key]['pos']
    import blend
    info = blend.apply(doc, TIERS[:-1] + [(10 ** 6, 'D')])
    if info: print('mezcla empírico+modelo:', info); rows.sort(key=lambda r: r['base']['pos'])
    out = os.path.join(ROOT, 'data', 'ranking.json')
    json.dump(doc, open(out, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(f'escrito {out} ({os.path.getsize(out) // 1024} KB) en {time.time() - t0:.0f}s')
    print('\nTop 30 (base):')
    for r in rows[:30]:
        b = r['base']; s = r['shop']
        print(f"{b['pos']:>3} {r['name']:<13} {'/'.join(r['types']):<16} {b['tier']} {b['score']:.3f} | hordas {r['hordes']['tier']} #{r['hordes']['rank']} | {b['ability']} | slow {b['slow']} stun {b['stun']} | build {[m['id'] for m in b['build']['moves']]} | shop #{s['pos']} {s['ability']}/{s['nature']} {[t['id'] for t in s['tms']]}")
    print('\nTop 15 (shop):')
    for r in sorted(rows, key=lambda r: r['shop']['pos'])[:15]:
        s = r['shop']; print(f"{s['pos']:>3} {r['name']:<13} {s['score']:.3f} {s['ability']}({s['abilitySlot']}) {s['nature']} {[m['id'] for m in s['build']['moves']]} MT {[t['id'] for t in s['tms']]}")

if __name__ == '__main__':
    main()
