"""Tarjeta para compartir de cada Pokémon (Open Graph) → docs/img/og/<dex>.png, 1200×630.

Sin dependencias: PNG leído y escrito con zlib, letras de una fuente de píxeles 5×7 propia (va con
los retratos de Mundo Misterioso). Sirve para los dos idiomas: nombre en inglés, tier, puesto y
segundos. Solo reescribe las que cambian. Lo llama gen.py.  python -I build/og.py"""
import json, os, struct, sys, unicodedata, zlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'docs', 'img', 'og')
W, H, U = 600, 315, 2
VERSION = 1                                   # súbelo si cambia el dibujo: rehace todas                         # lienzo lógico; cada píxel lógico = 2×2 reales

def hexc(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
BG, PANEL, LINE, INK, MUTED = hexc('#07070a'), hexc('#111116'), hexc('#2a2a33'), hexc('#f1efe4'), hexc('#9b9a8f')
YEL, RED, CYAN, GREEN = hexc('#fcee0a'), hexc('#ff003c'), hexc('#00e5ff'), hexc('#58f08a')
TIER = {'S': (YEL, (0, 0, 0)), 'A': (RED, (255, 255, 255)), 'B': (CYAN, (0, 0, 0)), 'C': (hexc('#6d6d80'), (255, 255, 255)), 'D': (hexc('#3a3a46'), INK)}
# G.U.TYPE_COLOR (js/core/util.js)
TYPE = dict(normal='#b0a99f', fire='#ff7b3d', water='#4b9bff', grass='#5fcb6a', electric='#ffd33d', ice='#7fe0e0', fighting='#e0533d', poison='#b45ec4',
            ground='#d6b25c', flying='#9bb8ff', psychic='#ff5f9e', bug='#a3c43d', rock='#bfa96b', ghost='#7a6bc4', dragon='#6b58ff', dark='#6b5c52',
            steel='#a8b8c4', fairy='#ff9ed8')

# fuente 5×7 (cada fila, 5 bits)
F = {
 'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'], 'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
 'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'], 'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
 'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'], 'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
 'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01111'], 'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
 'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'], 'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
 'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'], 'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
 'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'], 'N': ['10001', '10001', '11001', '10101', '10011', '10001', '10001'],
 'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'], 'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
 'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'], 'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
 'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'], 'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
 'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'], 'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
 'W': ['10001', '10001', '10001', '10101', '10101', '10101', '01010'], 'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
 'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'], 'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
 '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'], '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
 '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'], '3': ['11111', '00010', '00100', '00010', '00001', '10001', '01110'],
 '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'], '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
 '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'], '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
 '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'], '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
 ' ': ['00000'] * 7, '/': ['00001', '00010', '00010', '00100', '01000', '01000', '10000'], '#': ['01010', '01010', '11111', '01010', '11111', '01010', '01010'],
 '-': ['00000', '00000', '00000', '01110', '00000', '00000', '00000'], '.': ['00000', '00000', '00000', '00000', '00000', '01100', '01100'],
 ':': ['00000', '01100', '01100', '00000', '01100', '01100', '00000'], "'": ['00100', '00100', '01000', '00000', '00000', '00000', '00000'],
 '~': ['00000', '00000', '01000', '10101', '00010', '00000', '00000'],
}

def fold(s):
    s = s.replace('♀', ' F').replace('♂', ' M').replace('’', "'")
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().upper()

class Canvas:
    def __init__(self):
        self.px = [[BG] * W for _ in range(H)]
    def rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(H, y + h)):
            row = self.px[yy]
            for xx in range(max(0, x), min(W, x + w)): row[xx] = c
    def text(self, x, y, s, c, sc):
        for ch in s:
            g = F.get(ch, F[' '])
            for r, bits in enumerate(g):
                for k, b in enumerate(bits):
                    if b == '1': self.rect(x + k * sc, y + r * sc, sc, sc, c)
            x += 6 * sc
        return x
    def png(self):
        raw = bytearray()
        for row in self.px:
            line = bytearray(b'\x00')
            for c in row: line += bytes(c) * U
            raw += bytes(line) * U
        chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
        return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W * U, H * U, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')

def read_png(path):
    """RGBA de 8 bits sin entrelazar (los retratos de PMD SpriteCollab)."""
    d = open(path, 'rb').read(); pos = 8; idat = b''
    while pos < len(d):
        n, t = struct.unpack('>I4s', d[pos:pos + 8]); body = d[pos + 8:pos + 8 + n]
        if t == b'IHDR': w, h, bd, ct = struct.unpack('>IIBB', body[:10])
        elif t == b'IDAT': idat += body
        pos += 12 + n
    if (bd, ct) != (8, 6): return None
    raw = zlib.decompress(idat); bpp = 4; stride = w * bpp; out = []; prev = bytearray(stride); i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out.append([tuple(line[k:k + 4]) for k in range(0, stride, 4)]); prev = line
    return out

def card(p):
    cv = Canvas(); b = p['base']
    cv.rect(0, 0, W, 3, YEL); cv.rect(0, H - 3, W, 3, YEL)
    # retrato 40×40 ×4 en un panel con sombra amarilla
    x0, y0, S = 36, 64, 4
    cv.rect(x0 + 5, y0 + 5, 40 * S + 16, 40 * S + 16, YEL); cv.rect(x0, y0, 40 * S + 16, 40 * S + 16, PANEL)
    img = read_png(os.path.join(ROOT, 'docs', 'img', 'p', f"{p['dex']}.png"))
    if img:
        for y, row in enumerate(img):
            for x, (r, g, bl, a) in enumerate(row):
                if a > 127: cv.rect(x0 + 8 + x * S, y0 + 8 + y * S, S, S, (r, g, bl))
    tx = x0 + 40 * S + 16 + 34
    end = cv.text(tx, 34, 'SENTENCIA', YEL, 2); end = cv.text(end, 34, '//', INK, 2); cv.text(end, 34, 'TIERS', YEL, 2)
    name = fold(p['nameEn'])
    sc = 5 if len(name) * 30 <= W - tx - 20 else 4 if len(name) * 24 <= W - tx - 20 else 3
    cv.text(tx, 64, name, INK, sc)
    cv.text(tx, 64 + 7 * sc + 8, f"NO. {p['dex']:03d}", MUTED, 2)
    # tipos: franjas de color
    yy = 64 + 7 * sc + 8 + 22
    for i, t in enumerate(p['types']): cv.rect(tx + i * 70, yy, 62, 6, hexc(TYPE.get(t, '#b0a99f')))
    # tier y puesto
    ty = yy + 22; bgc, fg = TIER[b['tier']]
    cv.rect(tx, ty, 6 * 4 * 6 + 16, 7 * 4 + 16, bgc); cv.text(tx + 8, ty + 8, f"TIER {b['tier']}", fg, 4)
    px = tx + 6 * 4 * 6 + 32
    end = cv.text(px, ty + 8, '#', RED, 4); end = cv.text(end, ty + 8, str(b['pos']), YEL, 4); cv.text(end + 6, ty + 16, '/ 966', MUTED, 2)
    # segundos estimados en la Sentencia
    sy = ty + 7 * 4 + 16 + 20
    secs = f"~{round(b['est'])} S"; bw = 10 + len(secs) * 24 + 8 + 9 * 12 + 10
    cv.rect(tx + 4, sy + 4, bw, 46, GREEN); cv.rect(tx, sy, bw, 46, PANEL)
    end = cv.text(tx + 10, sy + 9, secs, GREEN, 4)
    cv.text(end + 8, sy + 22, 'SENTENCIA', MUTED, 2)
    cv.text(36, H - 22, 'JULIOLPZSU.GITHUB.IO/SENTENCIA-TIERS', MUTED, 2)
    return cv.png()

def main():
    R = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True); n = 0
    # índice de lo que pinta cada tarjeta: solo se rehacen las que cambian (pintarlas todas tarda ~1 min)
    idx_path = os.path.join(OUT, 'index.json')
    idx = json.load(open(idx_path, encoding='utf-8')) if os.path.exists(idx_path) else {}
    for p in R['pokemon']:
        b = p['base']; key = f"{VERSION}|{p['nameEn']}|{'/'.join(p['types'])}|{b['tier']}|{b['pos']}|{round(b['est'])}"
        path = os.path.join(OUT, f"{p['dex']}.png")
        if idx.get(str(p['dex'])) == key and os.path.exists(path): continue
        open(path, 'wb').write(card(p)); idx[str(p['dex'])] = key; n += 1
    json.dump(dict(sorted(idx.items(), key=lambda kv: int(kv[0]))), open(idx_path, 'w', encoding='utf-8', newline='\n'), separators=(',', ':'))
    return n

if __name__ == '__main__':
    one = sys.argv[1:]
    if one:
        R = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
        for p in R['pokemon']:
            if str(p['dex']) in one: open(os.path.join(ROOT, f"og-{p['dex']}.png"), 'wb').write(card(p))
    else:
        print(main(), 'tarjetas nuevas o cambiadas en', OUT)
