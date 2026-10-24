"""Datos compactos para la extensión «Sentencia Tiers · Consejero» (carpeta extension/).

La extensión lee en partida las cartas de subida de nivel y recomienda una según la
build de la Sentencia de cada Pokémon. Aquí se resume ranking.json a lo que necesita:

  dex -> {p: puesto, t: tier, s: slug de la ficha,
          b: build base, k: build de la Tienda Kecleon (solo si cambia los ataques)}
  build = {m: [[movimiento, papel], ...], e: {movimiento: stat que pide su evolución},
           sp: cartas de Carrera hasta el tope suave, tm: [MT que necesita]}

Papeles (de rank.choose_build): slow, stun, primary, second, buff, aquaring, agility.
Se escribe en docs/assets/advisor.json (la extensión lo baja una vez al día) y en
extension/data.js (copia de serie por si la web no responde).
"""
import json, os


def _build(var, tms=()):
    b = var['build']
    out = {'m': [[m['id'], m['code']] for m in b['moves']]}
    ev = {e['move']: e['need'] for e in b['evos']}
    if ev: out['e'] = ev
    if b['spd_cards']: out['sp'] = b['spd_cards']
    if tms: out['tm'] = list(tms)
    return out


def advisor_data(rk, slug):
    mons = {}
    for p in rk['pokemon']:
        b = _build(p['base'])
        e = {'p': p['base']['pos'], 't': p['base']['tier'], 's': slug(p), 'b': b}
        tms = [t['id'] for t in p['shop']['tms']]
        k = _build(p['shop'], tms)
        if k['m'] != b['m']: e['k'] = k
        mons[str(p['dex'])] = e
    return {'v': 1, 'generated': rk['generated'], 'game': rk['game_commit'], 'mons': mons}


def write_all(rk, slug, docs, ext_dir):
    data = advisor_data(rk, slug)
    s = json.dumps(data, separators=(',', ':'), ensure_ascii=False, sort_keys=True)
    with open(os.path.join(docs, 'assets', 'advisor.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    if os.path.isdir(ext_dir):
        with open(os.path.join(ext_dir, 'data.js'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('// Generado por build/advisor.py a partir de data/ranking.json: no editar a mano.\n'
                    'window.__stAdvisorData = ' + s + ';\n')
    return len(data['mons'])
