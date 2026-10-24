"""Descripción en español de cada habilidad tal y como la enseña el juego (réplica de js/data/ability-fx.js)."""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata import rd, TYPE_ES

_src = rd('js_data_ability-fx.js')
_fx = _src[_src.index('const FX = {'):_src.index("FX['pure-power']")]
_fx = re.sub(r'^\s*//[^\n]*\n', '', _fx, flags=re.M)

def _tn(t): return TYPE_ES[t]
_HELPERS = {
    'pinch': lambda t: f'+35 % de daño de tipo {_tn(t)} con poca vida (menos de 1/3).',
    'boost': lambda t: f'+20 % de daño con movimientos de tipo {_tn(t)}.',
    'absorb': lambda t: f'Los ataques de tipo {_tn(t)} no le hacen daño: le curan un poco.',
}
DESC = {}      # id -> (texto es, plus)
for m in re.finditer(r"'([a-z0-9-]+)':\s*(.+?)(?=,\s*'[a-z0-9-]+':\s|\n\s*\};)", _fx, re.S):
    aid, body = m.group(1), m.group(2).strip()
    plus = 'plus: true' in body
    d = None
    mm = re.match(r"(pinch|boost|absorb)\('(\w+)'\)", body)
    if mm: d = _HELPERS[mm.group(1)](mm.group(2))
    mm = re.match(r"byName\(/[^/]+/,\s*'([^']+)'(?:,\s*([\d.]+))?\)", body)
    if mm: d = f"+{round((float(mm.group(2) or 1.3) - 1) * 100)} % de daño con {mm.group(1)}."
    mm = re.match(r"rush\('\w+',\s*'([^']+)'\)", body)
    if mm: d = f'+50 % de velocidad con {mm.group(1)}.'
    mm = re.match(r"summon\('\w+',\s*'([^']+)'\)", body)
    if mm: d = f'Pone {mm.group(1)} al empezar la partida y cada 3 minutos.'
    if body.startswith('contact('):
        mm = re.search(r",\s*'([^']+)'\)\s*$", body)
        if mm: d = mm.group(1)
    if body.startswith('steady') or 'Object.assign({}, steady' in body: d = 'No le frenan las trampas pegajosas ni el terreno.'
    if body.startswith('moxie'): d = 'Cada enemigo derrotado le da +0,5 % de daño (hasta +15 %).'
    if d is None:
        mm = re.search(r"\bd:\s*'((?:[^'\\]|\\.)*)'", body) or re.search(r'\bd:\s*"((?:[^"\\]|\\.)*)"', body)
        if mm: d = mm.group(1).replace("\\'", "'")
        else:
            mm = re.search(r"\bd:\s*'([^']*)' \+ TN\(type\) \+ '([^']*)'", body)
    if d: DESC[aid] = (d, plus)
DESC['pure-power'] = DESC.get('huge-power', ('+50 % de daño con movimientos físicos.', False))
DESC['libero'] = DESC.get('protean', ('+12 % de daño con todos sus movimientos.', False))

def describe(aid, types):
    """[frase propia, frase genérica] en español; la genérica (+8 % tipo principal) va sola o sumada si es `plus`."""
    g = f'+8 % de daño con movimientos de tipo {_tn(types[0])}.'
    if aid in DESC:
        d, plus = DESC[aid]
        return [d, g] if plus else [d]
    return [g]

if __name__ == '__main__':
    print(len(DESC), 'habilidades con efecto propio')
    for k in ('technician', 'sturdy', 'serene-grace', 'overgrow', 'water-absorb', 'sharpness', 'static', 'limber', 'moxie', 'keen-eye', 'levitate', 'imposter', 'cursed-body'):
        print(k, '->', describe(k, ['water']))
