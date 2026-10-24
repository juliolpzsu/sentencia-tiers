"""Descarga los retratos de PMD SpriteCollab (CC BY-NC 4.0) de los 966 Pokémon del juego a docs/img/p/<dex>.png.
Si falta el retrato, usa el sprite de PokeAPI como reserva. Uso: python -I fetch_portraits.py
"""
import json, os, re, sys, urllib.request, concurrent.futures

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'img', 'p')
os.makedirs(OUT, exist_ok=True)
dex_js = open(os.path.join(ROOT, 'data', 'game', 'js_data_pokedex.js'), encoding='utf-8').read()
DEX = [json.loads(m.group(1))['dex'] for m in re.finditer(r'^\s*(\{"dex":.*\}),?\s*$', dex_js, re.M)]

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'sentencia-tiers/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def one(dex):
    dst = os.path.join(OUT, f'{dex}.png')
    if os.path.exists(dst) and os.path.getsize(dst) > 200: return dex, 'ok'
    for src, url in (('pmd', f'https://raw.githubusercontent.com/PMDCollab/SpriteCollab/master/portrait/{dex:04d}/Normal.png'),
                     ('pokeapi', f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{dex}.png')):
        try:
            data = fetch(url)
            if data[:8] == b'\x89PNG\r\n\x1a\n':
                open(dst, 'wb').write(data); return dex, src
        except Exception as e:
            err = e
    return dex, f'FAIL {err}'

if __name__ == '__main__':
    res = {}
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        for dex, st in ex.map(one, DEX): res[dex] = st
    from collections import Counter
    print(Counter(v.split(' ')[0] for v in res.values()))
    print('fallos:', [d for d, v in res.items() if v.startswith('FAIL')])
    print('pokeapi:', [d for d, v in res.items() if v == 'pokeapi'])
