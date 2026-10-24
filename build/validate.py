"""Contraste del ranking con récords reales (data/records/records.json).

Spearman entre la puntuación del modelo y la mediana de segundos aguantados en la Sentencia por los mejores
jugadores de cada Pokémon. Escribe data/records/validation.json, que gen.py enseña en la página Método.
Uso: python -I build/validate.py [min_marcas]
"""
import json, os, sys, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]: j += 1
        for k in range(i, j + 1): r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r

def pearson(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else 0.0

def spearman(a, b): return pearson(ranks(a), ranks(b))

def partial(a, b, c):
    """Spearman parcial de a y b controlando c."""
    rab, rac, rbc = spearman(a, b), spearman(a, c), spearman(b, c)
    return (rab - rac * rbc) / math.sqrt((1 - rac ** 2) * (1 - rbc ** 2))

def boot_ci(a, b, n=2000, seed=7):
    import random
    rnd = random.Random(seed); idx = list(range(len(a))); vals = []
    for _ in range(n):
        s = [rnd.choice(idx) for _ in idx]
        vals.append(spearman([a[i] for i in s], [b[i] for i in s]))
    vals.sort(); return round(vals[int(.025 * n)], 3), round(vals[int(.975 * n)], 3)

def main(min_n=10):
    R = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
    rec = json.load(open(os.path.join(ROOT, 'data', 'records', 'records.json'), encoding='utf-8'))['pokemon']
    rows = [(p, rec[str(p['dex'])]) for p in R['pokemon'] if rec.get(str(p['dex']), {}).get('nj', 0) >= min_n]
    y = [r['med'] for _, r in rows]
    pop = [r['n'] for _, r in rows]
    model = [p['base']['score'] for p, _ in rows]
    lv = [r.get('lv') or 0 for _, r in rows]
    simp = os.path.join(ROOT, 'data', 'sim.json'); SIM = json.load(open(simp, encoding='utf-8'))['pokemon'] if os.path.exists(simp) else {}
    shop = [p['shop']['score'] for p, _ in rows]
    hordes = [p['hordes']['surv'] for p, _ in rows]
    out = dict(min_marcas=min_n, n=len(rows), records_source=json.load(open(os.path.join(ROOT, 'data', 'records', 'records.json'), encoding='utf-8'))['source'],
               spearman=dict(modelo=round(spearman(model, y), 3), modelo_ic95=boot_ci(model, y), tienda=round(spearman(shop, y), 3),
                             hordas=round(spearman(hordes, y), 3), hordas_ic95=boot_ci(hordes, y), popularidad=round(spearman(pop, y), 3),
                             nivel=round(spearman(lv, y), 3), ataque=round(spearman([p['stats']['atk'] for p, _ in rows], y), 3),
                             simulador=round(spearman([SIM.get(str(p['dex']), {}).get('mean', 0) for p, _ in rows], y), 3) if SIM else None),
               parcial_popularidad=dict(modelo=round(partial(model, y, pop), 3), hordas=round(partial(hordes, y, pop), 3)),
               componentes={k: round(spearman([p['base']['comp'][k] for p, _ in rows], y), 3) for k in ('T', 'U', 'A', 'D', 'S', 'Z', 'V')})
    # mayores discrepancias (para revisar el modelo)
    rm, ry = ranks(model), ranks(y); n = len(rows)
    diff = sorted(((rm[i] - ry[i]) / n, rows[i][0]['name'], rows[i][0]['base']['pos'], rows[i][1]['med']) for i in range(n))
    out['sobrevalorados'] = [dict(name=d[1], pos=d[2], med=d[3]) for d in diff[-8:][::-1]]
    out['infravalorados'] = [dict(name=d[1], pos=d[2], med=d[3]) for d in diff[:8]]
    json.dump(out, open(os.path.join(ROOT, 'data', 'records', 'validation.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
