"""¿Ha cambiado en el juego algo de lo que usa el Consejero (extension/advisor.js)?

La extensión no lee las reglas: se engancha a piezas concretas del juego (las cartas de
subida de nivel, la pantalla que las pinta y unos campos del jugador). Este script guarda
una huella de esas piezas en data/game/HOOKS.sha y avisa si cambian, para revisar la
extensión antes de que deje de funcionar en silencio. Lo usa .github/workflows/hooks.yml.

  python -I build/check_hooks.py            → compara; escribe hooks-changed / hooks-report si cambia
  python -I build/check_hooks.py --update   → además guarda las huellas nuevas
"""
import hashlib, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA_PATH = os.path.join(ROOT, 'data', 'game', 'HOOKS.sha')
RAW = 'https://raw.githubusercontent.com/JPTER78/pokesurvivor/main/'

# fichero → None (entero) o una expresión con las líneas que importan (el resto cambia a menudo)
HOOKS = {
    'js/systems/levelup.js': None,                       # tipos y claves de las cartas, STATS y sus topes
    'js/ui/run-ui.js': r'showLevelUp|renderCards|function reroll|function pick|closeLevelUp|className = .card|lvl-reroll|offers',
    'js/game.js': r'LevelUp\.offer|showLevelUp|get state|get player|const st = ',
    'js/entities/player.js': r'this\.(mon|dex|moves|slots|maxMoves|statsTaken|dmgReduce|spdMul|cdMul|baseSpd|maxHp|banned) =|get reduction|Math\.max\(0\.12',
    'js/data/moves.js': r'function (poolFor|instance|evoInfo|levelUp|nextUpText)|G\.Moves = ',
    'index.html': r'id="(scr-levelup|cards|lvl-reroll|lvl-num)"',
}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'sentencia-tiers'}), timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def fingerprint(text, pattern):
    text = text.replace('\r\n', '\n')
    if pattern:
        rx = re.compile(pattern)
        text = '\n'.join(l.strip() for l in text.split('\n') if rx.search(l))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def out(key, val):
    gh = os.environ.get('GITHUB_OUTPUT')
    if gh:
        with open(gh, 'a', encoding='utf-8') as f: f.write(f'{key}={val}\n')


def main():
    old = json.load(open(SHA_PATH, encoding='utf-8')) if os.path.exists(SHA_PATH) else {}
    new, changed, failed = {}, [], []
    for path, pattern in HOOKS.items():
        try: new[path] = fingerprint(fetch(RAW + path), pattern)
        except Exception as e:
            failed.append(f'{path} ({e})'); new[path] = old.get(path, '?')
            continue
        if old.get(path) != new[path]: changed.append(path)
    if failed:
        print('aviso: no se pudo descargar', ', '.join(failed))
        if len(failed) == len(HOOKS): sys.exit(1)       # sin red o el repo del juego ha cambiado de sitio
    if not old:
        changed = []                                    # primera vez: solo se guardan
    if changed:
        report = ('Ha cambiado en el juego algo de lo que usa el Consejero:\n\n' +
                  ''.join(f'- `{p}`\n' for p in changed) +
                  '\nRevisar `extension/advisor.js` (enganche en `LevelUp.offer`, cartas en `#cards`, campos del jugador) '
                  'y probarlo en una partida antes de que alguien note que no marca nada. Historial del juego: '
                  'https://github.com/JPTER78/pokesurvivor/commits/main')
        print(report)
        open(os.path.join(ROOT, 'data', 'hooks-report.md'), 'w', encoding='utf-8', newline='\n').write(report + '\n')
        out('changed', 'true')
    else:
        print('Sin cambios en lo que usa el Consejero.')
        out('changed', 'false')
    if '--update' in sys.argv or not old:
        json.dump(new, open(SHA_PATH, 'w', encoding='utf-8', newline='\n'), indent=1)


if __name__ == '__main__':
    main()
