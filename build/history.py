"""Fotos del ranking por parche (data/history/AAAA-MM-DD_commit.json) y diferencias entre la última y la anterior.

Cada foto es compacta: {"date", "game", "pos": {dex: [puesto por defecto, puesto con tienda]}}.
update.py guarda una cada vez que publica; gen.py usa las dos últimas para las flechas ▲▼ y la página Cambios.
Uso manual: python -I build/history.py   (guarda la foto del ranking actual si no existe ya para esta versión)
"""
import json, os, glob, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, 'data', 'history')

def snapshot(doc, date=None):
    os.makedirs(HIST, exist_ok=True)
    game = doc.get('game_commit', '?').split(' ')[0]
    date = date or time.strftime('%Y-%m-%d')
    path = os.path.join(HIST, f'{date}_{re.sub(r"[^0-9a-z]", "", game)}.json')
    pos = {str(p['dex']): [p['base']['pos'], p['shop']['pos']] for p in doc['pokemon']}
    last = latest(1)
    if last and last[0]['pos'] == pos:
        return None                                   # nada cambió desde la última foto
    json.dump(dict(date=date, game=doc.get('game_commit', '?'), pos=pos), open(path, 'w', encoding='utf-8', newline='\n'), separators=(',', ':'))
    return path

def latest(n=2):
    files = sorted(glob.glob(os.path.join(HIST, '*.json')))
    return [json.load(open(f, encoding='utf-8')) for f in files[-n:]][::-1]   # la más reciente primero

def deltas():
    """{dex: [Δ por defecto, Δ con tienda]} (positivo = sube) entre las dos últimas fotos, y sus metadatos."""
    snaps = latest(2)
    if len(snaps) < 2: return None
    cur, prev = snaps
    d = {}
    for dex, (b, s) in cur['pos'].items():
        if dex in prev['pos']:
            pb, ps = prev['pos'][dex]
            if pb != b or ps != s: d[int(dex)] = [pb - b, ps - s]
    return dict(cur=dict(date=cur['date'], game=cur['game']), prev=dict(date=prev['date'], game=prev['game']), d=d)

if __name__ == '__main__':
    doc = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
    print(snapshot(doc) or 'sin cambios desde la última foto')
