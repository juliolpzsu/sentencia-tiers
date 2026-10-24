"""Comprueba si PokéSurvivor ha cambiado y, si afecta al ranking, lo actualiza.

1. Descarga los ficheros de datos del juego (repo público JPTER78/pokesurvivor) y el índice de SurvivorTiers.
2. Si alguno difiere de data/game/, los sustituye, apunta el commit del juego en data/game/VERSION y recalcula el ranking.
3. Compara el ranking nuevo con el anterior: si cambian puestos, builds o puntuaciones, deja el nuevo y escribe
   data/CHANGELOG.md; si no, restaura el anterior (nada que publicar).
Salida: imprime un resumen y, en GitHub Actions, escribe changed=true/false en $GITHUB_OUTPUT.
Uso: python -I build/update.py [--force]
"""
import json, os, sys, hashlib, shutil, subprocess, tempfile, urllib.request, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, 'data', 'game')
RANK = os.path.join(ROOT, 'data', 'ranking.json')
RAW = 'https://raw.githubusercontent.com/JPTER78/pokesurvivor/main/'
FILES = {f'js_data_{n}.js': f'js/data/{n}.js' for n in ('pokedex', 'moves', 'abilities', 'ability-fx', 'natures', 'tms', 'sprites-meta', 'lang-en', 'types', 'items', 'upgrades')}
FILES['survivortiers-index.json'] = 'https://survivortiers.pages.dev/data/pokemon-index.json'
# Ficheros del juego cuyas reglas replica rank.py: si cambian, avisar en el changelog para revisar el modelo a mano.
RULES = ['js/systems/judgment.js', 'js/systems/combat.js', 'js/entities/enemy.js', 'js/entities/player.js', 'js/systems/stats.js']

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'sentencia-tiers-update/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()
def norm(b): return b.replace(b'\r\n', b'\n')                     # los finales de línea no son un cambio
def sha(b): return hashlib.sha256(norm(b)).hexdigest()[:12]

def game_commit():
    try:
        d = json.loads(fetch('https://api.github.com/repos/JPTER78/pokesurvivor/commits?path=js/data&per_page=1'))
        c = d[0]; return c['sha'][:7], c['commit']['committer']['date'][:10]
    except Exception as e:
        print('aviso: no se pudo leer el commit del juego:', e); return 'desconocido', time.strftime('%Y-%m-%d')

def out(key, val):
    p = os.environ.get('GITHUB_OUTPUT')
    if p: open(p, 'a', encoding='utf-8').write(f'{key}={val}\n')

def main():
    force = '--force' in sys.argv
    changed_files = []
    new = {}
    for local, remote in FILES.items():
        url = remote if remote.startswith('http') else RAW + remote
        try: data = fetch(url)
        except Exception as e: print(f'aviso: no se pudo descargar {url}: {e}'); continue
        if local.endswith('.json'):
            try: json.loads(data)
            except Exception: print('aviso: índice de SurvivorTiers no es JSON válido; se ignora'); continue
        cur = os.path.join(GAME, local)
        old = open(cur, 'rb').read() if os.path.exists(cur) else b''
        if sha(old) != sha(data): changed_files.append(local); new[local] = norm(data)
    if not changed_files and not force:
        print('Sin cambios en los datos del juego.'); out('changed', 'false'); return
    print('Ficheros cambiados:', changed_files or '(forzado)')
    # reglas que el modelo replica a mano
    rules_sha_path = os.path.join(GAME, 'RULES.sha')
    old_rules = json.load(open(rules_sha_path, encoding='utf-8')) if os.path.exists(rules_sha_path) else {}
    rules_changed = []; new_rules = {}
    for f in RULES:
        try: new_rules[f] = sha(fetch(RAW + f))
        except Exception: new_rules[f] = old_rules.get(f, '?')
        if old_rules.get(f) != new_rules[f]: rules_changed.append(f)
    # sustituir y recalcular
    backup = tempfile.mkdtemp()
    for local in new:
        cur = os.path.join(GAME, local)
        if os.path.exists(cur): shutil.copy2(cur, os.path.join(backup, local))
        open(cur, 'wb').write(new[local])
    commit, date = game_commit()
    open(os.path.join(GAME, 'VERSION'), 'w', encoding='utf-8', newline='\n').write(f'{commit} ({date})\n')
    old_rank = json.load(open(RANK, encoding='utf-8')) if os.path.exists(RANK) else None
    r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'build', 'rank.py')], capture_output=True, text=True, encoding='utf-8')
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
    if not affected and not force:
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
    if rules_changed: lines.append(f'- ATENCIÓN: han cambiado ficheros de reglas que el modelo replica a mano ({", ".join(rules_changed)}): revisar build/rank.py.')
    lines.append('')
    cl = os.path.join(ROOT, 'data', 'CHANGELOG.md')
    old_cl = open(cl, encoding='utf-8').read() if os.path.exists(cl) else '# Actualizaciones automáticas del ranking\n\n'
    head, _, rest = old_cl.partition('\n\n')
    open(cl, 'w', encoding='utf-8', newline='\n').write(head + '\n\n' + '\n'.join(lines) + '\n' + rest)
    summary = f'Juego {commit} ({date}): {len(moved)} Pokémon cambian de puesto' + (' · REVISAR REGLAS' if rules_changed else '')
    print(summary); open(os.path.join(ROOT, 'data', 'update-summary.txt'), 'w', encoding='utf-8', newline='\n').write(summary + '\n')
    out('changed', 'true'); out('summary', summary)

if __name__ == '__main__':
    main()
