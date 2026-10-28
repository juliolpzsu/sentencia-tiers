"""Iconos pixel art del juego (js/ui/icons.js) como SVG en docs/img/i/: objetos, cartas de nivel, tienda y
emblemas de movimiento (tipo + familia). Replica svgOfRows() y emblem() de icons.js; lo llama gen.py.
python -I build/icons.py"""
import json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata import ROOT, MOVES

SRC = open(os.path.join(ROOT, 'data', 'game', 'js_ui_icons.js'), encoding='utf-8').read()
OUT = os.path.join(ROOT, 'docs', 'img', 'i')
K = '#1b1528'                                    # contorno
# G.U.TYPE_COLOR (js/core/util.js)
TYPE_COLOR = dict(normal='#b0a99f', fire='#ff7b3d', water='#4b9bff', grass='#5fcb6a', electric='#ffd33d', ice='#7fe0e0', fighting='#e0533d', poison='#b45ec4',
                  ground='#d6b25c', flying='#9bb8ff', psychic='#ff5f9e', bug='#a3c43d', rock='#bfa96b', ghost='#7a6bc4', dragon='#6b58ff', dark='#6b5c52',
                  steel='#a8b8c4', fairy='#ff9ed8')
# los que usa la web: objetos, cartas de nivel (LevelUp.STATS[].icon) y la tienda
UI_NAMES = ['leftovers', 'choiceband', 'quickclaw', 'focussash', 'shellbell', 'amuletcoin', 'luckyegg', 'lifeorb', 'choicescarf', 'rockyhelmet', 'assaultvest',
            'heart', 'fist', 'boot', 'clock', 'shield', 'sprout', 'magnet', 'book', 'berry', 'tm', 'mint', 'capsule', 'capsuleh', 'ban']

def strs(block): return re.findall(r"'([^']*)'", block)

def ui_defs():
    out = {}
    for m in re.finditer(r"^\s*(\w+):\s*\{\s*pal:\s*\{([^}]*)\},\s*rows:\s*\[(.*?)\]\s*(,\s*outline:\s*true)?\s*\}", SRC, re.M | re.S):
        pal = dict(re.findall(r"(\w+):\s*'(#[0-9a-fA-F]{6})'", m.group(2)))
        out[m.group(1)] = dict(pal=pal, rows=strs(m.group(3)), outline=bool(m.group(4)))
    return out

def glyphs(const):
    block = re.search(const + r"\s*=\s*\{(.*?)\n\s*\};", SRC, re.S).group(1)
    return {k: strs(v) for k, v in re.findall(r"(\w+):\s*\[([^\]]*)\]", block)}

def svg(w, h, px):
    """Un rectángulo por tramo horizontal de píxeles del mismo color (como svgOf)."""
    rects = []
    for y in range(h):
        x = 0
        while x < w:
            c = px.get((x, y))
            if not c: x += 1; continue
            n = 1
            while px.get((x + n, y)) == c: n += 1
            rects.append(f'<rect x="{x}" y="{y}" width="{n}" height="1" fill="{c}"/>'); x += n
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" shape-rendering="crispEdges">{"".join(rects)}</svg>'

def from_rows(d):
    pad = 1 if d['outline'] else 0; pal = {'k': K, **d['pal']}; px = {}
    h = len(d['rows']); w = max(len(r) for r in d['rows'])
    if d['outline']:
        for y, row in enumerate(d['rows']):
            for x, ch in enumerate(row):
                if ch in '. ': continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): px[(x + pad + dx, y + pad + dy)] = K
    for y, row in enumerate(d['rows']):
        for x, ch in enumerate(row):
            if ch in '. ' or ch not in pal: continue
            px[(x + pad, y + pad)] = pal[ch]
    return svg(w + 2 * pad, h + 2 * pad, px)

def shade(hexc, k):
    n = int(hexc[1:], 16)
    f = lambda c: max(0, min(255, round(c * k)))
    return '#' + ''.join(f'{f(v):02x}' for v in (n >> 16 & 255, n >> 8 & 255, n & 255))

def emblem(typ, kind, TG, KG):
    S = 16; col = TYPE_COLOR.get(typ, '#b0a99f'); dark = shade(col, 0.55); lite = shade(col, 1.3); px = {}
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 7.5, y - 7.5)
            if d > 7.6: continue
            f = col
            if d > 6.6: f = K
            elif (x - 7.5) + (y - 7.5) > 6: f = dark
            elif (x - 7.5) + (y - 7.5) < -6.5: f = lite
            px[(x, y)] = f
    g = TG.get(typ) or TG['normal']
    for off, c in ((5, dark), (4, '#ffffff')):
        for y, row in enumerate(g):
            for x, ch in enumerate(row):
                if ch == '#': px[(x + off, y + off)] = c
    if kind and kind in KG:
        for y in range(9, 16):
            for x in range(9, 16): px[(x, y)] = K
        for y in range(10, 15):
            for x in range(10, 15): px[(x, y)] = '#2b3454'
        for y, row in enumerate(KG[kind]):
            for x, ch in enumerate(row):
                if ch == '#': px[(x + 10, y + 10)] = '#ffd23f'
    return svg(S, S, px)

def main():
    os.makedirs(OUT, exist_ok=True)
    UI = ui_defs(); TG = glyphs('TYPE_GLYPH'); KG = glyphs('KIND_GLYPH')
    files = {f'{n}.svg': from_rows(UI[n]) for n in UI_NAMES if n in UI}
    missing = [n for n in UI_NAMES if n not in UI]
    if missing: print('aviso: iconos que ya no están en icons.js:', missing)
    for mid, m in MOVES.items(): files[f'm-{mid}.svg'] = emblem(m['type'], m['kind'], TG, KG)
    for t in TYPE_COLOR: files[f't-{t}.svg'] = emblem(t, None, TG, KG)
    keep = set(files)
    for f in os.listdir(OUT):
        if f.endswith('.svg') and f not in keep: os.remove(os.path.join(OUT, f))
    for f, s in files.items():
        p = os.path.join(OUT, f)
        if not os.path.exists(p) or open(p, encoding='utf-8').read() != s:
            open(p, 'w', encoding='utf-8', newline='\n').write(s)
    return len(files)

if __name__ == '__main__':
    print(main(), 'iconos en', OUT)
