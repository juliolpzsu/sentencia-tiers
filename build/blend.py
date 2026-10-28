"""Ranking empírico + modelo (decisión de Julio del 25-10-2026).

Para cada Pokémon se estima cuántos segundos aguanta en la Sentencia un buen jugador:
  1. Predicción (todos): regresión ridge sobre rasgos conocidos de los 966 (ataque, tamaño, hordas, componentes
     del modelo, vida, velocidad, BST, legendario) con objetivo log(mediana real de los récords). Se ajusta con
     los Pokémon con récords suficientes; alpha por validación cruzada.
  2. Récords (data/records/records.json): mediana de segundos de Sentencia del top 50 de cada Pokémon.
  3. Mezcla en escala logarítmica: est = (nj·real + K·pred) / (nj + K). Con pocas partidas manda la predicción.
  4. Tienda Kecleon: la misma estimación + lo que cambia la predicción con los componentes de su build de tienda.
rank.py llama a apply(doc) antes de escribir data/ranking.json: fija base/shop.pos, .tier y .est (segundos).
"""
import json, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 10            # partidas "equivalentes" que vale la predicción
MIN_FIT = 10      # marcas en Sentencia para entrar en el ajuste
COMPS = ('T', 'U', 'A', 'D', 'S', 'Z')

SIM = {}
def feats(p, comp):
    s = p['stats']
    extra = [math.log(max(1.0, SIM[str(p['dex'])]['mean']))] if SIM else []
    # Lado especial (27-10-2026): en los récords los especiales aguantan más (ataques a distancia y en área:
    # farmean más y llegan con más nivel). Con estas dos variables la validación cruzada pasa de 0,28 a 0,39.
    side = [1.0 if s['sa'] > s['pa'] else 0.0, math.log(s['sa'] / s['pa'])]
    return extra + [s['atk'], math.log(max(p['r'], 1)), p['hordes']['surv'], s['hp'], s['spd'], p['bst'] / 100, 1.0 if p['leg'] else 0.0] + side + [comp[k] for k in COMPS]
NAMES = ['ataque', 'log radio', 'hordas', 'vida', 'velocidad', 'BST', 'legendario', 'especial', 'log AtEsp/Ataque'] + [f'comp {k}' for k in COMPS]

def _solve(A, b):
    n = len(A); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-12: continue
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1): M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]

class Ridge:
    def fit(self, X, y, alpha):
        n, m = len(X), len(X[0])
        self.mu = [sum(r[j] for r in X) / n for j in range(m)]
        self.sd = [math.sqrt(sum((r[j] - self.mu[j]) ** 2 for r in X) / n) or 1.0 for j in range(m)]
        Z = [[(r[j] - self.mu[j]) / self.sd[j] for j in range(m)] for r in X]
        self.y0 = sum(y) / n
        A = [[sum(Z[i][a] * Z[i][b] for i in range(n)) + (alpha if a == b else 0) for b in range(m)] for a in range(m)]
        bb = [sum(Z[i][a] * (y[i] - self.y0) for i in range(n)) for a in range(m)]
        self.w = _solve(A, bb); return self
    def predict(self, x):
        return self.y0 + sum(self.w[j] * (x[j] - self.mu[j]) / self.sd[j] for j in range(len(x)))

def _ranks(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2
        i = j + 1
    return r
def spearman(a, b):
    ra, rb = _ranks(a), _ranks(b); n = len(a); ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else 0.0

def cv(X, y, alpha, folds=5, reps=6, seed=3):
    rnd = random.Random(seed); out = []
    for _ in range(reps):
        idx = list(range(len(X))); rnd.shuffle(idx)
        for f in range(folds):
            te = idx[f::folds]; tes = set(te); tr = [i for i in idx if i not in tes]
            m = Ridge().fit([X[i] for i in tr], [y[i] for i in tr], alpha)
            out.append(spearman([m.predict(X[i]) for i in te], [y[i] for i in te]))
    return sum(out) / len(out)

def apply(doc, tiers, pick=None):
    path = os.path.join(ROOT, 'data', 'records', 'records.json')
    if not os.path.exists(path): return None
    rec = json.load(open(path, encoding='utf-8'))['pokemon']
    P = doc['pokemon']
    fit = [p for p in P if rec.get(str(p['dex']), {}).get('nj', 0) >= MIN_FIT and rec[str(p['dex'])].get('med')]
    y = [math.log(rec[str(p['dex'])]['med']) for p in fit]
    alphas = [3, 10, 30, 100, 300, 1000, 3000, 10000]
    global SIM
    simp = os.path.join(ROOT, 'data', 'sim.json'); sim_all = json.load(open(simp, encoding='utf-8'))['pokemon'] if os.path.exists(simp) else {}
    trials = {}
    for use_sim in ((False, True) if len(sim_all) == len(P) else (False,)):
        SIM = sim_all if use_sim else {}
        X = [feats(p, p['base']['comp']) for p in fit]
        sc = {a: cv(X, y, a) for a in alphas}
        trials[use_sim] = (max(sc.values()), max(sc, key=sc.get), sc)
    use_sim = max(trials, key=lambda k: trials[k][0] - (0.01 if k else 0))   # el simulador solo entra si mejora de verdad
    SIM = sim_all if use_sim else {}
    X = [feats(p, p['base']['comp']) for p in fit]
    _, alpha, scores = trials[use_sim]
    model = Ridge().fit(X, y, alpha)
    for p in P:
        r = rec.get(str(p['dex']), {}); nj = r.get('nj', 0) or 0
        if pick: pick(p, lambda comp: model.predict(feats(p, comp)))     # Tienda Kecleon: la combinación que más segundos estima
        pb = model.predict(feats(p, p['base']['comp'])); ps = model.predict(feats(p, p['shop']['comp']))
        real = math.log(r['med']) if nj and r.get('med') else None
        lb = (nj * real + K * pb) / (nj + K) if real is not None else pb
        p['base']['est'] = round(math.exp(lb), 1); p['shop']['est'] = round(math.exp(lb + (ps - pb)), 1)
        p['base']['pred'] = round(math.exp(pb), 1)
        p['evidence'] = dict(nj=nj, real=r.get('med'), lv=r.get('lv'), weight=round(nj / (nj + K), 2))
    for key in ('base', 'shop'):
        order = sorted(P, key=lambda p: (-p[key]['est'], -p[key]['score'], p['dex']))
        for i, p in enumerate(order):
            p[key]['pos'] = i + 1; p[key]['tier'] = next(t for lim, t in tiers if i + 1 <= lim)
    info = dict(alpha=alpha, cv_spearman=round(scores[alpha], 3), cv_by_alpha={str(a): round(v, 3) for a, v in scores.items()}, n_fit=len(fit), K=K,
                weights={n: round(w, 3) for n, w in zip((['log simulador'] if use_sim else []) + NAMES, model.w)},
                simulator=dict(used=use_sim, cv_with=round(trials[True][0], 3) if True in trials else None, cv_without=round(trials[False][0], 3)),
                with_records=sum(1 for p in P if p['evidence']['nj']), model_only_cv=round(cv([[p['base']['score']] for p in fit], y, 1), 3))
    doc['blend'] = info
    return info
