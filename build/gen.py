"""Genera la web estática (docs/) a partir de data/ranking.json. Uso: python -I gen.py"""
import json, os, re, sys, html, shutil, unicodedata, time
from urllib.parse import urlencode
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedata import ROOT, MOVES, NAT_BY, ABIL_NAMES, TYPE_ES, TYPE_EN, TYPES, EVO, NEED_NAME, en, TM_PRICE, TM_MOVES
from abilfx import describe
import history
DELTA = history.deltas()                       # None si solo hay una foto
import advisor

R = json.load(open(os.path.join(ROOT, 'data', 'ranking.json'), encoding='utf-8'))
P = R['pokemon']
BY = {p['dex']: p for p in P}
FRESH = bool(DELTA) and (time.mktime(time.strptime(R['generated'], '%Y-%m-%d')) - time.mktime(time.strptime(DELTA['cur']['date'], '%Y-%m-%d'))) <= 7 * 86400
DOCS = os.path.join(ROOT, 'docs')
SITE = 'https://juliolpzsu.github.io/sentencia-tiers'
REPO = 'https://github.com/juliolpzsu/sentencia-tiers'
STORE = 'https://chromewebstore.google.com/detail/glehijclpafhcajjdcmmcaepkjeianlo'
LANGS = ['es', 'en']
esc = html.escape

TC = {'normal': '#b5b48f', 'fire': '#ff7a1f', 'water': '#3d8bff', 'grass': '#5cd65c', 'electric': '#ffd21f', 'ice': '#7fe0ff', 'fighting': '#e8503f', 'poison': '#c15ad6',
      'ground': '#e0b35a', 'flying': '#a9b8ff', 'psychic': '#ff5fa8', 'bug': '#a7c428', 'rock': '#c9ad5a', 'ghost': '#8a6bd6', 'dragon': '#7a68ff', 'dark': '#9a846e', 'steel': '#b8c0d8', 'fairy': '#ff9fd6'}
TYPE_NAME = {'es': TYPE_ES, 'en': TYPE_EN}
STAT = {'es': dict(hp='Vida', spd='Velocidad', pa='Ataque', sa='At. Especial', df='Defensa', sd='Def. Especial'),
        'en': dict(hp='HP', spd='Speed', pa='Attack', sa='Sp. Atk', df='Defense', sd='Sp. Def')}
KIND = {'es': dict(projectile='proyectil', melee='cuerpo a cuerpo', beam='rayo', orbit='orbes', nova='ráfaga radial', aura='aura', buff='potenciador', boomerang='bumerán', chain='cadena',
                   mine='minas', meteor='meteoros', turret='torreta', dash='embestida', trail='rastro', cone='abanico', homing='perseguidor', bounce='rebote', charge='carga', spin='giro',
                   quake='onda sísmica', vortex='remolino', shove='empujón', stun='aturdimiento'),
        'en': dict(projectile='projectile', melee='melee', beam='beam', orbit='orbit', nova='nova', aura='aura', buff='boost', boomerang='boomerang', chain='chain', mine='mines',
                   meteor='meteors', turret='turret', dash='dash', trail='trail', cone='cone', homing='homing', bounce='bounce', charge='charge', spin='spin', quake='quake',
                   vortex='vortex', shove='shove', stun='stun')}
CAT = {'es': dict(physical='Físico', special='Especial'), 'en': dict(physical='Physical', special='Special')}
COMP = {'es': dict(V=('Llegar al minuto 30', 'ranking en hordas de SurvivorTiers'), T=('Aguante ante legendarios', 'vida, defensas, tipos y habilidad frente al pool'),
                   U=('Control', 'frenazos y aturdimientos: lo único que afecta a los jefes'), A=('Regeneración', 'contra el daño porcentual de Arceus'),
                   D=('Daño a un legendario', 'mejor ataque de su lado contra el pool'), S=('Velocidad efectiva', 'con el tope suave de 130'), Z=('Tamaño', 'radio de colisión: más pequeño, más fácil esquivar')),
        'en': dict(V=('Reaching minute 30', 'SurvivorTiers horde ranking'), T=('Toughness vs legendaries', 'HP, defenses, typing and ability against the pool'),
                   U=('Control', 'slows and stuns: the only things that work on bosses'), A=('Regeneration', 'against Arceus’ percentage damage'),
                   D=('Damage to one legendary', 'best same-side attack against the pool'), S=('Effective speed', 'with the soft cap at 130'), Z=('Size', 'collision radius: smaller is easier to dodge with'))}

UI = {
 'es': dict(title='Sentencia Tiers', tagline='Tier list de PokéSurvivor para la Sentencia de Arceus', nav_tiers='Tiers', nav_judg='La Sentencia', nav_method='Método', nav_repo='Código', nav_coop='Cooperativo', nav_adv='Consejero', nav_adv_t='Extensión para Chrome: marca en el juego qué carta coger según la build de la Sentencia',
            intro='Los 966 Pokémon ordenados por los segundos que aguantan en la Sentencia de Arceus (minuto 30). La estimación junta los récords reales del juego (las mejores partidas de cada Pokémon) con una predicción hecha a partir del código del juego: ataque, tamaño, lo bien que limpia hordas, aguante ante los legendarios, control y velocidad.',
            updated='Parche del juego', pokemon='Pokémon', legs='Legendarios', nonlegs='No legendarios', all='Todos', tier='Tier', sort='Ordenar por', group='Agrupar por',
            mode_base='Por defecto', mode_shop='Tienda Kecleon', count='{n} de {m} Pokémon', none='Ningún Pokémon cumple los filtros.', shuffle='Al azar', filters='Filtros', types='Tipos',
            sort_opts=[('pos', 'Puesto'), ('name', 'Nombre'), ('dex', 'Nº Pokédex'), ('hordes', 'Ranking en hordas'), ('T', 'Aguante'), ('U', 'Control'), ('A', 'Regeneración'), ('D', 'Daño'), ('S', 'Velocidad efectiva'), ('Z', 'Tamaño'), ('hp', 'Vida'), ('spd', 'Velocidad base'), ('rnd', 'Al azar')],
            group_opts=[('tier', 'Tier'), ('type', 'Tipo'), ('leg', 'Legendarios'), ('none', 'Sin agrupar')],
            flag_leg='Solo legendarios', flag_slow='Con frenazo', flag_stun='Con aturdimiento', flag_regen='Con regeneración', slow='Frenazo', stun='Aturdimiento', regen='Regeneración', slowS='SLOW', stunS='STUN', regenS='REGEN',
            mode_help='Por defecto: habilidad 1, naturaleza neutra y solo sus ataques naturales. Tienda Kecleon: la mejor habilidad (Cápsula), la mejor naturaleza (Menta) y las MT que le sirven.',
            back='Tier list', rank_base='Puesto · por defecto', rank_shop='Puesto · con Tienda Kecleon', rank_hordes='Ranking en hordas (SurvivorTiers)', of='de', stats='Estadísticas del juego', guard='Daño que recibe (defensa)',
            radius='Radio de colisión', px='px', speed_eff='Velocidad efectiva en la Sentencia', score='Puntuación', components='Componentes del modelo', incoming='Daño recibido por tipo (pool de legendarios)',
            abilities='Habilidades', default_ab='Habilidad 1 · por defecto', hidden_ab='Oculta', rec_ab='Recomendada', ab_note='Te toca la 1 o la 2 al azar; la oculta, 1 de cada 20.',
            build='Build', tab_base='Por defecto', tab_shop='Con Tienda Kecleon', moves='Movimientos', slot='HUECO', why='Por qué', start='Movimiento inicial', start2='Segundo movimiento inicial (Repertorio)', bans='Vetos (Mejoras → Veto)',
            items='Objeto', items_note='Solo se lleva uno por partida: los sueltan los jefes y los cofres con candado.', cards='Cartas de nivel', evos='Evoluciones de movimiento', evo_text='{move} evoluciona al nivel máximo si en la partida has cogido al menos una vez la carta {need}.',
            nature='Naturaleza (Menta, 1.500)', ability='Habilidad (Cápsula)', tms='MT a comprar', tm_note='La Tienda Kecleon vende 8 MT al día entre unas 100; si ninguna le sirve a tu compañero, la última se cambia por una que sí aprenda.', total='Total', none_tm='No necesita ninguna MT: su pool natural ya tiene lo importante.',
            nat_none='Ninguna Menta mejora claramente su puntuación: mejor dejar la naturaleza que le tocó.', ab_same='Su habilidad 1 ya es la mejor de las suyas para la Sentencia.', prev='Anterior', next='Siguiente', hordes_link='Ver su ficha en SurvivorTiers',
            strategy='Estrategia', verdict='Veredicto', footer_data='Datos y reglas: código de PokéSurvivor (JPTER78) · Ranking en hordas: SurvivorTiers (@fildotai) · Retratos: PMD SpriteCollab (CC BY-NC 4.0) · Pokémon © Nintendo/Creatures/GAME FREAK.',
            footer_fan='Proyecto de fans sin ánimo de lucro, sin relación con los autores del juego ni con Nintendo.', generated='Generado el', not_available='—',
            flag_tm='MT útil hoy', tmToday='Tienda Kecleon · MT de hoy ({d})', tmHint='Pokémon a los que su build con Tienda Kecleon les pide una MT que se vende hoy', tmFor='{n} Pokémon la usan en su build', moved='Puestos que ha subido o bajado con la última actualización del juego', tmNone='Hoy ninguna de las MT a la venta aparece en las builds recomendadas: no merece la pena comprar ninguna para la Sentencia. Mañana habrá otras 8.', tm8='la octava puede ser otra: si ninguna le sirve a tu compañero, el juego la cambia (carga tu partida para verla exacta)',
            changes='Cambios', search='Nombre, nº, ataque o habilidad',
            est='Aguanta en la Sentencia (estimado)',
            me='Mi partida', meTitle='Cargar tu partida', meIntro='Con tu partida la web marca los Pokémon que tienes, sus mejoras y la habilidad y naturaleza que te tocaron, y calcula tu puesto aproximado con ellas. Todo se queda en este navegador: no se envía a ningún sitio.',
            meHow='1. Abre pokesurvivor.com con tu cuenta. 2. Pulsa F12 y entra en la pestaña «Console». 3. Pega esta línea y pulsa Intro: copia tu partida al portapapeles. 4. Vuelve aquí y pégala en el cuadro.',
            copy='Copiar la línea', copied='Copiada', meLoad='Cargar', meClear='Quitar partida', close='Cerrar', mePaste='Pega aquí tu partida (empieza por {"stats":…)', meError='No parece una partida de PokéSurvivor: tiene que ser el JSON entero de la clave ps.cloud.',
            meLoaded='Partida de {name}: {n} Pokémon.', mine='Mis Pokémon', owned='Lo tienes', notOwned='No lo tienes', ownedS='TUYO', upgrades='Mejoras compradas', yourRank='Tu puesto con tu habilidad y tu naturaleza', you='tú',
            sort_you='Tu puesto', meBlock='Tu partida ({name})', meAbility='Tu habilidad', meNature='Tu naturaleza', loading='Calculando tu puesto…',
            meRank='Con tu habilidad y tu naturaleza quedaría en el puesto <b>{n}</b> de 966 (puesto general: {base}). Las mejoras y cartas se suponen al máximo; las MT que ya le enseñaste no se cuentan.'),
 'en': dict(title='Sentencia Tiers', tagline='PokéSurvivor tier list for the Judgment of Arceus', nav_tiers='Tiers', nav_judg='The Judgment', nav_method='Method', nav_repo='Source', nav_coop='Co-op', nav_adv='Advisor', nav_adv_t='Chrome extension: marks in game which card to take according to the Judgment build',
            intro='All 966 Pokémon ranked by the seconds they last in the Judgment of Arceus (minute 30). The estimate blends the game’s real records (each Pokémon’s best runs) with a prediction built from the game’s code: attack, size, how well it clears hordes, toughness against the legendaries, control and speed.',
            updated='Game patch', pokemon='Pokémon', legs='Legendaries', nonlegs='Non-legendaries', all='All', tier='Tier', sort='Sort by', group='Group by',
            mode_base='Default', mode_shop='Kecleon Shop', count='{n} of {m} Pokémon', none='No Pokémon matches the filters.', shuffle='Shuffle', filters='Filters', types='Types',
            sort_opts=[('pos', 'Rank'), ('name', 'Name'), ('dex', 'Dex number'), ('hordes', 'Horde ranking'), ('T', 'Toughness'), ('U', 'Control'), ('A', 'Regeneration'), ('D', 'Damage'), ('S', 'Effective speed'), ('Z', 'Size'), ('hp', 'HP'), ('spd', 'Base speed'), ('rnd', 'Random')],
            group_opts=[('tier', 'Tier'), ('type', 'Type'), ('leg', 'Legendaries'), ('none', 'No grouping')],
            flag_leg='Legendaries only', flag_slow='Has a slow', flag_stun='Has a stun', flag_regen='Has regeneration', slow='Slow', stun='Stun', regen='Regeneration', slowS='SLOW', stunS='STUN', regenS='REGEN',
            mode_help='Default: ability 1, neutral nature and natural moves only. Kecleon Shop: best ability (Capsule), best nature (Mint) and the TMs that help.',
            back='Tier list', rank_base='Rank · default', rank_shop='Rank · with Kecleon Shop', rank_hordes='Horde ranking (SurvivorTiers)', of='of', stats='In-game stats', guard='Damage taken (defense)',
            radius='Collision radius', px='px', speed_eff='Effective speed in the Judgment', score='Score', components='Model components', incoming='Damage taken by type (legendary pool)',
            abilities='Abilities', default_ab='Ability 1 · default', hidden_ab='Hidden', rec_ab='Recommended', ab_note='You roll ability 1 or 2 at random; the hidden one 1 in 20.',
            build='Build', tab_base='Default', tab_shop='With Kecleon Shop', moves='Moves', slot='SLOT', why='Why', start='Starting move', start2='Second starting move (Repertoire)', bans='Bans (Upgrades → Ban)',
            items='Item', items_note='Only one per run: dropped by bosses and locked chests.', cards='Level-up cards', evos='Move evolutions', evo_text='{move} evolves at max level if you have taken the {need} card at least once this run.',
            nature='Nature (Mint, 1,500)', ability='Ability (Capsule)', tms='TMs to buy', tm_note='The Kecleon Shop sells 8 TMs a day out of about 100; if none fits your partner, the last one is swapped for one it can learn.', total='Total', none_tm='No TM needed: its natural pool already has what matters.',
            nat_none='No Mint clearly improves its score: keep the nature it rolled.', ab_same='Its ability 1 is already the best of its abilities for the Judgment.', prev='Previous', next='Next', hordes_link='See its SurvivorTiers page',
            strategy='Strategy', verdict='Verdict', footer_data='Data and rules: PokéSurvivor source code (JPTER78) · Horde ranking: SurvivorTiers (@fildotai) · Portraits: PMD SpriteCollab (CC BY-NC 4.0) · Pokémon © Nintendo/Creatures/GAME FREAK.',
            footer_fan='Non-profit fan project, unaffiliated with the game’s authors or Nintendo.', generated='Generated on', not_available='—',
            flag_tm='TM useful today', tmToday='Kecleon Shop · today’s TMs ({d})', tmHint='Pokémon whose Kecleon Shop build asks for a TM on sale today', tmFor='{n} Pokémon use it in their build', moved='Ranks gained or lost with the latest game update', tmNone='None of today’s TMs appears in the recommended builds: none is worth buying for the Judgment today. There will be 8 new ones tomorrow.', tm8='the eighth may differ: if none fits your partner, the game swaps it (load your save to see it exactly)',
            changes='Changes', search='Name, no., move or ability',
            est='Lasts in the Judgment (estimate)',
            me='My save', meTitle='Load your save', meIntro='With your save the site marks the Pokémon you own, their upgrades and the ability and nature you rolled, and estimates your rank with them. Everything stays in this browser: nothing is sent anywhere.',
            meHow='1. Open pokesurvivor.com with your account. 2. Press F12 and open the “Console” tab. 3. Paste this line and press Enter: it copies your save to the clipboard. 4. Come back here and paste it in the box.',
            copy='Copy the line', copied='Copied', meLoad='Load', meClear='Remove save', close='Close', mePaste='Paste your save here (it starts with {"stats":…)', meError='That does not look like a PokéSurvivor save: it must be the whole JSON of the ps.cloud key.',
            meLoaded='Save of {name}: {n} Pokémon.', mine='My Pokémon', owned='Owned', notOwned='Not owned', ownedS='MINE', upgrades='Upgrades bought', yourRank='Your rank with your ability and nature', you='you',
            sort_you='Your rank', meBlock='Your save ({name})', meAbility='Your ability', meNature='Your nature', loading='Computing your rank…',
            meRank='With your ability and nature it would rank <b>{n}</b> of 966 (general rank: {base}). Upgrades and cards are assumed maxed; TMs you already taught are not counted.'),
}
ITEMS = {'es': dict(quickclaw=('Garra Rápida', '−20 % de recarga: más daño para farmear y, con Reflejos, Ataque Rápido encadena las embestidas y te deja invulnerable sin pausa ante las hordas y los legendarios.'),
                    leftovers=('Restos', 'Recuperas un 1,5 % de tu vida por segundo. El daño de Arceus es porcentual y puro: la regeneración porcentual es lo único que lo contrarresta.'),
                    focussash=('Banda Focus', 'Un golpe mortal te deja con 1 de vida (cada 60 s). Salva de un pilar o de un toque de Arceus hasta el minuto 35, cuando Arceus rompe tu objeto.'),
                    assaultvest=('Chaleco Asalto', '−20 % de daño recibido. Ayuda a llegar al minuto 30; en la Sentencia sobra en cuanto Coraza alcanza el tope del 80 %.')),
         'en': dict(quickclaw=('Quick Claw', '−20% cooldown: more damage to farm and, with Reflexes, Quick Attack chains its dashes and keeps you invulnerable nonstop against hordes and legendaries.'),
                    leftovers=('Leftovers', 'Recover 1.5% of your HP per second. Arceus’ damage is percentage-based and pure: percentage regeneration is the only thing that offsets it.'),
                    focussash=('Focus Sash', 'A lethal hit leaves you at 1 HP (every 60 s). Saves you from a pillar or an Arceus touch until minute 35, when Arceus breaks your item.'),
                    assaultvest=('Assault Vest', '−20% damage taken. Helps reach minute 30; in the Judgment it becomes redundant once Armor hits the 80% cap.'))}
CARDS = {'es': dict(cd='Reflejos', spd='Carrera', def_='Coraza', hp='Vigor', rgn='Síntesis', atk='Potencia', heal='Baya Zidra', mag='Imán', xp='Aprendizaje'),
         'en': dict(cd='Reflexes', spd='Sprint', def_='Armor', hp='Vigor', rgn='Synthesis', atk='Power', heal='Sitrus Berry', mag='Magnet', xp='Learning')}
NEED = {'es': NEED_NAME, 'en': {k: en(v) for k, v in NEED_NAME.items()}}

def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')
def slug(p): return f"{p['dex']}-{slugify(p['nameEn'])}"
def name(p, lang): return p['name'] if lang == 'es' else p['nameEn']
def mname(mid, lang): return MOVES[mid]['name'] if lang == 'es' else en(MOVES[mid]['name'])
def mdesc(mid, lang): return MOVES[mid]['desc'] if lang == 'es' else en(MOVES[mid]['desc'])
def aname(aid, lang):
    n = ABIL_NAMES.get(aid); return (n[0] if lang == 'es' else n[1]) if n else aid
def adesc(aid, types, lang):
    parts = describe(aid, types); return ' '.join(parts if lang == 'es' else [en(x) for x in parts])
def nname(nid, lang):
    n = NAT_BY[nid]; return n['n'][0] if lang == 'es' else n['n'][1]
def fmt(n, lang): return f'{n:,}'.replace(',', '.') if lang == 'es' else f'{n:,}'
def pct(x): return f'{round(x * 100)} %'
def dec(x, lang, nd=2): return f'{x:.{nd}f}'.replace('.', ',') if lang == 'es' else f'{x:.{nd}f}'
def andjoin(xs, lang):
    xs = list(xs); y = ' y ' if lang == 'es' else ' and '
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + y + xs[-1] if xs else ''
def typechip(t, lang): return f'<span class="type" style="--tc:{TC[t]}">{TYPE_NAME[lang][t]}</span>'

# ---------------- textos generados ----------------
def reason(m, p, var, lang):
    """Por qué va en la build, en una línea."""
    c = m['code']; es = lang == 'es'
    side = (('Ataque' if m.get('side') == 'physical' else 'At. Esp.') if es else ('Attack' if m.get('side') == 'physical' else 'Sp. Atk'))
    t = {'primary': ('Ataque principal: el que mejor farmea.', 'Main attack: your best farming move.'),
         'second': ('Farmea con el principal: fusiónalos en una grieta.', 'Farms alongside the main attack: fuse them at a rift.'),
         'buff': (f'Sube el {side}; solo sirve fusionado con el grupo.', f'Boosts {side}; only useful fused with the group.'),
         'dash': ('Cada embestida te deja 0,3 s invulnerable: úsalo cuando te rodeen.', 'Each dash makes you invulnerable for 0.3 s: use it when surrounded.'),
         'slow': (f"Frena un {m.get('pct')} % a los legendarios (no a Arceus).", f"Slows legendaries by {m.get('pct')}% (not Arceus)."),
         'stun': (f"Aturde a los legendarios {str(m.get('secs')).replace('.', ',')} s (no a Arceus).", f"Stuns legendaries for {m.get('secs')} s (not Arceus)."),
         'aquaring': ('Regenera hasta ~19 PS/s con sus mejoras.', 'Regenerates up to ~19 HP/s with its upgrades.'),
         'agility': ('Velocidad hasta el tope de 130.', 'Speed up to the 130 cap.')}.get(c)
    return t[0 if es else 1] if t else ''

def group_evos(b):
    out = {}
    for e in b['evos']: out.setdefault(e['need'], []).append(e['move'])
    return out

STAT_ICON = dict(cd='clock', spd='boot', def_='shield', hp='heart', rgn='sprout', atk='fist', heal='berry', mag='magnet', xp='book')
ITEM_SHORT = {'es': dict(quickclaw='−20 % de recarga', leftovers='+1,5 % de vida por segundo', focussash='Sobrevive a un golpe mortal (cada 60 s)', assaultvest='−20 % de daño recibido'),
              'en': dict(quickclaw='−20% cooldown', leftovers='+1.5% HP per second', focussash='Survive a lethal hit (every 60 s)', assaultvest='−20% damage taken')}

def cards_text(p, var, lang):
    """Cartas de nivel por prioridad (la del Consejero): (stat, nota corta)."""
    n = var['build']['spd_cards']; es = lang == 'es'
    out = [('cd', 'hasta 10' if es else 'up to 10'),
           ('spd', (f'{n} hasta 130' if es else f'{n} to 130') if n else ('ya en 130' if es else 'already at 130')),
           ('def_', 'hasta 12' if es else 'up to 12'),
           ('hp', '+20 de vida' if es else '+20 HP'),
           ('rgn', '+0,9 vida/s' if es else '+0.9 HP/s'),
           ('atk', 'al principio' if es else 'early on'),
           ('xp', 'al principio' if es else 'early on'),
           ('heal', 'con poca vida' if es else 'when low')]
    return out

def card_tiles(p, var, lang):
    tiles = ''.join(f'<li><img class="pix" src="../../../img/i/{STAT_ICON[k]}.svg" width="24" height="24" alt=""><b>{CARDS[lang][k]}</b><span>{note}</span></li>' for k, note in cards_text(p, var, lang))
    ev = group_evos(var['build'])
    evo = (f'<p class="small muted" style="margin:6px 0 0">{"Evolución (basta con coger la carta una vez)" if lang == "es" else "Evolution (take the card once)"}: ' + ' · '.join(f'{", ".join(esc(mname(m, lang)) for m in mvs)} → <b>{NEED[lang][need]}</b>' for need, mvs in ev.items()) + '</p>') if ev else ''
    return f'<ol class="tiles">{tiles}</ol>{evo}'

def strategy(p, lang):
    """Estrategia en tres párrafos cortos (lo general de Arceus está en la página La Sentencia)."""
    b = p['base']; s = p['shop']; inc = p['incoming']; es = lang == 'es'
    worst = [(t, v) for t, v in inc.items() if v > 1.0][:3]
    best = [(t, v) for t, v in inc.items() if v < 0.7][-3:]
    ht = p['hordes']['tier']; N = name(p, lang); tn = lambda t: TYPE_NAME[lang][t]
    num = lambda v: f'{v:.2f}'.replace('.', ',') if es else f'{v:.2f}'
    g1 = [m['id'] for m in b['build']['moves'] if m.get('slot', 1) == 1]
    ctl = [x for x in (b['slow'], b['stun']) if x and x not in g1]
    sp = b['build']['spd_cards']
    if es:
        via = {'S': 'llega al minuto 30 sobrado', 'A': 'llega al minuto 30 sin problema', 'B': 'llega al minuto 30 si la partida va limpia', 'C': 'le cuesta llegar al minuto 30', 'D': 'llegar al minuto 30 ya es un reto'}[ht]
        w = f" Le castigan {andjoin((f'{tn(t)} (×{num(v)})' for t, v in worst), lang)}." if worst else ''
        r = f" Aguanta bien {andjoin((f'{tn(t)} (×{num(v)})' for t, v in reversed(best)), lang)}." if best else ''
        out = [f"Tier {b['tier']} en la Sentencia y {ht} en hordas: {via}.{w}{r}",
               f"Antes del minuto 30, farmea: el nivel con el que llegas es lo que más alarga la Sentencia. Fusiona {andjoin((mname(x, lang) for x in g1), lang)} en el hueco 1 en cada grieta; Ataque Rápido, en su propio hueco, para cuando te rodeen"
               + (f"; {andjoin((mname(x, lang) for x in ctl), lang)} en los huecos que quedan" if ctl else '') + ". Con el grupo completo, no entres en más grietas.",
               ('Ya llega al tope de velocidad de 130' if sp == 0 else f"Necesita {'una carta' if sp == 1 else f'{sp} cartas'} de Carrera para el tope de 130")
               + f". {'Pequeño: le cuesta menos esquivar los pilares.' if p['r'] <= 11 else 'Grande: le cuesta más salir de los pilares.' if p['r'] >= 17 else ''}"]
        changes = andjoin([f"{mname(t['id'], lang)} (MT)" for t in s['tms']] + ([f"Menta {nname(s['nature'], lang)}"] if s['nature'] else []) + ([f"habilidad {aname(s['ability'], lang)}"] if s['ability'] != b['ability'] else []), lang)
        gain = round(s['est'] - b['est'])
        if changes: out.append(f"Tienda Kecleon: {changes}" + (f" (+{gain} s en la Sentencia)." if gain > 0 else ' (apenas cambia lo que aguanta).'))
    else:
        via = {'S': 'reaches minute 30 with ease', 'A': 'reaches minute 30 without trouble', 'B': 'reaches minute 30 if the run goes cleanly', 'C': 'struggles to reach minute 30', 'D': 'reaching minute 30 is already a challenge'}[ht]
        w = f" Weak to {andjoin((f'{tn(t)} (×{num(v)})' for t, v in worst), lang)}." if worst else ''
        r = f" Resists {andjoin((f'{tn(t)} (×{num(v)})' for t, v in reversed(best)), lang)}." if best else ''
        out = [f"Judgment tier {b['tier']} and horde tier {ht}: it {via}.{w}{r}",
               f"Before minute 30, farm: the level you arrive with is what extends the Judgment most. Fuse {andjoin((mname(x, lang) for x in g1), lang)} in slot 1 at every rift; keep Quick Attack in its own slot for when you get surrounded"
               + (f"; {andjoin((mname(x, lang) for x in ctl), lang)} in the remaining slots" if ctl else '') + ". Once the group is complete, skip further rifts.",
               ('Already at the 130 speed cap' if sp == 0 else f"Needs {'one Sprint card' if sp == 1 else f'{sp} Sprint cards'} for the 130 cap")
               + f". {'Small: pillars have less room to catch it.' if p['r'] <= 11 else 'Big: it takes longer to leave a pillar.' if p['r'] >= 17 else ''}"]
        changes = andjoin([f"{mname(t['id'], lang)} (TM)" for t in s['tms']] + ([f"{nname(s['nature'], lang)} Mint"] if s['nature'] else []) + ([f"{aname(s['ability'], lang)} ability"] if s['ability'] != b['ability'] else []), lang)
        gain = round(s['est'] - b['est'])
        if changes: out.append(f"Kecleon Shop: {changes}" + (f" (+{gain} s in the Judgment)." if gain > 0 else ' (barely changes how long it lasts).'))
    return out

def evidence_txt(p, lang):
    e = p.get('evidence') or {}
    if not e.get('nj'): return 'predicción del modelo (sin partidas reales)' if lang == 'es' else 'model prediction (no real runs)'
    w = round(e['weight'] * 100)
    return (f"{e['nj']} partidas reales (mediana {e['real']} s, pesan un {w} %)" if lang == 'es'
            else f"{e['nj']} real runs (median {e['real']} s, {w}% of the weight)")

def slow_pct(b):
    if not b['slow']: return 0
    return round(min(0.8, MOVES[b['slow']]['slow'] * (2 if b['ability'] == 'serene-grace' else 1)) * 100)

def verdict(p, lang):
    b = p['base']; ht = p['hordes']['tier']
    tools = (b['slow'] is not None) + (b['stun'] is not None) + (b['heal'] > 0)
    if lang == 'es':
        h = {'S': ' Además es de los mejores limpiando hordas: llega al minuto 30 sobrado.', 'A': ' Limpia hordas muy bien: llega al minuto 30 sin problema.', 'B': ' Limpiando hordas es del montón: llega al minuto 30 con una partida normal.',
             'C': ' Limpiando hordas flojea: llegar al minuto 30 cuesta.', 'D': ' Limpiando hordas es de los peores: llegar al minuto 30 es lo difícil.'}[ht]
        e = p.get('evidence') or {}; src = (f" Lo dicen sus {e['nj']} partidas reales más la predicción." if e.get('nj', 0) >= 10 else ' Es sobre todo una predicción: tiene pocas partidas reales.' if e.get('nj') else ' Es una predicción: no hay partidas reales suyas en la Sentencia.')
        if b['tier'] == 'S': return 'De los que más aguantan en la Sentencia.' + src + h
        if b['tier'] == 'A': return 'Aguanta muy bien la Sentencia.' + src + h
        if b['tier'] == 'B': return 'Aguanta la Sentencia un rato, pero hay quien lo hace mejor con menos esfuerzo.' + src + h
        if b['tier'] == 'C': return 'Justo en la Sentencia.' + src + h
        return 'De los que menos aguantan en la Sentencia. Juégalo por gusto, no por el ranking.' + src + h
    h = {'S': ' It is also among the best at clearing hordes: reaches minute 30 with ease.', 'A': ' Clears hordes very well: reaches minute 30 without trouble.', 'B': ' Average at clearing hordes: reaches minute 30 with a normal run.',
         'C': ' Weak at clearing hordes: reaching minute 30 is hard.', 'D': ' Among the worst at clearing hordes: reaching minute 30 is the real challenge.'}[ht]
    e = p.get('evidence') or {}; src = (f" Backed by its {e['nj']} real runs plus the prediction." if e.get('nj', 0) >= 10 else ' Mostly a prediction: few real runs.' if e.get('nj') else ' A prediction: no real Judgment runs of it.')
    if b['tier'] == 'S': return 'Among the longest-lasting in the Judgment.' + src + h
    if b['tier'] == 'A': return 'Lasts very well in the Judgment.' + src + h
    if b['tier'] == 'B': return 'Lasts a while in the Judgment, but others do it better with less effort.' + src + h
    if b['tier'] == 'C': return 'Marginal in the Judgment.' + src + h
    return 'Among the shortest-lasting in the Judgment. Play it for fun, not for the ranking.' + src + h

# ---------------- plantillas ----------------
def layout(lang, title, body, active, depth, desc='', extra_head='', path='', img='og.png'):
    U = UI[lang]; root = '../' * depth
    other = 'en' if lang == 'es' else 'es'
    url = f'{SITE}/{path}'
    extra_head += (f'<meta property="og:type" content="website"><meta property="og:site_name" content="Sentencia Tiers"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc or U["tagline"])}">'
                   f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="{"es_ES" if lang == "es" else "en_US"}">'
                   f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc or U["tagline"])}"><meta name="twitter:image" content="{SITE}/{img}">'
                   f'<link rel="canonical" href="{url}"><link rel="alternate" hreflang="{lang}" href="{url}"><link rel="alternate" hreflang="{other}" href="{SITE}/{path.replace(lang + "/", other + "/", 1)}">')
    # en móvil (≤720 px) las de clase rp se ocultan para que la barra quepa en una fila; Cambios queda en el pie
    nav = ''.join(f'<a href="{root}{lang}/{h}" class="{c}{" on" if k == active else ""}">{U[k]}</a>' for k, h, c in (('nav_tiers', '', ''), ('nav_judg', 'sentencia/', ''), ('changes', 'cambios/', 'rp')))
    nav += f'<a href="{root}{lang}/cooperativo/" class="{"on" if active == "nav_coop" else ""}">{U["nav_coop"]}</a>'
    nav += f'<a href="{STORE}" rel="noopener" title="{U["nav_adv_t"]}">{U["nav_adv"]}</a>'
    nav += f'<a class="rp" href="{REPO}" rel="noopener">{U["nav_repo"]}</a>'
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc or U['tagline'])}">
<meta name="theme-color" content="#07070a"><link rel="icon" href="{root}favicon.svg" type="image/svg+xml"><link rel="icon" href="{root}favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{root}apple-touch-icon.png"><link rel="manifest" href="{root}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css">{extra_head}
</head><body>
<header class="top"><div class="wrap"><a class="logo" href="{root}{lang}/">SENTENCIA<b>//</b>TIERS</a><nav class="nav">{nav}</nav>
<div class="lang"><a href="{root}es/{'' if depth == 1 else ''}" class="{'on' if lang == 'es' else ''}" data-l="es">ES</a><a href="{root}en/" class="{'on' if lang == 'en' else ''}" data-l="en">EN</a></div></div></header>
<main class="wrap">{body}</main>
<footer class="wrap"><div>{U['footer_data']}</div><div><a href="{root}{lang}/cambios/">{U['changes']}</a> · {U['footer_fan']} · {U['generated']} {R['generated']} · {U['updated']}: {R['game_commit']} · <a href="{REPO}" rel="noopener">GitHub</a></div></footer>
</body></html>'''

def index_page(lang):
    U = UI[lang]
    data = dict(t=dict(types=TYPE_NAME[lang], slow=U['slow'], stun=U['stun'], regen=U['regen'], slowS=U['slowS'], stunS=U['stunS'], regenS=U['regenS'], count=U['count'], none=U['none'], tier=U['tier'], legs=U['legs'], nonlegs=U['nonlegs'], all=U['all']),
                types=TYPES, typeColors=TC, list=[])
    for p in P:
        row = dict(dex=p['dex'], slug=slug(p), name=name(p, lang), alt=p['nameEn'] if lang == 'es' else p['name'], types=p['types'], leg=p['leg'], hp=p['stats']['hp'], spd=p['stats']['spd'], hordes=p['hordes']['rank'],
                   sc=p['base']['score'], abs={int(k): v for k, v in p['abil_scores'].items()}, ab=p['abils'])
        for k in ('base', 'shop'):
            v = p[k]; row[k] = dict(pos=v['pos'], tier=v['tier'], e=round(v['est']), c=v['comp'], slow=v['slow'], stun=v['stun'], regen=bool(v['heal']) or v['ability'] in ('regenerator', 'natural-cure', 'healer', 'shed-skin'))
        data['list'].append(row)
    data['an'] = {a: aname(a, lang) for p in P for a in p['abils'] if a}
    # ataques: índices en una lista común (compacto) para buscar por ataque y para las MT de hoy
    MV = sorted(MOVES); MI = {m: i for i, m in enumerate(MV)}
    data['mv'] = [mname(m, lang) for m in MV]
    data['tmAll'] = sorted(TM_MOVES)                       # como Object.keys(G.TM_MOVES).sort() en shop.js
    data['tmIdx'] = {m: MI.get(m, -1) for m in data['tmAll']}
    data['tmPrice'] = {m: TM_PRICE.get(m, 400) for m in data['tmAll']}
    for row, p in zip(data['list'], P):
        row['bm'] = sorted({MI[m['id']] for k in ('base', 'shop') for m in p[k]['build']['moves']})
        row['tm'] = [MI[t['id']] for t in p['tm']]
        row['st'] = [MI[t['id']] for t in p['shop']['tms']]
        if FRESH and p['dex'] in DELTA['d']: row['dl'] = DELTA['d'][p['dex']]
    data['natures'] = [dict(id=n['id'], n=nname(n['id'], lang)) for n in NAT_BY.values()]
    for k in ('owned', 'ownedS', 'upgrades', 'yourRank', 'you', 'meLoaded', 'meError', 'copied', 'tmToday', 'tmHint', 'tmFor', 'tm8', 'tmNone', 'moved'): data['t'][k] = U[k]
    n_leg = sum(1 for p in P if p['leg'])
    body = f'''<section class="hero"><div><span class="tag">// {U['tagline']}</span><h1>{U['title']}</h1><p>{U['intro']}</p></div>
<div class="kpis"><div class="kpi"><b>966</b>{U['pokemon']}</div><div class="kpi"><b>{len(R['legendary_pool'])}</b>{U['legs']} {'en el pool' if lang == 'es' else 'in the pool'}</div><div class="kpi"><b>{R['game_commit'].split(' ')[0]}</b>{U['updated']}</div></div></section>
<section class="controls cut">
<div class="row"><input id="q" type="search" placeholder="{U['search']}" aria-label="{U['search']}">
<div class="seg" id="mode" title="{esc(U['mode_help'])}"><button type="button" data-m="base" class="on">{U['mode_base']}</button><button type="button" data-m="shop" class="red">{U['mode_shop']}</button></div>
<button type="button" class="chip more" id="more" aria-expanded="false">{U['filters']} ▾</button>
<label class="adv">{U['sort']}<span style="display:flex;gap:4px"><select id="sort">{''.join(f'<option value="{k}">{v}</option>' for k, v in U['sort_opts'])}<option value="you">{U['sort_you']}</option></select><button type="button" class="chip" id="dir" title="asc/desc">↓</button><button type="button" class="chip" id="shuffle">{U['shuffle']}</button></span></label>
<label class="adv">{U['group']}<select id="group">{''.join(f'<option value="{k}">{v}</option>' for k, v in U['group_opts'])}</select></label><span class="seg view" id="view"><button type="button" data-v="grid" class="on" aria-pressed="true">{'Cartas' if lang == 'es' else 'Cards'}</button><button type="button" data-v="list" aria-pressed="false">{'Lista' if lang == 'es' else 'List'}</button></span><span class="count" id="count"></span></div>
<div class="row adv"><label>{U['tier']}<span class="chips" id="tiers">{''.join(f'<button type="button" class="chip" data-tier="{t}">{t}</button>' for t in 'SABCD')}</span></label>
<label>{U['filters']}<span class="chips" id="flags"><button type="button" class="chip" data-f="leg">{U['flag_leg']}</button><button type="button" class="chip" data-f="slow">{U['flag_slow']}</button><button type="button" class="chip" data-f="stun">{U['flag_stun']}</button><button type="button" class="chip" data-f="regen">{U['flag_regen']}</button><button type="button" class="chip" data-f="tmday" title="{esc(U['tmHint'])}">{U['flag_tm']}</button><button type="button" class="chip" data-f="mine" id="flag-mine" hidden>{U['mine']}</button><button type="button" class="chip me" id="me-btn">{U['me']}</button></span></label>
<label>{U['types']}<span class="chips" id="types"></span></label></div>
</section>
<section class="shopday"><img class="pix" src="../img/i/tm.svg" width="24" height="24" alt=""><div class="tmday" id="tmday"></div></section>
<dialog id="me-dlg" class="panel"><h3>{U['meTitle']}</h3><p class="small">{U['meIntro']}</p><ol class="small steps">{''.join(f'<li>{esc(x.strip())}</li>' for x in re.split(r'\d\. ', U['meHow']) if x.strip())}</ol>
<pre class="snippet"><code>{esc("copy(localStorage.getItem(Object.keys(localStorage).find(k => k.startsWith('ps.cloud.'))))")}</code></pre>
<div class="row"><button type="button" class="chip" id="me-copy">{U['copy']}</button></div>
<textarea id="me-text" rows="4" placeholder="{esc(U['mePaste'])}"></textarea><p class="small" id="me-err" style="color:var(--red);margin:4px 0"></p>
<div class="row"><button type="button" class="chip on" id="me-load">{U['meLoad']}</button><button type="button" class="chip" id="me-clear">{U['meClear']}</button><button type="button" class="chip" id="me-close">{U['close']}</button><span class="small muted" id="me-status"></span></div></dialog>
<div id="out"></div>
<script id="data" type="application/json">{json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')}</script>
<script src="../assets/save.js"></script><script src="../assets/app.js"></script>'''
    return layout(lang, f"{U['title']} · {U['tagline']}", body, 'nav_tiers', 1, U['intro'], path=f'{lang}/')

def bars(p, lang):
    U = UI[lang]; out = ['<div class="bars">']
    for k in ('T', 'U', 'A', 'D', 'S', 'Z', 'V'):
        if not R['weights'].get(k): continue
        b = p['base']['comp'][k]; s = p['shop']['comp'][k]; label, hint = COMP[lang][k]
        out.append(f'<div class="bar" title="{esc(hint)}"><span class="l">{label} </span><span class="track"><span class="fill base" style="width:{b * 100:.0f}%"></span><span class="fill shop" style="width:{s * 100:.0f}%"></span></span><span class="v">{dec(b, lang)} <em>{dec(s, lang)}</em></span></div>')
    out.append(f'</div><div class="legend"><span><i style="background:var(--yellow)"></i>{U["mode_base"]}</span><span><i style="background:var(--red)"></i>{U["mode_shop"]}</span><span class="muted">{"0–1 entre los 966" if lang == "es" else "0–1 across the 966"}</span></div>')
    return ''.join(out)

def build_panel(p, var, key, lang):
    U = UI[lang]; b = var['build']; es = lang == 'es'; I = '../../../img/i/'
    icon = lambda n, s=24: f'<img class="pix" src="{I}{n}.svg" width="{s}" height="{s}" alt="">'
    cards = []
    for i, m in enumerate(b['moves']):
        mv = MOVES[m['id']]; isTM = any(t['id'] == m['id'] for t in var.get('tms', []))
        tag = f'<span class="pill y" title="{CAT[lang].get(mv["cat"], "")}">{KIND[lang][mv["kind"]]}</span>' + (f'<span class="pill r">{"MT" if lang == "es" else "TM"}</span>' if isTM else '')
        cards.append(f'<article class="move" style="--tc:{TC[mv["type"]]}" title="{esc(mdesc(m["id"], lang))}">{icon("m-" + m["id"], 32)}<div><div class="n">{esc(mname(m["id"], lang))}</div>'
                     f'<div class="tg">{typechip(mv["type"], lang)}{tag}<span class="slot">{U["slot"]} {m.get("slot", i + 1)}</span></div><div class="why">{reason(m, p, var, lang)}</div></div></article>')
    shop_html = ''
    if key == 'shop':
        if var['nature']:
            nb = NAT_BY[var['nature']]
            nat = f"<b>{nname(var['nature'], lang)}</b> <span class=muted>+{STAT[lang][nb['up']]} −{STAT[lang][nb['down']]}</span>"
        else: nat = '<span class=muted>' + ('Ninguna: deja la que te tocó' if es else 'None: keep the one you rolled') + '</span>'
        if var['capsule']:
            ab = f"<b>{aname(var['ability'], lang)}</b> <span class=muted>{('Cápsula Habilidad Oculta · 5.000' if es else 'Hidden Ability Capsule · 5,000') if var['capsule'] == 'caph' else ('Cápsula Habilidad · 1.500' if es else 'Ability Capsule · 1,500')}</span>"
        else: ab = '<span class=muted>' + ('No hace falta: la 1 ya es la mejor' if es else 'Not needed: ability 1 is already best') + '</span>'
        if var['tms']:
            tms = ', '.join(f'<b>{esc(mname(t["id"], lang))}</b> <span class="price">{fmt(t["price"], lang)}</span>' for t in var['tms'])
        else: tms = '<span class=muted>' + ('Ninguna' if es else 'None') + '</span>'
        shop_html = (f'<div class="shoprow"><div>{icon("mint")}<span class="l">{"Menta" if es else "Mint"}</span>{nat}</div>'
                     f'<div>{icon("capsuleh" if var["capsule"] == "caph" else "capsule")}<span class="l">{"Habilidad" if es else "Ability"}</span>{ab}</div>'
                     f'<div>{icon("tm")}<span class="l">{"MT" if es else "TM"}</span>{tms}</div></div>')
    items = ''.join(f'<div class="item {"rec" if i == 0 else ""}">{icon(it, 32)}<div><span class="n">{ITEMS[lang][it][0]}</span><span class="small muted">{ITEM_SHORT[lang][it]}</span></div></div>' for i, it in enumerate(b['items']))
    na = U['not_available']
    kv = [(U['start'], esc(mname(b['start'], lang)) if b['start'] else na),
          ('Repertorio' if es else 'Repertoire', esc(mname(b['start2'], lang)) if b['start2'] else na),
          (icon('ban', 16) + ' ' + ('Vetos' if es else 'Bans'), ', '.join(esc(mname(x, lang)) for x in b['bans']) or na)]
    return f'''<div class="tab-panel" data-tab="{key}">
<div class="moves">{''.join(cards)}</div>
{shop_html}
<div class="g3">
<div class="panel"><h3>{'Antes de la partida' if es else 'Before the run'}</h3><dl class="kv">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in kv)}</dl></div>
<div class="panel"><h3>{U['items']}</h3><div class="items">{items}</div></div>
<div class="panel"><h3>{U['cards']}</h3>{card_tiles(p, var, lang)}</div>
</div>
</div>'''

def report_url(p, lang):
    """Incidencia con la plantilla «Error en una ficha» ya rellenada (Pokémon, idioma y parche)."""
    q = dict(template='ficha.yml', title=f"[Ficha] {name(p, lang)}", pokemon=f"{name(p, lang)} · {p['dex']:03d}",
             idioma='Español' if lang == 'es' else 'English', version=R['game_commit'])
    return f"{REPO}/issues/new?{urlencode(q)}"

def pokemon_page(p, lang, prev, nxt):
    U = UI[lang]; N = name(p, lang); b = p['base']; s = p['shop']; st = p['stats']; tn = TYPE_NAME[lang]
    abil_html = []
    for i, aid in enumerate(p['abils']):
        if not aid or (i == 1 and aid == p['abils'][0]): continue
        tags = (f'<span class="pill y">{U["default_ab"]}</span>' if i == 0 else '') + (f'<span class="pill c">{U["hidden_ab"]}</span>' if i == 2 else '') + (f'<span class="pill r">{U["rec_ab"]}</span>' if aid == s['ability'] and s['ability'] != b['ability'] else '')
        abil_html.append(f'<div class="a {"rec" if aid == s["ability"] else ""}"><span class="n">{esc(aname(aid, lang))} {tags}</span><span class="small muted">{esc(adesc(aid, p["types"], lang))}</span></div>')
    inc = ''.join(f'<div class="r"><span class="type" style="--tc:{TC[t]}">{tn[t]}</span><span class="track"><span class="fill" style="--tc:{TC[t]};width:{min(100, v / 2.4 * 100):.0f}%"></span></span><span class="v {"bad" if v > 1.05 else "good" if v < 0.75 else ""}">×{dec(v, lang)}</span></div>' for t, v in p['incoming'].items())
    hordes = p['hordes']
    stats = [(STAT[lang]['hp'], f"{st['hp']}"), (STAT[lang]['spd'], f"{st['spd']} <span class=muted>→ {b['S']}</span>"), (STAT[lang]['pa'], f"×{dec(st['pa'], lang)}"), (STAT[lang]['sa'], f"×{dec(st['sa'], lang)}"),
             (STAT[lang]['df'], f"{st['df']} <span class=muted>(×{dec(p['guard']['p'], lang)})</span>"), (STAT[lang]['sd'], f"{st['sd']} <span class=muted>(×{dec(p['guard']['s'], lang)})</span>"), (U['radius'], f"{dec(p['r'], lang, 1)} {U['px']}")]
    body = f'''<nav class="crumbs"><a href="../../">{U['back']}</a><span>/</span><span>{'Nº' if lang == 'es' else 'No.'} {p['dex']:03d}</span></nav>
<section class="head"><div class="pic cut"><img class="px" src="../../../img/p/{p['dex']}.png" alt="{esc(N)}" width="120" height="120"></div>
<div class="hd"><div class="sub"><h1>{esc(N)}</h1><span>{'Nº' if lang == 'es' else 'No.'} {p['dex']:03d}</span>{''.join(typechip(t, lang) for t in p['types'])}{'<span class="pill c">' + ('Legendario' if lang == 'es' else 'Legendary') + '</span>' if p['leg'] else ''}<span class="tier {b['tier']}">TIER {b['tier']}</span></div>
<div class="ranks"><div class="rank"><span class="l">{U['rank_base']}</span><span class="v">{b['pos']} <span class="small muted">/ 966</span></span></div>
<div class="rank shop"><span class="l">{U['rank_shop']}</span><span class="v">{s['pos']} <span class="small muted">/ 966 · {U['tier']} {s['tier']}</span></span></div>
<div class="rank est"><span class="l">{U['est']}</span><span class="v">{round(b['est'])} s</span><span class="ev">{evidence_txt(p, lang)}</span></div>
<div class="rank ext"><span class="l">{U['rank_hordes']}</span><span class="v">{hordes['rank'] or '—'} <span class="small muted">/ 966 · {U['tier']} {hordes['tier']}</span></span></div></div>
<div class="verdict"><b class="up" style="color:var(--yellow)">{U['verdict']}:</b> {verdict(p, lang)}</div>
<section id="me" class="panel me" hidden data-dex="{p['dex']}" data-pos="{b['pos']}" data-sc="{b['score']}" data-scores="../../../assets/scores.json" data-abils="{esc(json.dumps(p['abils']))}" data-names="{esc(json.dumps([aname(a, lang) if a else '' for a in p['abils']], ensure_ascii=False))}" data-abs="{esc(json.dumps({int(k): v for k, v in p['abil_scores'].items()}))}" data-natures="{esc(json.dumps([dict(id=n['id'], n=nname(n['id'], lang)) for n in NAT_BY.values()], ensure_ascii=False))}" data-t="{esc(json.dumps(dict(title=U['meBlock'], owned=U['owned'], notOwned=U['notOwned'], upgrades=U['upgrades'], ability=U['meAbility'], hidden=U['hidden_ab'].lower(), nature=U['meNature'], loading=U['loading'], rank=U['meRank']), ensure_ascii=False))}"></section></div></section>
<h2>{U['strategy']}</h2><div class="strat">{''.join(f'<p>{x}</p>' for x in strategy(p, lang))}</div>
<div class="g2">
<div class="panel"><h3>{U['components']}</h3>{bars(p, lang)}</div>
<div class="panel"><h3>{U['stats']}</h3><dl class="kv2">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in stats)}</dl>
</div>
<div class="panel"><h3>{U['incoming']}</h3><div class="inc">{inc}</div></div>
<div class="panel"><h3>{U['abilities']}</h3><div class="abil">{''.join(abil_html)}</div><p class="small muted" style="margin:6px 0 0">{U['ab_note']}</p></div></div>
<div class="tabs"><h2 style="margin:0;align-self:end;padding-right:14px">{U['build']}</h2><button data-tab="base">{U['tab_base']}</button><button data-tab="shop" class="red">{U['tab_shop']}</button></div>
{build_panel(p, b, 'base', lang)}{build_panel(p, s, 'shop', lang)}
<nav class="pager">{f'<a href="../{slug(prev)}/">← #{prev["base"]["pos"]} {esc(name(prev, lang))}</a>' if prev else '<span></span>'}<a href="../../">{U['back']}</a>{f'<a href="../{slug(nxt)}/">#{nxt["base"]["pos"]} {esc(name(nxt, lang))} →</a>' if nxt else '<span></span>'}</nav>
<p class="report"><a href="{esc(report_url(p, lang))}" rel="noopener" target="_blank">{'¿Algo no cuadra en esta ficha? Avísanos' if lang == 'es' else 'Something off on this page? Let us know'} ↗</a></p>
<script src="../../../assets/save.js"></script><script src="../../../assets/page.js"></script>'''
    title = f"{N} · {U['title']}: tier {b['tier']}, {'puesto' if lang == 'es' else 'rank'} {b['pos']}"
    desc = (f"{N} en la Sentencia de Arceus: tier {b['tier']} (puesto {b['pos']} de 966), build, habilidades, objetos y estrategia." if lang == 'es' else f"{N} in the Judgment of Arceus: tier {b['tier']} (rank {b['pos']} of 966), build, abilities, items and strategy.")
    return layout(lang, title, body, None, 3, desc, path=f'{lang}/pokemon/{slug(p)}/', img=f"img/og/{p['dex']}.png")

def prose_page(lang, key, title, html_body, path, wide=False):
    return layout(lang, f"{title} · {UI[lang]['title']}", f'<article class="prose{" wide" if wide else ""}">{html_body}</article>', key, 2, path=path)

def judgment_text(lang):
    """La Sentencia en una pantalla: tres columnas (Arceus, legendarios, qué hacer). Todo sale de judgment.js y compañía."""
    if lang == 'es':
        return '''<h1>La Sentencia de Arceus</h1><p class="muted">Minuto 30: Arceus te lleva a una arena redonda (768 px de radio) de la que no se sale. Es invencible y cada 5 s acude un legendario. El ranking cuenta el tiempo que aguantas y el daño que le haces. Todo lo de aquí sale del código del juego.</p>
<div class="g3 jd">
<div class="panel"><h3>Arceus</h3>
<table class="moves-t"><tr><th>Ataque</th><th>Daño</th><th>Aviso</th></tr>
<tr><td>Pilares (4–10, radio 44 px)</td><td>30 %</td><td>1,25 s</td></tr>
<tr><td>Rayos en cruz (4, luego 8)</td><td>35 %</td><td>1,1 s</td></tr>
<tr><td>Onda (si estás a &lt;210 px)</td><td>40 %</td><td>0,85 s</td></tr>
<tr><td>Toque</td><td>40 → 100 %</td><td>—</td></tr></table>
<ul class="plain small">
<li><b>Daño puro en % de vida:</b> ignora tipos, defensa, Coraza, habilidad e invulnerabilidad. Solo lo compensan esquivar, regenerar y la Banda Focus.</li>
<li><b>No se le deja atrás:</b> corre al 74 % de tu velocidad y a los 37 s ya va a ×1,22. A los 5 min acelera sin tope.</li>
<li><b>Tope suave de 130:</b> lo que pase cuenta un 25 %.</li>
<li><b>Sus pausas</b> (1–1,5 s tras cada ataque) son tu distancia.</li>
<li><b>Minuto 35:</b> rompe tu objeto.</li></ul></div>
<div class="panel"><h3>Los legendarios</h3><ul class="plain small">
<li>Uno cada 5 s entre 86, cada uno con <b>+25 % de vida</b> y <b>+15 % de daño</b> que el anterior.</li>
<li>La vida del primero son <b>3 s de tu daño</b>: tu DPS casi no cambia nada; desde el tercero se acumulan.</li>
<li>Corren al menos al 80 % de tu velocidad. Psíquico, Eléctrico, Fantasma, Hada, Fuego, Agua, Hielo y Dragón disparan desde 300 px; el resto embiste.</li>
<li>Su daño sí pasa por tus tipos, defensa, Coraza (tope 80 %) y habilidad.</li>
<li><b>Frenazos</b> al 100 %, <b>aturdimientos</b> al 35 % (uno aturdido no daña al tocar). El empuje no les afecta.</li>
<li>Ataque Rápido te deja 0,3 s invulnerable a sus golpes (no a los de Arceus).</li></ul>
<h3 style="margin-top:12px">Daño a Arceus</h3><p class="small">Cuenta un 5 % (1 % a los 10 min) y solo le apuntas sin legendarios vivos. No alarga la Sentencia.</p></div>
<div class="panel"><h3>Qué hacer</h3><ol class="plain small">
<li><b>Llega con nivel:</b> antes del minuto 30 farmea. Cada nivel extra da Vigor o Síntesis sin tope, y es lo que más explica cuánto aguantas.</li>
<li><b>Muévete siempre:</b> sal de cada círculo en cuanto aparece y gana distancia en sus pausas.</li>
<li><b>Distancia:</b> 250–400 px de Arceus (entre rayos hay ~200 px de hueco) y lejos del borde.</li>
<li><b>Legendarios encima:</b> Ataque Rápido para atravesarlos; frena o aturde al grupo, no intentes matarlos desde el tercero.</li>
<li><b>Cartas:</b> Reflejos, Coraza, Vigor y Síntesis; Carrera solo hasta 130.</li>
<li><b>Objeto:</b> Garra Rápida, Restos o Banda Focus (hasta el minuto 35).</li></ol></div>
</div>'''
    return '''<h1>The Judgment of Arceus</h1><p class="muted">Minute 30: Arceus takes you to a round arena (768 px radius) you cannot leave. It is invincible and a legendary shows up every 5 s. The ranking counts how long you last and how much damage you deal to it. Everything here comes from the game’s code.</p>
<div class="g3 jd">
<div class="panel"><h3>Arceus</h3>
<table class="moves-t"><tr><th>Attack</th><th>Damage</th><th>Warning</th></tr>
<tr><td>Pillars (4–10, 44 px radius)</td><td>30%</td><td>1.25 s</td></tr>
<tr><td>Cross beams (4, then 8)</td><td>35%</td><td>1.1 s</td></tr>
<tr><td>Shockwave (within 210 px)</td><td>40%</td><td>0.85 s</td></tr>
<tr><td>Touch</td><td>40 → 100%</td><td>—</td></tr></table>
<ul class="plain small">
<li><b>Pure % HP damage:</b> ignores types, defense, Armor, ability and invulnerability. Only dodging, regeneration and the Focus Sash offset it.</li>
<li><b>You cannot outrun it:</b> it starts at 74% of your speed and after 37 s runs at ×1.22. After 5 min it accelerates without limit.</li>
<li><b>Soft cap at 130:</b> anything above counts 25%.</li>
<li><b>Its pauses</b> (1–1.5 s after each attack) are your distance.</li>
<li><b>Minute 35:</b> it breaks your item.</li></ul></div>
<div class="panel"><h3>The legendaries</h3><ul class="plain small">
<li>One every 5 s out of 86, each with <b>+25% HP</b> and <b>+15% damage</b> over the previous one.</li>
<li>The first one’s HP is <b>3 s of your damage</b>: your DPS barely matters; from the third on they pile up.</li>
<li>They run at least at 80% of your speed. Psychic, Electric, Ghost, Fairy, Fire, Water, Ice and Dragon shoot from 300 px; the rest charge.</li>
<li>Their damage does go through your types, defense, Armor (80% cap) and ability.</li>
<li><b>Slows</b> land at 100%, <b>stuns</b> at 35% (a stunned one deals no contact damage). Knockback does nothing.</li>
<li>Quick Attack leaves you 0.3 s invulnerable to their hits (not to Arceus’).</li></ul>
<h3 style="margin-top:12px">Damage to Arceus</h3><p class="small">5% of it counts (1% after 10 min) and you only target it with no legendary alive. It does not extend the Judgment.</p></div>
<div class="panel"><h3>What to do</h3><ol class="plain small">
<li><b>Arrive high-level:</b> farm before minute 30. Every extra level gives uncapped Vigor or Synthesis, and your level is what explains survival most.</li>
<li><b>Keep moving:</b> leave every circle as soon as it appears and gain distance during its pauses.</li>
<li><b>Distance:</b> 250–400 px from Arceus (~200 px gap between beams) and off the edge.</li>
<li><b>Legendaries on you:</b> Quick Attack through them; slow or stun the group, do not try to kill them after the third.</li>
<li><b>Cards:</b> Reflexes, Armor, Vigor and Synthesis; Sprint only up to 130.</li>
<li><b>Item:</b> Quick Claw, Leftovers or Focus Sash (until minute 35).</li></ol></div>
</div>'''

ROOT_INDEX = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Sentencia Tiers</title>
<meta name="description" content="Tier list de PokéSurvivor para la Sentencia de Arceus · PokéSurvivor tier list for the Judgment of Arceus"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="apple-touch-icon.png"><link rel="manifest" href="site.webmanifest">
<link rel="alternate" hreflang="es" href="{SITE}/es/"><link rel="alternate" hreflang="en" href="{SITE}/en/"><link rel="alternate" hreflang="x-default" href="{SITE}/es/">
<link rel="stylesheet" href="assets/style.css"><script>var l=(navigator.language||'es').slice(0,2);location.replace((l==='es'?'es':'en')+'/'+location.hash);</script></head>
<body><main class="wrap" style="padding-top:60px"><h1 style="color:var(--yellow)">SENTENCIA//TIERS</h1><p><a href="es/">Español</a> · <a href="en/">English</a></p></main></body></html>'''
FAVICON = None   # docs/favicon.svg (Poké Ball en la rueda de Arceus) y sus PNG se mantienen a mano; gen.py no los toca.

def coop_text(lang):
    path = os.path.join(ROOT, 'data', 'coop.json')
    if not os.path.exists(path): return '<p>—</p>'
    C = json.load(open(path, encoding='utf-8'))
    PB = {p['dex']: p for p in R['pokemon']}
    es = lang == 'es'
    ROLE = {'portador': ('portador', 'carry'), 'farmeo': ('farmeo', 'farmer'), 'control': ('control', 'control'), 'apoyo': ('apoyo', 'support')}
    BRIEF = {'portador': ('Aguanta: tira del grupo en la Sentencia.', 'Survives: anchors the group in the Judgment.'),
             'farmeo': ('Limpia hordas: sube el nivel de todos.', 'Clears hordes: levels up everyone.'),
             'control': ('Frena y aturde a los legendarios.', 'Slows and stuns the legendaries.'),
             'apoyo': ('Rápido: revive a los caídos y abre los cofres.', 'Fast: revives fallen allies and grabs chests.')}
    rl = lambda r: ' '.join(f'<span class="pill">{ROLE[x][0 if es else 1]}</span>' for x in r)
    link = lambda d: f'<a href="../pokemon/{slug(PB[d])}/">{esc(name(PB[d], lang))}</a>'
    pc = lambda v: f'{round(v * 100)}'
    def member(d, role):
        p = PB[d]; r = C['pokemon'][str(d)]
        brief = BRIEF[role][0 if es else 1] if role else ('Un poco de todo.' if es else 'A bit of everything.')
        mv = ''.join(f'<img class="pix" src="../../img/i/m-{m["id"]}.svg" width="24" height="24" alt="{esc(mname(m["id"], lang))}" title="{esc(mname(m["id"], lang))}">' for m in p['base']['build']['moves'])
        return (f'<div class="mem"><a class="pic" href="../pokemon/{slug(p)}/"><img class="px" src="../../img/p/{d}.png" alt="" width="56" height="56" loading="lazy"></a>'
                f'<div><div class="nm">{link(d)} <span class="tier {r["tier"]}">{r["tier"]}</span>{rl(([role] if role else []) + [x for x in r['roles'] if x != role])}</div><div class="small muted">{brief}</div><div class="mvs">{mv}</div></div></div>')
    def roles_of(t):
        # un papel por miembro: primero los que solo uno del equipo cubre (control, farmeo, portador)
        out, used = {}, set()
        for d in sorted(t['members'], key=lambda d: len(C['pokemon'][str(d)]['roles'])):
            rs = C['pokemon'][str(d)]['roles']
            out[d] = next((x for x in ('control', 'apoyo', 'farmeo', 'portador') if x in rs and x not in used), rs[0] if rs else None)
            used.add(out[d])
        return out
    def teams(n):
        return '<div class="teams">' + ''.join(f'<div class="team panel">{"".join(member(d, roles_of(t)[d]) for d in t["members"])}</div>' for t in C['teams'][str(n)]) + '</div>'
    def tabs(labels):
        # pestañas sin JavaScript (radio + :checked): un tamaño de equipo a la vista
        heads = ''.join(f'<input type="radio" name="ct" id="ct{n}"{" checked" if n == 2 else ""}><label for="ct{n}">{lab}</label>' for n, lab in labels)
        return f'<div class="ctabs">{heads}' + ''.join(f'<div class="cpanel p{n}">{teams(n)}</div>' for n, _ in labels) + '</div>'
    rows = ''.join(f'<tr><td>{r["pos"]}</td><td><span class="tier {r["tier"]}">{r["tier"]}</span></td><td>{link(r["dex"])}</td><td>{r["solo"]}</td><td>{pc(r["c"]["surv"])}</td><td>{pc(r["c"]["farm"])}</td><td>{pc(r["c"]["ctl"])}</td><td>{pc(r["c"]["spd"])}</td><td>{rl(r["roles"])}</td></tr>'
                   for r in (C['pokemon'][str(d)] for d in C['order'][:120]))
    hd = ('<tr><th>#</th><th>Tier</th><th>Pokémon</th><th>Puesto solo</th><th>Aguante</th><th>Farmeo</th><th>Control</th><th>Velocidad</th><th>Papel</th></tr>' if es else
          '<tr><th>#</th><th>Tier</th><th>Pokémon</th><th>Solo rank</th><th>Survival</th><th>Farm</th><th>Control</th><th>Speed</th><th>Role</th></tr>')
    if es:
        return f'''<h1>Cooperativo</h1><p class="muted">En grupo la experiencia es de todos (con un compañero que mata tanto como tú, el equipo sube de nivel un 25 % más rápido), el control protege a todos, a un caído lo levantas quedándote 3 s a su lado y Arceus persigue al más cercano, así que separarse reparte la presión. Por eso aquí también cuentan farmear, controlar y la velocidad: antes del minuto 30 no hay tope, y un Pokémon rápido hace de apoyo, llegando antes a revivir y a los cofres.</p>
<h2>Equipos recomendados</h2>{tabs([(2, 'Dúos'), (3, 'Tríos'), (4, 'De cuatro')])}
<h2>Los 120 mejores en grupo</h2><p class="small muted">Percentiles entre los 966 (100 = el mejor).</p><div class="scroll"><table class="moves-t">{hd}{rows}</table></div>'''
    return f'''<h1>Co-op</h1><p class="muted">In a group, experience is shared (with a partner who kills as much as you, the team levels up 25% faster), control protects everyone, a downed partner gets back up after you stand next to them for 3 s, and Arceus chases the nearest player, so splitting up spreads the pressure. That is why farming, control and speed count here too: before minute 30 there is no speed cap, and a fast Pokémon plays support, first to revive and to the chests.</p>
<h2>Recommended teams</h2>{tabs([(2, 'Duos'), (3, 'Trios'), (4, 'Fours')])}
<h2>Top 120 in a group</h2><p class="small muted">Percentiles across the 966 (100 = best).</p><div class="scroll"><table class="moves-t">{hd}{rows}</table></div>'''

def changes_text(lang):
    """Historial de data/CHANGELOG.md (lo escribe update.py, en español)."""
    path = os.path.join(ROOT, 'data', 'CHANGELOG.md')
    md = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    out = ['<h1>' + ('Cambios del ranking' if lang == 'es' else 'Ranking changes') + '</h1>',
           '<p class="muted">' + ('Cada día se comprueba si PokéSurvivor ha cambiado; si el cambio mueve el ranking, la web se actualiza sola y queda apuntado aquí.' if lang == 'es'
            else 'Every day the site checks whether PokéSurvivor changed; if the change moves the ranking, the site updates itself and it is logged here (entries are in Spanish).') + '</p>']
    if DELTA:
        d = DELTA['d']; name_ = lambda dex: name(BY[dex], lang)
        def tbl(i, title):
            ups = sorted(((v[i], k) for k, v in d.items() if v[i] > 0), reverse=True)[:12]
            downs = sorted(((v[i], k) for k, v in d.items() if v[i] < 0))[:12]
            if not ups and not downs: return ''
            row = lambda v, k: f'<tr><td><a href="../pokemon/{slug(BY[k])}/">{esc(name_(k))}</a></td><td>{BY[k][("base", "shop")[i]]["pos"]}</td><td class="{"up" if v > 0 else "down"}">{"▲" if v > 0 else "▼"} {abs(v)}</td></tr>'
            hd = '<tr><th>Pokémon</th><th>' + ('Puesto' if lang == 'es' else 'Rank') + '</th><th>Δ</th></tr>'
            empty = '<tr><td colspan="3" class="muted">—</td></tr>'
            return (f'<div><h3>{title} <span class="up">▲</span></h3><table class="moves-t">{hd}{"".join(row(v, k) for v, k in ups) or empty}</table></div>'
                    f'<div><h3>{title} <span class="down">▼</span></h3><table class="moves-t">{hd}{"".join(row(v, k) for v, k in downs) or empty}</table></div>')
        out.append('<h2>' + ('Quién sube y quién baja' if lang == 'es' else 'Who rises and who falls') + '</h2>')
        out.append('<p class="muted">' + (f"Comparado con el ranking del {DELTA['prev']['date']} (juego {esc(DELTA['prev']['game'])}): {len(d)} Pokémon cambian de puesto. En la tier list salen con flecha durante 7 días." if lang == 'es'
                   else f"Compared with the ranking of {DELTA['prev']['date']} (game {esc(DELTA['prev']['game'])}): {len(d)} Pokémon change rank. They carry an arrow in the tier list for 7 days.") + '</p>')
        out.append('<div class="movers">' + tbl(0, UI[lang]['mode_base']) + tbl(1, UI[lang]['mode_shop']) + '</div>')
    ul = 0
    for line in md.splitlines():
        if line.startswith('# '): continue
        ind = len(line) - len(line.lstrip(' ')); t = line.strip()
        lvl = 0 if not t.startswith('- ') else (2 if ind >= 2 else 1)
        while ul > lvl: out.append('</ul>'); ul -= 1
        if t.startswith('## '): out.append(f'<h2>{esc(t[3:])}</h2>')
        elif t.startswith('- '):
            while ul < lvl: out.append('<ul>'); ul += 1
            item = esc(t[2:]).replace('→', '<span style="color:var(--yellow)">→</span>')
            if 'ATENCIÓN' in item: item = f'<span style="color:var(--red)">{item}</span>'
            out.append(f'<li>{item}</li>')
        elif t: out.append(f'<p>{esc(t)}</p>')
    while ul: out.append('</ul>'); ul -= 1
    if len(out) == 2: out.append('<p>' + ('Aún no hay cambios.' if lang == 'es' else 'No changes yet.') + '</p>')
    return ''.join(out)

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='\n').write(text)

def main():
    t0 = time.time()
    import coop; coop.main()          # data/coop.json (página Cooperativo)
    import icons; icons.main()        # docs/img/i: iconos del juego (objetos, cartas, ataques)
    import og; og.main()              # docs/img/og: tarjeta para compartir de cada Pokémon
    for lang in LANGS:
        shutil.rmtree(os.path.join(DOCS, lang), ignore_errors=True)
    write(os.path.join(DOCS, 'index.html'), ROOT_INDEX)
    write(os.path.join(DOCS, '.nojekyll'), '')
    write(os.path.join(DOCS, 'robots.txt'), f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    write(os.path.join(DOCS, '404.html'), ROOT_INDEX.replace('location.replace(', 'location.replace("/sentencia-tiers/"+').replace("+'/'+location.hash", "+'/'"))
    urls = []
    order = sorted(P, key=lambda p: p['base']['pos'])
    for lang in LANGS:
        write(os.path.join(DOCS, lang, 'index.html'), index_page(lang)); urls.append(f'{SITE}/{lang}/')
        write(os.path.join(DOCS, lang, 'sentencia', 'index.html'), prose_page(lang, 'nav_judg', UI[lang]['nav_judg'], judgment_text(lang), f'{lang}/sentencia/', wide=True)); urls.append(f'{SITE}/{lang}/sentencia/')
        # el método se explica en el repositorio (MODELO.md); los enlaces antiguos a /metodo/ llevan allí
        write(os.path.join(DOCS, lang, 'metodo', 'index.html'), f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={REPO}/blob/main/MODELO.md"><link rel="canonical" href="{REPO}/blob/main/MODELO.md"><a href="{REPO}/blob/main/MODELO.md">MODELO.md</a>')
        write(os.path.join(DOCS, lang, 'cambios', 'index.html'), prose_page(lang, 'changes', UI[lang]['changes'], changes_text(lang), f'{lang}/cambios/', wide=True)); urls.append(f'{SITE}/{lang}/cambios/')
        write(os.path.join(DOCS, lang, 'cooperativo', 'index.html'), prose_page(lang, 'nav_coop', UI[lang]['nav_coop'], coop_text(lang), f'{lang}/cooperativo/', wide=True)); urls.append(f'{SITE}/{lang}/cooperativo/')
        for i, p in enumerate(order):
            prev = order[i - 1] if i > 0 else None; nxt = order[i + 1] if i + 1 < len(order) else None
            write(os.path.join(DOCS, lang, 'pokemon', slug(p), 'index.html'), pokemon_page(p, lang, prev, nxt)); urls.append(f'{SITE}/{lang}/pokemon/{slug(p)}/')
    # puntuaciones para "Tu partida": dex -> {b: general, a: {hueco de habilidad: [25 naturalezas ×10000]}}
    write(os.path.join(DOCS, 'assets', 'scores.json'), json.dumps({p['dex']: {'b': p['base']['score'], 'a': p['an_scores']} for p in P}, separators=(',', ':')))
    # datos del Consejero (extensión del navegador): docs/assets/advisor.json y extension/data.js
    advisor.write_all(R, slug, DOCS, os.path.join(ROOT, 'extension'))
    write(os.path.join(DOCS, 'sitemap.xml'), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    print(f'{len(urls)} páginas en {time.time() - t0:.1f}s')

if __name__ == '__main__':
    main()
