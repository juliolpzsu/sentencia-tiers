"""Valida el simulador contra los récords: simula los Pokémon con récords usando su nivel mediano real.
Uso: python -I build/simval.py [partidas=10] [mín. marcas=20]"""
import json, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim
from validate import spearman
from multiprocessing import Pool

if __name__ == '__main__':
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10; mn = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    R = json.load(open(os.path.join(sim.ROOT, 'data', 'ranking.json'), encoding='utf-8'))
    rec = json.load(open(os.path.join(sim.ROOT, 'data', 'records', 'records.json'), encoding='utf-8'))['pokemon']
    P = [p for p in R['pokemon'] if rec.get(str(p['dex']), {}).get('nj', 0) >= mn and rec[str(p['dex'])].get('lv')]
    with Pool(max(2, (os.cpu_count() or 4) // 2)) as pool:
        resL = dict(pool.map(sim.sim_one, [(p, runs, p['dex'], rec[str(p['dex'])]['lv']) for p in P]))
        resN = dict(pool.map(sim.sim_one, [(p, runs, p['dex'], 200) for p in P]))
    y = [rec[str(p['dex'])]['med'] for p in P]
    out = dict(n=len(P), runs=runs,
               sim_con_nivel_real=round(spearman([resL[p['dex']]['mean'] for p in P], y), 3),
               sim_con_nivel_200=round(spearman([resN[p['dex']]['mean'] for p in P], y), 3),
               nivel_solo=round(spearman([rec[str(p['dex'])]['lv'] for p in P], y), 3),
               tiempos=dict(sim_mediana=round(st.median(resL[p['dex']]['mean'] for p in P)), real_mediana=round(st.median(y))))
    print(json.dumps(out, ensure_ascii=False))
    json.dump(out, open(os.path.join(sim.ROOT, 'data', 'records', 'simval.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
