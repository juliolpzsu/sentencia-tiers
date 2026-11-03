"""Comprueba si PokéSurvivor ha cambiado y, si afecta al ranking, lo actualiza.

1. Descarga el bundle del juego (js/app.min.js del repo público JPTER78/pokesurvivor) y el índice de SurvivorTiers.
2. Extrae los datos del bundle sin ejecutarlo (build/extract_game.mjs). Si algo difiere de data/game/, lo sustituye,
   apunta el commit del juego en data/game/VERSION y recalcula el ranking.
3. Compara el ranking nuevo con el anterior: si cambian puestos, builds o puntuaciones, o si cambia alguno de los
   módulos de reglas que el modelo replica a mano, deja lo nuevo y escribe data/CHANGELOG.md; si no, restaura lo anterior.
Si no se puede bajar o leer el bundle, termina con error: la Action debe ponerse roja, no quedarse en un «sin cambios».
Salida: imprime un resumen y, en GitHub Actions, escribe changed=true/false en $GITHUB_OUTPUT.
Uso: python -I build/update.py [--force]
"""
import json, os, sys, hashlib, shutil, subprocess, tempfile, urllib.request, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, 'data', 'game')
RANK = os.path.join(ROOT, 'data', 'ranking.json')
RAW = 'https://raw.githubusercontent.com/JPTER78/pokesurvivor/main/'
BUNDLE = RAW + 'js/app.min.js'
INDEX = 'https://survivortiers.pages.dev/data/pokemon-index.json'
# lo que extract_game.mjs escribe y data/game guarda
FILES = [f'js_data_{n}.js' for n in ('pokedex', 'moves', 'abilities', 'ability-fx', 'natures', 'tms', 'sprites-meta', 'lang-en', 'types')] + ['js_ui_icons.js']
EXTRACT_RULES = 'RULES.sha'                         # huella de cada módulo de reglas (Judgment, Combat...)

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'sentencia-tiers-update/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()
def norm(b): return b.replace(b'\r\n', b'\n')                     # los finales de línea no son un cambio
def sha(b): return hashlib.sha256(norm(b)).hexdigest()[:12]

def game_commit():
    try:
        d = json.loads(fetch('https://api.github.com/repos/JPTER78/pokesurvivor/commits?path=js/app.min.js&per_page=1'))
        c = d[0]; return c['sha'][:7], c['commit']['committer']['date'][:10]
    except Exception as e:
        print('aviso: no se pudo leer el commit del juego:', e); return 'desconocido', time.strftime('%Y-%m-%d')

def extract():
    """Baja el bundle y deja los ficheros extraídos en una carpeta temporal. Cualquier fallo aquí es un error."""
    node = shutil.which('node')
    if not node: sys.exit('ERROR: hace falta node para leer el bundle del juego')
    tmp = tempfile.mkdtemp()
    bundle = os.path.join(tmp, 'app.min.js')
    try: open(bundle, 'wb').write(fetch(BUNDLE))
    except Exception as e: sys.exit(f'ERROR: no se pudo descargar {BUNDLE}: {e}')
    out_dir = os.path.join(tmp, 'out')
    r = subprocess.run([node, os.path.join(ROOT, 'build', 'extract_game.mjs'), bundle, out_dir], capture_output=True, text=True, encoding='utf-8')
    if r.stderr.strip(): print(r.stderr.strip())
    if r.returncode != 0: sys.exit('ERROR: no se pudieron extraer los datos del bundle (¿ha cambiado el ofuscador o la forma de los datos?)')
    print(r.stdout.strip())
    return out_dir

def out(key, val):
    p = os.environ.get('GITHUB_OUTPUT')
    if p: open(p, 'a', encoding='utf-8').write(f'{key}={val}\n')

def main():
    force = '--force' in sys.argv
    changed_files = []
    new = {}
    out_dir = extract()
    for local in FILES:
        data = norm(open(os.path.join(out_dir, local), 'rb').read())
        cur = os.path.join(GAME, local)
        old = open(cur, 'rb').read() if os.path.exists(cur) else b''
        if sha(old) != sha(data): changed_files.append(local); new[local] = data
    try:
        data = fetch(INDEX); json.loads(data)
        cur = os.path.join(GAME, 'survivortiers-index.json')
        old = open(cur, 'rb').read() if os.path.exists(cur) else b''
        if sha(old) != sha(data): changed_files.append('survivortiers-index.json'); new['survivortiers-index.json'] = norm(data)
    except Exception as e: print(f'aviso: índice de SurvivorTiers no disponible; se ignora: {e}')
    # reglas que el modelo replica a mano: una huella por módulo del bundle
    rules_sha_path = os.path.join(GAME, 'RULES.sha')
    old_rules = json.load(open(rules_sha_path, encoding='utf-8')) if os.path.exists(rules_sha_path) else {}
    new_rules = json.load(open(os.path.join(out_dir, EXTRACT_RULES), encoding='utf-8'))
    rules_changed = [m for m in new_rules if m in old_rules and old_rules[m] != new_rules[m]]
    rules_new_format = new_rules != old_rules and not rules_changed       # primera huella de un módulo: no es un cambio del juego
    if not changed_files and not rules_changed and not rules_new_format and not force:
        print('Sin cambios en los datos del juego.'); out('changed', 'false'); return
    print('Ficheros cambiados:', changed_files or '(ninguno)', '· reglas cambiadas:', rules_changed or '(ninguna)')
    # sustituir y recalcular
    backup = tempfile.mkdtemp()
    for local in new:
        cur = os.path.join(GAME, local)
        if os.path.exists(cur): shutil.copy2(cur, os.path.join(backup, local))
        open(cur, 'wb').write(new[local])
    commit, date = game_commit()
    open(os.path.join(GAME, 'VERSION'), 'w', encoding='utf-8', newline='\n').write(f'{commit} ({date})\n')
    old_rank = json.load(open(RANK, encoding='utf-8')) if os.path.exists(RANK) else None
    r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'build', 'rank.py')], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        print('ERROR al recalcular el ranking (¿ha cambiado el formato de los datos del juego?):\n', r.stderr[-3000:])
        for local in new:
            b = os.path.join(backup, local)
            if os.path.exists(b): shutil.copy2(b, os.path.join(GAME, local))
        out('changed', 'false'); sys.exit(1)
    new_rank = json.load(open(RANK, encoding='utf-8'))
    def key(doc): return {p['dex']: (p['base']['pos'], p['shop']['pos'], p['base']['score'], p['shop']['score'], [m['id'] for m in p['base']['build']['moves']], [m['id'] for m in p['shop']['build']['moves']]) for p in doc['pokemon']}
    moved = []
    if old_rank:
        ok, nk = key(old_rank), key(new_rank)
        names = {p['dex']: p['name'] for p in new_rank['pokemon']}
        for d in nk:
            if d in ok and ok[d][0] != nk[d][0]: moved.append((names[d], ok[d][0], nk[d][0]))
        affected = any(ok.get(d) != nk[d] for d in nk) or set(ok) != set(nk)
    else: affected = True
    if not affected and not rules_changed and not rules_new_format and not force:
        print('Los datos cambiaron pero el ranking es idéntico: no se publica nada.')
        for local in new:
            b = os.path.join(backup, local)
            if os.path.exists(b): shutil.copy2(b, os.path.join(GAME, local))
        if old_rank: json.dump(old_rank, open(RANK, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        out('changed', 'false'); return
    json.dump(new_rules, open(rules_sha_path, 'w', encoding='utf-8', newline='\n'), indent=1)
    moved.sort(key=lambda m: -abs(m[1] - m[2]))
    lines = [f'## {time.strftime("%Y-%m-%d")} · juego {commit} ({date})', '',
             f'- Ficheros del juego cambiados: {", ".join(changed_files) or "ninguno (forzado)"}.',
             f'- Pokémon que cambian de puesto: {len(moved)}.']
    for n, a, b in moved[:15]: lines.append(f'  - {n}: {a} → {b}')
    if rules_changed: lines.append(f'- ATENCIÓN: han cambiado módulos de reglas que el modelo replica a mano ({", ".join(rules_changed)}): revisar build/rank.py (`node build/extract_game.mjs <app.min.js> --dump <Módulo>` da su texto para comparar).')
    lines.append('')
    cl = os.path.join(ROOT, 'data', 'CHANGELOG.md')
    old_cl = open(cl, encoding='utf-8').read() if os.path.exists(cl) else '# Actualizaciones automáticas del ranking\n\n'
    head, _, rest = old_cl.partition('\n\n')
    open(cl, 'w', encoding='utf-8', newline='\n').write(head + '\n\n' + '\n'.join(lines) + '\n' + rest)
    summary = f'Juego {commit} ({date}): {len(moved)} Pokémon cambian de puesto' + (' · REVISAR REGLAS' if rules_changed else '')
    print(summary); open(os.path.join(ROOT, 'data', 'update-summary.txt'), 'w', encoding='utf-8', newline='\n').write(summary + '\n')
    sys.path.insert(0, os.path.join(ROOT, 'build')); import history
    history.snapshot(new_rank)                         # foto para las flechas ▲▼ y la página Cambios
    out('changed', 'true'); out('summary', summary)

if __name__ == '__main__':
    main()
