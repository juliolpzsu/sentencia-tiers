"""Tier list del cooperativo y equipos recomendados (27-10-2026) -> data/coop.json.

En cooperativo (net/coop.js, game.js, spawner.js, judgment.js):
  - la experiencia y el nivel son del equipo: lo que mata uno sube a todos (y el bonus de
    Aprendizaje se promedia); los enemigos tienen más vida y salen más con más jugadores;
  - un compañero caído se levanta estando 3 s a su lado (Player.REVIVE_TIME);
  - las esferas de potenciador valen para los compañeros cercanos;
  - en la Sentencia Arceus va a por el más cercano y la lluvia de pilares cae sobre cada uno.
Así, un Pokémon que aguanta peor pero limpia mucho en área (experiencia para todos) o frena y
aturde (protege a todos) aporta al grupo aunque solo no destaque.

Puntuación = 0,45 aguante propio + 0,25 farmeo en área + 0,20 control + 0,10 velocidad, cada parte
en percentil entre los 966. Si existe data/bench/bench.json (banco de partidas del bot), el farmeo
se mezcla con los enemigos derrotados por minuto medidos.
python -I build/coop.py
"""
import json, math, os, sys, itertools
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import gamedata as g
import rank

W = dict(surv=0.45, farm=0.25, ctl=0.20, spd=0.10)
TIERS = [(30, 'S'), (120, 'A'), (320, 'B'), (620, 'C'), (10 ** 6, 'D')]

def pct(vals):
    """Percentil (0-1) de cada valor; empates al mismo valor."""
    order = sorted(vals)
    n = len(order)
    pos = {}
    for i, v in enumerate(order): pos.setdefault(v, i)
    return [pos[v] / max(1, n - 1) for v in vals]

def group_farm(p):
    """Daño en hordas del grupo del primer hueco de su build (lo que se fusiona)."""
    b = p['base']['build']; dex = p['dex']; mon = rank.DEX[dex]
    side_atk = lambda d: mon['pa'] if d['cat'] == 'physical' else mon['sa']
    tot = 0.0
    for m in b['moves']:
        if m.get('slot', 1) != 1: continue
        d = rank.MOVES[m['id']]
        if d['kind'] in ('buff', 'turret'): continue
        tot += rank.farm_dps(rank.maxed(m['id'])) * side_atk(d) * (1.2 if len(mon['types']) == 1 and d['type'] == mon['types'][0] else 1.0)
    return tot

def weak_types(types):
    return {t for t in g.CHART if g.tmult(t, types) > 1.0}

def main():
    doc = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
    P = doc['pokemon']
    bench_path = os.path.join(ROOT, 'data', 'bench', 'bench.json')
    bench = json.load(open(bench_path, encoding='utf-8'))['pokemon'] if os.path.exists(bench_path) else {}
    surv = pct([math.log(max(1, p['base']['est'])) for p in P])
    farm_model = pct([group_farm(p) for p in P])
    if bench:
        kpm = [bench.get(str(p['dex']), {}).get('kpm') for p in P]
        known = [k for k in kpm if k is not None]
        kp = pct([k if k is not None else sorted(known)[len(known) // 2] for k in kpm]) if known else farm_model
        farm = [0.5 * a + 0.5 * b for a, b in zip(farm_model, kp)]
    else:
        farm = farm_model
    ctl = pct([p['base']['comp']['U'] for p in P])
    spd = pct([p['base']['comp']['S'] for p in P])
    rows = []
    for i, p in enumerate(P):
        c = dict(surv=surv[i], farm=farm[i], ctl=ctl[i], spd=spd[i])
        score = sum(W[k] * c[k] for k in W)
        roles = [r for r, k, lim in (('portador', 'surv', 0.9), ('farmeo', 'farm', 0.85), ('control', 'ctl', 0.85)) if c[k] >= lim]
        rows.append(dict(dex=p['dex'], name=p['name'], nameEn=p['nameEn'], types=p['types'], score=round(score, 4), c={k: round(v, 3) for k, v in c.items()},
                         roles=roles, solo=p['base']['pos'], weak=sorted(weak_types(p['types']))))
    rows.sort(key=lambda r: (-r['score'], r['solo'], r['dex']))
    for i, r in enumerate(rows):
        r['pos'] = i + 1; r['tier'] = next(t for lim, t in TIERS if i + 1 <= lim)
    # equipos: entre los 40 mejores, combinaciones con buena suma, roles cubiertos y debilidades repartidas
    pool = rows[:40]
    def team_score(t):
        base = sum(r['score'] for r in t) / len(t)
        roles = set(x for r in t for x in r['roles'])
        cover = ('control' in roles) * 0.04 + ('farmeo' in roles) * 0.04 + ('portador' in roles) * 0.02
        shared = sum(len(set(a['weak']) & set(b['weak'])) for a, b in itertools.combinations(t, 2)) / max(1, len(t) * (len(t) - 1) / 2)
        same_type = sum(1 for a, b in itertools.combinations(t, 2) if set(a['types']) & set(b['types']))
        return base + cover - 0.012 * shared - 0.02 * same_type
    teams = {}
    for n in (2, 3, 4):
        cands = sorted(itertools.combinations(pool[:24 if n == 4 else 32], n), key=lambda t: -team_score(t))
        picked, used = [], set()
        for t in cands:
            ids = {r['dex'] for r in t}
            if len(ids & used) > (0 if n == 2 else 1): continue       # equipos distintos entre sí
            picked.append(dict(members=[r['dex'] for r in t], score=round(team_score(t), 4),
                               roles=sorted(set(x for r in t for x in r['roles'])),
                               weakShared=sorted(set.intersection(*[set(r['weak']) for r in t])) if n > 1 else []))
            used |= ids
            if len(picked) == 4: break
        teams[str(n)] = picked
    out = dict(generated=doc['generated'], weights=W, bench=bool(bench), pokemon={str(r['dex']): r for r in rows}, order=[r['dex'] for r in rows], teams=teams)
    json.dump(out, open(os.path.join(ROOT, 'data', 'coop.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    for r in rows[:15]: print(r['pos'], r['name'], r['score'], r['roles'], 'solo', r['solo'])
    for n, ts in teams.items():
        for t in ts: print(n, [next(x['name'] for x in rows if x['dex'] == d) for d in t['members']], t['score'], t['roles'], t['weakShared'])

if __name__ == '__main__':
    main()
