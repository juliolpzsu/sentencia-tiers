"""Simulador de la Sentencia de Arceus (minuto 30 en adelante) para los 966 Pokémon.

Reproduce, con un paso de 0,1 s, lo que programa js/systems/judgment.js y el comportamiento de los jefes de
js/entities/enemy.js, con un bot que juega igual con todos los Pokémon:
  - Arena redonda (radio útil 723 px). Arceus persigue al jugador a 0,74→1,22× su velocidad (y más desde los
    5 min); lanza pilares (30 % de vida), rayos en cruz (35 %) y onda si estás cerca (40 %), todo con aviso y
    daño puro; tocarle quita el 40 % (100 % a los 10 min de Sentencia).
  - Cada 5 s acude un legendario al azar del pool: vida = max(suelo, 3 s de tu daño a un objetivo) × 1,25ⁿ,
    daño × 1,15ⁿ, velocidad ≥ 80 % de la tuya. Pegan al contacto y lanzan zonas con aviso; su daño pasa por
    tipos, defensa (física/especial), Coraza (80 %) y habilidad.
  - El jugador lleva su build por defecto (data/ranking.json): ataque principal, frenazo y aturdimiento, con
    las mejoras y cartas típicas del minuto 30, y Restos hasta el minuto 35.
  - El bot planifica a 0,6 s entre 16 direcciones: se aleja de Arceus (aprovechando sus pausas), de los
    legendarios y de la pared, sale de los avisos que estallan antes de poder salir (reacción 0,3 s) y cambia
    de ataque: aturde si hay grupo, frena si alguno se le acerca, si no, pega.
Salida: data/sim.json con la mediana y percentiles de segundos aguantados por Pokémon.
Uso: python -I build/sim.py [partidas por Pokémon=8] [procesos=núcleos]
"""
import json, math, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rank
from gamedata import DEX, MOVES, maxed, tmult, guard, player_radius, clamp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DT = 0.1
ARENA = (24 - 1.4) * 32           # 723 px
T0 = 1800                         # minuto 30
CD_MUL = rank.CD_MUL              # Reflejos al máximo + 10 cartas
ATK_MUL = 1.4 * 1.1 ** 10         # Fuerza al máximo + 10 cartas de Potencia
CRIT = 1 + 0.30 * 0.5             # Golpe Crítico 30 % a ×1,5
RED = 0.8                         # Coraza (mejoras + cartas) en el tope
REACT = 0.3                       # tiempo de reacción del bot ante un aviso
LOOK = 0.6                        # horizonte del planificador del bot (s)
KEEP = 380                        # distancia a Arceus que intenta mantener
WALL = 600                        # a partir de aquí la pared penaliza
CAND = [None] + [(math.cos(i * math.pi / 8), math.sin(i * math.pi / 8)) for i in range(16)]
LEGS = rank.LEGS

def cap_spd(s): return s if s <= 130 else 130 + (s - 130) * 0.25

class Hz:
    __slots__ = ('kind', 'x', 'y', 'r', 'a', 'len', 'w', 't', 'pct', 'dmg', 'seen', 'typ', 'cls')
    def __init__(self, kind, x, y, t, r=0, a=0, ln=0, w=0, pct=0, dmg=0, typ=None, cls=None):
        self.kind, self.x, self.y, self.t, self.r, self.a, self.len, self.w = kind, x, y, t, r, a, ln, w
        self.pct, self.dmg, self.typ, self.cls, self.seen = pct, dmg, typ, cls, -REACT
    def inside(self, px, py, pr):
        if self.kind == 'zone': return (px - self.x) ** 2 + (py - self.y) ** 2 < (self.r + pr * 0.6) ** 2
        ca, sa = math.cos(self.a), math.sin(self.a); dx, dy = px - self.x, py - self.y
        along = dx * ca + dy * sa
        if along < -pr or along > self.len + pr: return False
        return abs(-dx * sa + dy * ca) <= self.w / 2 + pr * 0.6
    def escape(self, px, py):
        """Dirección para salir cuanto antes."""
        if self.kind == 'zone':
            dx, dy = px - self.x, py - self.y; d = math.hypot(dx, dy) or 1e-6
            return dx / d, dy / d
        ca, sa = math.cos(self.a), math.sin(self.a); side = -(px - self.x) * sa + (py - self.y) * ca
        s = 1 if side >= 0 else -1
        return -sa * s, ca * s

class Leg:
    __slots__ = ('x', 'y', 'hp', 'spd', 'dmg', 'shot', 'types', 'atype', 'cls', 'ranged', 'cd', 'touch', 'slow', 'slowT', 'stun', 'fury', 'mon', 'r')
    def __init__(self, L, x, y, hp, n, pspd, t):
        kd = 1.15 ** n
        self.x, self.y, self.hp, self.mon, self.r = x, y, hp, L, 22
        self.spd = max(clamp(48 + (L['spd'] - 78) * 0.6, 48, 105), pspd * 0.8)
        self.dmg = (36 + t / 20) * kd; self.shot = (18 + t / 40) * kd
        self.types = L['types']; self.atype = L['types'][0]; self.cls = 'p' if L['pa'] >= L['sa'] else 's'
        self.ranged = any(x in ('psychic', 'electric', 'ghost', 'fairy', 'fire', 'water', 'ice', 'dragon') for x in L['types'])
        self.cd = 1.6; self.touch = 0; self.slow = 0; self.slowT = 0; self.stun = 0; self.fury = False

def cards_at(level):
    """Cartas de Vigor y Síntesis según el nivel al minuto 30: las de stat con tope (Potencia 40, Carrera 8,
    Reflejos 10, Coraza 12, Imán 6, Aprendizaje 8) y las de movimientos (~40) salen primero; después solo
    quedan Vigor, Síntesis y Baya Zidra, sin tope."""
    extra = max(0, level - 1 - 124)
    return 15 + 0.4 * extra, 5 + 0.4 * extra

def player_profile(p, level=None):
    """Lo que el simulador necesita de un Pokémon, sacado de su build por defecto."""
    dex = p['dex']; b = DEX[dex]; ab = p['base']['ability']; types = b['types']
    mon = rank.mon_with_nature(dex, None)
    r, _ = player_radius(dex)
    pool = [m['id'] for m in p['base']['build']['moves']]
    moves = []
    for mid in pool:
        d = MOVES[mid]
        if d['kind'] == 'buff': continue
        s = maxed(mid)
        atk = mon['pa'] if d['cat'] == 'physical' else mon['sa']
        mono = 1.2 if len(types) == 1 and d['type'] == types[0] else 1.0
        base = rank.move_dps(s) / CD_MUL * atk * mono * rank.out_mul(ab, d, types) * ATK_MUL * CRIT
        if d['kind'] in rank.CLOSE: base *= 0.5
        reach = 300 if d['kind'] not in rank.CLOSE else 90
        slow = min(0.8, d.get('slow', 0) * (2 if ab == 'serene-grace' else 1)) if d.get('slow') and d['kind'] not in rank.CLOSE else 0
        stun = s['stun'] * 0.35 if d['kind'] == 'stun' else 0
        moves.append(dict(id=mid, type=d['type'], cat=d['cat'], dps=base, reach=reach, slow=slow, stun=stun, cd=max(0.1, s['cd'] * CD_MUL), area=s.get('radius', 50)))
    if not moves: moves = [dict(id='tackle', type='normal', cat='physical', dps=10, reach=90, slow=0, stun=0, cd=0.2, area=50)]
    # defensa ante cada legendario (tipos, defensa y habilidad), multiplicador de su daño
    def inmul(L):
        at = L['types'][0]; cls = 'p' if L['pa'] >= L['sa'] else 's'
        k, dodge = rank.in_mul(ab, at, cls, types)
        return tmult(at, types) * guard(mon['df'] if cls == 'p' else mon['sd']) * k * (1 - dodge)
    vig, syn = cards_at(level) if level else (15, 5)
    hp = b['hp'] + 80 + 20 * vig
    spd = cap_spd(mon['spd'] * 1.24 * 1.07 ** 8 * (1.3 if ab == 'speed-boost' else 1.08 if ab == 'run-away' else 1.0))
    regen = 1.0 + 0.9 * syn + hp * rank.REGEN_AB.get(ab, 0)
    return dict(dex=dex, hp=hp, spd=spd, r=r, regen=regen, moves=moves, inmul={L['dex']: inmul(L) for L in LEGS},
                sturdy=ab == 'sturdy', eff={(m['type'], m['cat'], L['dex']): tmult(m['type'], L['types']) * guard(L['df'] if m['cat'] == 'physical' else L['sd']) for m in moves for L in LEGS})

DEBUG = None
def run(prof, seed, tmax=1200):
    rnd = random.Random(seed)
    dbg = DEBUG if DEBUG is not None else {}
    px, py = 0.0, 96.0; ax, ay = 0.0, -160.0
    hp = maxhp = prof['hp']; spd = prof['spd']; pr = prof['r']
    hz = []; legs = []; arenaT = 0.0; bossT = 1.2; n = 0
    acd = 2.2; alast = None; acast = 0.0; atouch = 0.0; invul = 0.0; item = True; sash_t = -99; sturdy_t = -999
    prev_dir = None
    moves = prof['moves']; mcd = [0.0] * len(moves); active = 0
    single = max((m['dps'] for m in moves), default=10)
    floor = (3200 + T0 * 9) * 0.35
    base = max(floor, single * 3)
    while arenaT < tmax:
        arenaT += DT; t = T0 + arenaT
        # ---------- Arceus ----------
        dA = math.hypot(px - ax, py - ay) or 1e-6
        if acast > 0:
            acast -= DT
        else:
            k = min(1.22, 0.74 + arenaT * 0.013) + max(0, arenaT - 300) * 0.0015
            aspd = max(70, spd * k)
            ax += (px - ax) / dA * aspd * DT; ay += (py - ay) / dA * aspd * DT
            acd -= DT
            if acd <= 0:
                if dA < 210 and rnd.random() < 0.6:
                    hz.append(Hz('zone', ax, ay, 0.85, r=170, pct=0.4)); wind = 0.85; alast = 'nova'
                elif alast != 'rain':
                    m_ = 4 + min(6, int(arenaT // 10))
                    for i in range(m_):
                        a = rnd.random() * 6.2832; d = rnd.uniform(40, 150) if i else 0
                        hz.append(Hz('zone', px + math.cos(a) * d, py + math.sin(a) * d * 0.8, 1.25 + i * 0.09, r=44, pct=0.3))
                    wind = 0.7; alast = 'rain'
                else:
                    a0 = math.atan2(py - ay, px - ax) + (0 if rnd.random() < 0.5 else math.pi / 4)
                    nb = 8 if arenaT > 30 else 4
                    for i in range(nb): hz.append(Hz('beam', ax, ay, 1.1, a=a0 + i * 6.2832 / nb, ln=1700, w=34, pct=0.35))
                    wind = 1.1; alast = 'cross'
                acast = wind + 0.35; acd = max(1.4, 3.2 - arenaT * 0.025)
        # ---------- legendarios ----------
        bossT -= DT
        if bossT <= 0:
            bossT = 5
            L = LEGS[rnd.randrange(len(LEGS))]
            for _ in range(16):
                a = rnd.random() * 6.2832; d = ARENA - rnd.uniform(3, 6) * 32
                lx, ly = math.cos(a) * d, math.sin(a) * d
                if (lx - px) ** 2 + (ly - py) ** 2 > 280 ** 2: break
            legs.append(Leg(L, lx, ly, base * 1.25 ** n, n, spd, t)); n += 1
        for e in legs:
            if e.slowT > 0:
                e.slowT -= DT
                if e.slowT <= 0: e.slow = 0
            if e.stun > 0: e.stun -= DT; continue
            dx, dy = px - e.x, py - e.y; d = math.hypot(dx, dy) or 1e-6
            v = e.spd * (1 - e.slow) * (1.25 if e.fury else 1)
            if e.ranged and d < 220: v *= -0.3
            e.x += dx / d * v * DT; e.y += dy / d * v * DT
            e.cd -= DT * (1.25 if e.fury else 1)
            if e.cd <= 0 and d < 480:
                if d < 125: hz.append(Hz('zone', e.x, e.y, 0.85, r=96 + e.r, dmg=e.dmg * 1.3, typ=e.mon['dex'], cls=e.cls))
                else:
                    for i in range(6 if e.fury else 4):
                        a = rnd.random() * 6.2832 if i else 0; dd = rnd.uniform(40, 120) if i else 0
                        hz.append(Hz('zone', px + math.cos(a) * dd, py + math.sin(a) * dd * 0.8, 1.05 + i * 0.12, r=50, dmg=e.shot * 1.15, typ=e.mon['dex'], cls=e.cls))
                e.cd = rnd.uniform(1.3, 2.0)
            e.touch -= DT
            if d < e.r + pr and e.touch <= 0 and invul <= 0:
                e.touch = 0.55
                x_ = e.dmg * prof['inmul'][e.mon['dex']] * (1 - RED); hp -= x_; invul = 0.45; dbg['contacto'] = dbg.get('contacto', 0) + x_
        # ---------- ataques del jugador (un hueco activo) ----------
        alive = [e for e in legs if e.hp > 0]
        near = sorted(alive, key=lambda e: (e.x - px) ** 2 + (e.y - py) ** 2)
        close = [e for e in near if (e.x - px) ** 2 + (e.y - py) ** 2 < 300 ** 2]
        want = 0
        stun_i = next((i for i, m in enumerate(moves) if m['stun']), None)
        slow_i = next((i for i, m in enumerate(moves) if m['slow']), None)
        dmg_i = max(range(len(moves)), key=lambda i: moves[i]['dps'])
        if stun_i is not None and len(close) >= 2 and mcd[stun_i] <= 0: want = stun_i
        elif slow_i is not None and any(e.slow == 0 for e in close): want = slow_i
        else: want = dmg_i
        active = want
        for i in range(len(mcd)): mcd[i] -= DT
        m = moves[active]
        tgt = near[0] if near and (near[0].x - px) ** 2 + (near[0].y - py) ** 2 < m['reach'] ** 2 else None
        if tgt:
            tgt.hp -= m['dps'] * prof['eff'][(m['type'], m['cat'], tgt.mon['dex'])] * DT
            if m['slow']:
                for e in close:
                    if (e.x - tgt.x) ** 2 + (e.y - tgt.y) ** 2 < 120 ** 2: e.slow = max(e.slow, m['slow']); e.slowT = 1.2
            if m['stun'] and mcd[active] <= 0:
                for e in close:
                    if (e.x - tgt.x) ** 2 + (e.y - tgt.y) ** 2 < (m['area'] + 20) ** 2: e.stun = max(e.stun, m['stun'] + 0.45)
                mcd[active] = m['cd']
            if tgt.hp <= 0 and not tgt.fury: pass
            if tgt.hp < 0: legs.remove(tgt)
        for e in legs:
            if not e.fury and e.hp < base * 1.25 ** 0 * 0.5: pass
        # ---------- movimiento del bot ----------
        for h in hz: h.seen += DT
        vis = [h for h in hz if h.seen > 0]
        kA = min(1.22, 0.74 + arenaT * 0.013) + max(0, arenaT - 300) * 0.0015
        aspd = max(70, spd * kA)
        best = None
        for c in CAND:
            if c is None: dx_, dy_ = 0.0, 0.0
            else: dx_, dy_ = c
            qx, qy = px + dx_ * spd * LOOK, py + dy_ * spd * LOOK
            qr = math.hypot(qx, qy)
            if qr > ARENA: qx, qy = qx / qr * ARENA, qy / qr * ARENA; qr = ARENA
            # Arceus dentro de LOOK s (quieto mientras lanza)
            mv = max(0.0, LOOK - max(0.0, acast)) * aspd
            ddx, ddy = qx - ax, qy - ay; dq = math.hypot(ddx, ddy) or 1e-6
            dA2 = max(0.0, dq - mv)
            sc = -max(0.0, KEEP - dA2) * 3.0 - (400 if dA2 < 215 else 0) - (2000 if dA2 < 28.5 + pr + 10 else 0)
            sc -= max(0.0, qr - WALL) * 2.0
            for e in near[:10]:
                dd = math.hypot(qx - e.x, qy - e.y) - (0 if e.stun > 0 else e.spd * (1 - e.slow) * LOOK)
                if dd < 160: sc -= (160 - dd) * 2.0
            for h in vis:
                if h.t <= LOOK + 0.25:
                    # posición cuando estalla
                    f = min(1.0, h.t / LOOK)
                    hx, hy = px + (qx - px) * f, py + (qy - py) * f
                    if h.inside(hx, hy, pr + 4): sc -= 900 * (h.pct * 3 if h.pct else 1)
            if prev_dir is not None and c is not None: sc += 25 * (dx_ * prev_dir[0] + dy_ * prev_dir[1])
            if best is None or sc > best[0]: best = (sc, c)
        c = best[1]; prev_dir = c
        if c is not None:
            px += c[0] * spd * DT; py += c[1] * spd * DT
        rr = math.hypot(px, py)
        if rr > ARENA: px, py = px / rr * ARENA, py / rr * ARENA
        # ---------- avisos que estallan ----------
        keep = []
        for h in hz:
            h.t -= DT
            if h.t > 0: keep.append(h); continue
            if h.inside(px, py, pr) and invul <= 0:
                if h.pct: dmg = maxhp * h.pct
                else: dmg = h.dmg * prof['inmul'][h.typ] * (1 - RED)
                hp -= dmg; invul = 0.45; k_ = ('arceus_' + ('onda' if h.r == 170 else 'pilar' if h.kind == 'zone' else 'rayo')) if h.pct else ('leg_golpe' if h.r > 60 else 'leg_zona'); dbg[k_] = dbg.get(k_, 0) + dmg
        hz = keep
        # ---------- toque de Arceus ----------
        atouch -= DT
        if dA < 28.5 + pr and atouch <= 0:
            atouch = 0.9; x_ = maxhp * min(1, 0.4 + max(0, arenaT - 420) / 180 * 0.6); hp -= x_; invul = 0.45; dbg['arceus_toque'] = dbg.get('arceus_toque', 0) + x_
        invul -= DT
        if arenaT >= 300: item = False
        hp = min(maxhp, hp + (prof['regen'] + (maxhp * 0.015 if item else 0)) * DT)
        if hp <= 0:
            if item and arenaT - sash_t > 60 and False: pass
            if prof['sturdy'] and arenaT - sturdy_t > 90: hp = 1; sturdy_t = arenaT; invul = 1.2; continue
            return arenaT
    return tmax

def sim_one(args):
    p, runs, seed = args[:3]
    prof = player_profile(p, level=args[3] if len(args) > 3 else None)
    ts = sorted(run(prof, seed * 1000 + i) for i in range(runs))
    q = lambda f: round(ts[min(len(ts) - 1, int(f * (len(ts) - 1) + 0.5))], 1)
    return p['dex'], dict(med=q(0.5), p25=q(0.25), p75=q(0.75), mean=round(sum(ts) / len(ts), 1))

def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else (os.cpu_count() or 4)
    only = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
    R = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
    P = [p for p in R['pokemon'] if not only or p['dex'] in only]
    t0 = time.time(); out = {}
    if procs > 1 and len(P) > 4:
        from multiprocessing import Pool
        with Pool(procs) as pool:
            for i, (dex, r) in enumerate(pool.imap_unordered(sim_one, [(p, runs, p['dex']) for p in P], chunksize=4)):
                out[str(dex)] = r
                if i % 100 == 0: print(f'  {i}/{len(P)}  {time.time() - t0:.0f}s', flush=True)
    else:
        for p in P: dex, r = sim_one((p, runs, p['dex'])); out[str(dex)] = r
    doc = dict(generated=time.strftime('%Y-%m-%d'), runs=runs, bot=dict(reaction=REACT, dt=DT), pokemon=out)
    path = os.path.join(ROOT, 'data', 'sim.json') if not only else os.path.join(ROOT, 'data', 'sim-sample.json')
    json.dump(doc, open(path, 'w', encoding='utf-8', newline='\n'), separators=(',', ':'))
    print(f'{len(out)} Pokémon en {time.time() - t0:.0f}s → {path}')
    if only:
        for p in P: print(p['name'], out[str(p['dex'])])

if __name__ == '__main__':
    main()
