"""Genera la web estática (docs/) a partir de data/ranking.json. Uso: python -I gen.py"""
import json, os, re, sys, html, shutil, unicodedata, time
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
        'en': dict(projectile='projectile', melee='melee', beam='beam', orbit='orbit', nova='nova', aura='aura', buff='buff', boomerang='boomerang', chain='chain', mine='mines',
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
 'es': dict(title='Sentencia Tiers', tagline='Tier list de PokéSurvivor para la Sentencia de Arceus', nav_tiers='Tiers', nav_judg='La Sentencia', nav_method='Método', nav_repo='Código',
            intro='Los 966 Pokémon ordenados solo por lo que aguantan en la Sentencia de Arceus (minuto 30). Calculado a partir del código del juego: frenazos, aturdimientos, defensas frente a los 86 legendarios que acuden, regeneración, velocidad con tope y tamaño. Lo que limpian antes del minuto 30 se indica en cada ficha, no puntúa.',
            updated='Parche del juego', pokemon='Pokémon', legs='Legendarios', nonlegs='No legendarios', all='Todos', tier='Tier', sort='Ordenar por', group='Agrupar por',
            mode_base='Por defecto', mode_shop='Tienda Kecleon', count='{n} de {m} Pokémon', none='Ningún Pokémon cumple los filtros.', shuffle='Al azar', filters='Filtros', types='Tipos',
            sort_opts=[('pos', 'Puesto'), ('name', 'Nombre'), ('dex', 'Nº Pokédex'), ('hordes', 'Ranking en hordas'), ('T', 'Aguante'), ('U', 'Control'), ('A', 'Regeneración'), ('D', 'Daño'), ('S', 'Velocidad'), ('Z', 'Tamaño'), ('hp', 'Vida'), ('spd', 'Velocidad base'), ('rnd', 'Al azar')],
            group_opts=[('tier', 'Tier'), ('type', 'Tipo'), ('leg', 'Legendarios'), ('none', 'Sin agrupar')],
            flag_leg='Solo legendarios', flag_slow='Con frenazo', flag_stun='Con aturdimiento', flag_regen='Con regeneración', slow='Frenazo', stun='Aturdimiento', regen='Regeneración', slowS='SLOW', stunS='STUN', regenS='REGEN',
            mode_help='Por defecto: habilidad 1, naturaleza neutra y solo sus ataques naturales. Tienda Kecleon: la mejor habilidad (Cápsula), la mejor naturaleza (Menta) y las MT que le sirven.',
            back='Tier list', rank_base='Puesto · por defecto', rank_shop='Puesto · con Tienda Kecleon', rank_hordes='Ranking en hordas (SurvivorTiers)', of='de', stats='Estadísticas del juego', guard='Daño que recibe (defensa)',
            radius='Radio de colisión', px='px', speed_eff='Velocidad efectiva en la Sentencia', score='Puntuación', components='Por qué está aquí', incoming='Daño recibido por tipo (pool de legendarios)',
            abilities='Habilidades', default_ab='Habilidad 1 · por defecto', hidden_ab='Oculta', rec_ab='Recomendada', ab_note='A cada cuenta le toca al azar la habilidad 1 o la 2 (50 %), y la oculta 1 de cada 20. La Cápsula Habilidad (1.500) cambia entre la 1 y la 2; la Cápsula Habilidad Oculta (5.000) pone la oculta.',
            build='Build', tab_base='Por defecto', tab_shop='Con Tienda Kecleon', moves='Movimientos', slot='HUECO', why='Por qué', start='Movimiento inicial', start2='Segundo movimiento inicial (Repertorio)', bans='Vetos (Mejoras → Veto)',
            items='Objeto equipable', items_note='Solo se lleva uno por partida: los sueltan los jefes y los cofres con candado.', cards='Cartas de nivel: prioridad', evos='Evoluciones de movimiento', evo_text='{move} evoluciona al nivel máximo si en la partida has cogido al menos una vez la carta {need}.',
            nature='Naturaleza (Menta, 1.500)', ability='Habilidad (Cápsula)', tms='MT a comprar', tm_note='La Tienda Kecleon vende 8 MT al día entre unas 100; si ninguna le sirve a tu compañero, la última se cambia por una que sí aprenda.', total='Total', none_tm='No necesita ninguna MT: su pool natural ya tiene lo importante.',
            nat_none='Ninguna Menta mejora claramente su puntuación: mejor dejar la naturaleza que le tocó.', ab_same='Su habilidad 1 ya es la mejor de las suyas para la Sentencia.', prev='Anterior', next='Siguiente', hordes_link='Ver su ficha en SurvivorTiers',
            strategy='Estrategia', verdict='Veredicto', footer_data='Datos y reglas: código de PokéSurvivor (JPTER78) · Ranking en hordas: SurvivorTiers (@fildotai) · Retratos: PMD SpriteCollab (CC BY-NC 4.0) · Pokémon © Nintendo/Creatures/GAME FREAK.',
            footer_fan='Proyecto de fans sin ánimo de lucro, sin relación con los autores del juego ni con Nintendo.', generated='Generado el', not_available='—',
            flag_tm='MT útil hoy', tmToday='MT a la venta hoy en la Tienda Kecleon ({d})', tmHint='Pokémon a los que su build con Tienda Kecleon les pide una MT que se vende hoy', tmFor='{n} Pokémon la usan en su build', moved='Puestos que ha subido o bajado con la última actualización del juego', tmNone='Hoy ninguna de las MT a la venta aparece en las builds recomendadas: no merece la pena comprar ninguna para la Sentencia. Mañana habrá otras 8.', tm8='la octava puede ser otra: si ninguna le sirve a tu compañero, el juego la cambia (carga tu partida para verla exacta)',
            changes='Cambios', search='Nombre, nº, ataque o habilidad',
            me='Mi partida', meTitle='Cargar tu partida', meIntro='Con tu partida la web marca los Pokémon que tienes, sus mejoras y la habilidad y naturaleza que te tocaron, y calcula tu puesto aproximado con ellas. Todo se queda en este navegador: no se envía a ningún sitio.',
            meHow='1. Abre pokesurvivor.com con tu cuenta. 2. Pulsa F12 y entra en la pestaña «Console». 3. Pega esta línea y pulsa Intro: copia tu partida al portapapeles. 4. Vuelve aquí y pégala en el cuadro.',
            copy='Copiar la línea', copied='Copiada', meLoad='Cargar', meClear='Quitar partida', close='Cerrar', mePaste='Pega aquí tu partida (empieza por {"stats":…)', meError='No parece una partida de PokéSurvivor: tiene que ser el JSON entero de la clave ps.cloud.',
            meLoaded='Partida de {name}: {n} Pokémon.', mine='Mis Pokémon', owned='Lo tienes', notOwned='No lo tienes', ownedS='TUYO', upgrades='Mejoras compradas', yourRank='Tu puesto con tu habilidad y tu naturaleza', you='tú',
            sort_you='Tu puesto', meBlock='Tu partida ({name})', meAbility='Tu habilidad', meNature='Tu naturaleza', loading='Calculando tu puesto…',
            meRank='Con tu habilidad y tu naturaleza quedaría en el puesto <b>{n}</b> de 966 (puesto general: {base}). Las mejoras y cartas se suponen al máximo; las MT que ya le enseñaste no se cuentan.'),
 'en': dict(title='Sentencia Tiers', tagline='PokéSurvivor tier list for Arceus’ Judgment', nav_tiers='Tiers', nav_judg='The Judgment', nav_method='Method', nav_repo='Source',
            intro='All 966 Pokémon ranked only by how long they last in Arceus’ Judgment (minute 30). Computed from the game’s code: slows, stuns, defenses against the 86 legendaries that show up, regeneration, capped speed and size. How well they clear before minute 30 is shown on each page; it does not score.',
            updated='Game patch', pokemon='Pokémon', legs='Legendaries', nonlegs='Non-legendaries', all='All', tier='Tier', sort='Sort by', group='Group by',
            mode_base='Default', mode_shop='Kecleon Shop', count='{n} of {m} Pokémon', none='No Pokémon matches the filters.', shuffle='Shuffle', filters='Filters', types='Types',
            sort_opts=[('pos', 'Rank'), ('name', 'Name'), ('dex', 'Dex number'), ('hordes', 'Horde ranking'), ('T', 'Toughness'), ('U', 'Control'), ('A', 'Regeneration'), ('D', 'Damage'), ('S', 'Speed'), ('Z', 'Size'), ('hp', 'HP'), ('spd', 'Base speed'), ('rnd', 'Random')],
            group_opts=[('tier', 'Tier'), ('type', 'Type'), ('leg', 'Legendaries'), ('none', 'No grouping')],
            flag_leg='Legendaries only', flag_slow='Has a slow', flag_stun='Has a stun', flag_regen='Has regeneration', slow='Slow', stun='Stun', regen='Regeneration', slowS='SLOW', stunS='STUN', regenS='REGEN',
            mode_help='Default: ability 1, neutral nature and natural moves only. Kecleon Shop: best ability (Capsule), best nature (Mint) and the TMs that help.',
            back='Tier list', rank_base='Rank · default', rank_shop='Rank · with Kecleon Shop', rank_hordes='Horde ranking (SurvivorTiers)', of='of', stats='In-game stats', guard='Damage taken (defense)',
            radius='Collision radius', px='px', speed_eff='Effective speed in the Judgment', score='Score', components='Why it is here', incoming='Damage taken by type (legendary pool)',
            abilities='Abilities', default_ab='Ability 1 · default', hidden_ab='Hidden', rec_ab='Recommended', ab_note='Each account rolls ability 1 or 2 at random (50%), and the hidden one 1 in 20. The Ability Capsule (1,500) swaps between 1 and 2; the Hidden Ability Capsule (5,000) sets the hidden one.',
            build='Build', tab_base='Default', tab_shop='With Kecleon Shop', moves='Moves', slot='SLOT', why='Why', start='Starting move', start2='Second starting move (Repertoire)', bans='Bans (Upgrades → Ban)',
            items='Held item', items_note='Only one per run: dropped by bosses and locked chests.', cards='Level-up cards: priority', evos='Move evolutions', evo_text='{move} evolves at max level if you have taken the {need} card at least once this run.',
            nature='Nature (Mint, 1,500)', ability='Ability (Capsule)', tms='TMs to buy', tm_note='The Kecleon Shop sells 8 TMs a day out of about 100; if none fits your partner, the last one is swapped for one it can learn.', total='Total', none_tm='No TM needed: its natural pool already has what matters.',
            nat_none='No Mint clearly improves its score: keep the nature it rolled.', ab_same='Its ability 1 is already the best of its abilities for the Judgment.', prev='Previous', next='Next', hordes_link='See its SurvivorTiers page',
            strategy='Strategy', verdict='Verdict', footer_data='Data and rules: PokéSurvivor source code (JPTER78) · Horde ranking: SurvivorTiers (@fildotai) · Portraits: PMD SpriteCollab (CC BY-NC 4.0) · Pokémon © Nintendo/Creatures/GAME FREAK.',
            footer_fan='Non-profit fan project, unaffiliated with the game’s authors or Nintendo.', generated='Generated on', not_available='—',
            flag_tm='TM useful today', tmToday='TMs on sale today at the Kecleon Shop ({d})', tmHint='Pokémon whose Kecleon Shop build asks for a TM on sale today', tmFor='{n} Pokémon use it in their build', moved='Ranks gained or lost with the latest game update', tmNone='None of today’s TMs appears in the recommended builds: none is worth buying for the Judgment today. There will be 8 new ones tomorrow.', tm8='the eighth may differ: if none fits your partner, the game swaps it (load your save to see it exactly)',
            changes='Changes', search='Name, no., move or ability',
            me='My save', meTitle='Load your save', meIntro='With your save the site marks the Pokémon you own, their upgrades and the ability and nature you rolled, and estimates your rank with them. Everything stays in this browser: nothing is sent anywhere.',
            meHow='1. Open pokesurvivor.com with your account. 2. Press F12 and open the “Console” tab. 3. Paste this line and press Enter: it copies your save to the clipboard. 4. Come back here and paste it in the box.',
            copy='Copy the line', copied='Copied', meLoad='Load', meClear='Remove save', close='Close', mePaste='Paste your save here (it starts with {"stats":…)', meError='That does not look like a PokéSurvivor save: it must be the whole JSON of the ps.cloud key.',
            meLoaded='Save of {name}: {n} Pokémon.', mine='My Pokémon', owned='Owned', notOwned='Not owned', ownedS='MINE', upgrades='Upgrades bought', yourRank='Your rank with your ability and nature', you='you',
            sort_you='Your rank', meBlock='Your save ({name})', meAbility='Your ability', meNature='Your nature', loading='Computing your rank…',
            meRank='With your ability and nature it would rank <b>{n}</b> of 966 (general rank: {base}). Upgrades and cards are assumed maxed; TMs you already taught are not counted.'),
}
ITEMS = {'es': dict(leftovers=('Restos', 'Recuperas un 1,5 % de tu vida por segundo. El daño de Arceus es porcentual y puro: la regeneración porcentual es lo único que lo contrarresta.'),
                    focussash=('Banda Focus', 'Un golpe mortal te deja con 1 de vida (cada 60 s). Salva de un pilar o de un toque de Arceus hasta el minuto 35, cuando Arceus rompe tu objeto.'),
                    assaultvest=('Chaleco Asalto', '−20 % de daño recibido. Ayuda a llegar al minuto 30; en la Sentencia sobra en cuanto Coraza alcanza el tope del 80 %.')),
         'en': dict(leftovers=('Leftovers', 'Recover 1.5% of your HP per second. Arceus’ damage is percentage-based and pure: percentage regeneration is the only thing that offsets it.'),
                    focussash=('Focus Sash', 'A lethal hit leaves you at 1 HP (every 60 s). Saves you from a pillar or an Arceus touch until minute 35, when Arceus breaks your item.'),
                    assaultvest=('Assault Vest', '−20% damage taken. Helps reach minute 30; in the Judgment it becomes redundant once Armor hits the 80% cap.'))}
CARDS = {'es': dict(cd='Reflejos', spd='Carrera', def_='Coraza', hp='Vigor', rgn='Síntesis', atk='Potencia', heal='Baya Zidra', mag='Imán', xp='Aprendizaje'),
         'en': dict(cd='Reflexes', spd='Sprint', def_='Armor', hp='Vigor', rgn='Synthesis', atk='Power', heal='Zidra Berry', mag='Magnet', xp='Learning')}
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
def typechip(t, lang): return f'<span class="type" style="--tc:{TC[t]}">{TYPE_NAME[lang][t]}</span>'

# ---------------- textos generados ----------------
def reason(m, p, var, lang):
    c = m['code']; mv = MOVES[m['id']]
    if lang == 'es':
        if c == 'slow': return f"Frena un {m['pct']} % a todo lo que toca y los jefes no lo resisten: los legendarios de la Sentencia se quedan al {m['left']} % de velocidad y dejan de alcanzarte. Con Reflejos la recarga baja tanto que el frenazo no se corta."
        if c == 'stun': return f"Zona con aviso que aturde. En los jefes solo dura el 35 % ({m['secs']} s por lanzamiento), pero con la recarga reducida se encadena: un legendario aturdido no ataca ni te hace daño al tocarte."
        if c == 'primary':
            k = {'homing': 'los proyectiles persiguen al objetivo y no fallan', 'beam': 'atraviesa a todo lo que pilla en línea', 'projectile': 'varios proyectiles al objetivo más cercano', 'charge': 'se carga un instante y suelta un rayo enorme',
                 'meteor': 'cae sobre los enemigos cercanos', 'bounce': 'rebota de enemigo en enemigo', 'chain': 'salta entre enemigos', 'boomerang': 'golpea a la ida y a la vuelta', 'nova': 'sale en todas direcciones', 'cone': 'abanico corto de disparos',
                 'quake': 'ondas en línea por el suelo', 'vortex': 'remolino que daña en su zona', 'shove': 'onda alrededor', 'melee': 'cuerpo a cuerpo: recibes un 25 % menos de daño con él activo, pero te obliga a estar pegado a los legendarios',
                 'dash': 'embestida: cruzas a los enemigos sin recibir daño', 'spin': 'giras golpeando alrededor', 'aura': 'daño continuo a tu alrededor', 'orbit': 'orbes que giran a tu alrededor', 'mine': 'minas que estallan al pisarlas', 'trail': 'charcos que dañan al pisarlos'}.get(m['kind'], '')
            side = 'físico' if m['cat'] == 'physical' else 'especial'
            return f"Tu ataque de daño para llegar al minuto 30 y rematar legendarios: es {side}, su lado bueno ({m['fit']}× del máximo), y {k}. En la Sentencia el daño cuenta poco (la vida de cada legendario se ajusta a tu propio daño), así que prima la fiabilidad."
        if c == 'aquaring': return "No hace daño: acumula regeneración (hasta 6 cargas con sus mejoras, unos 19 PS/s). Los pilares de Arceus quitan un 30 % de vida puro y esta es la mejor forma de recuperarlo entre salvas."
        if c == 'buff': return f"Acumula {'Ataque' if m['side'] == 'physical' else 'Ataque Especial'} (hasta 5 cargas) para los ataques de su lado. Contra Arceus da igual, pero acorta las oleadas de antes del minuto 30 y los primeros legendarios."
        if c == 'second': return "Segundo ataque para las hordas de antes del minuto 30 y para cuando el principal no tenga blanco."
        if c == 'agility': return "Acumula velocidad: sirve hasta el tope suave de 130; por encima solo cuenta un 25 %."
    else:
        if c == 'slow': return f"Slows everything it touches by {m['pct']}% and bosses do not resist it: the Judgment legendaries drop to {m['left']}% speed and stop catching you. With Reflexes the cooldown gets so short the slow never lapses."
        if c == 'stun': return f"Telegraphed zone that stuns. On bosses it only lasts 35% ({m['secs']} s per cast), but with the reduced cooldown it chains: a stunned legendary neither attacks nor hurts you on contact."
        if c == 'primary':
            k = {'homing': 'the projectiles track the target and never miss', 'beam': 'pierces everything in a line', 'projectile': 'several projectiles at the nearest target', 'charge': 'charges briefly and fires a huge beam',
                 'meteor': 'falls on nearby enemies', 'bounce': 'bounces from enemy to enemy', 'chain': 'jumps between enemies', 'boomerang': 'hits on the way out and back', 'nova': 'fires in every direction', 'cone': 'short fan of shots',
                 'quake': 'ground waves in a line', 'vortex': 'a whirlpool that damages its area', 'shove': 'a wave around you', 'melee': 'melee: you take 25% less damage while it is active, but it forces you to stand next to the legendaries',
                 'dash': 'a dash through enemies without taking damage', 'spin': 'you spin hitting all around', 'aura': 'continuous damage around you', 'orbit': 'orbs circling you', 'mine': 'mines that explode when stepped on', 'trail': 'puddles that hurt whoever steps in'}.get(m['kind'], '')
            side = 'physical' if m['cat'] == 'physical' else 'special'
            return f"Your damage move to reach minute 30 and finish legendaries: it is {side}, its strong side ({m['fit']}× of max), and {k}. Damage matters little in the Judgment (each legendary’s HP scales with your own damage), so reliability comes first."
        if c == 'aquaring': return "Deals no damage: stacks regeneration (up to 6 stacks with its upgrades, about 19 HP/s). Arceus’ pillars take 30% of your HP as pure damage and this is the best way to get it back between volleys."
        if c == 'buff': return f"Stacks {'Attack' if m['side'] == 'physical' else 'Special Attack'} (up to 5) for same-side moves. Irrelevant against Arceus, but it shortens the waves before minute 30 and the first legendaries."
        if c == 'second': return "Second attack for the hordes before minute 30 and for when the main one has no target."
        if c == 'agility': return "Stacks speed: useful up to the soft cap of 130; above it only 25% counts."
    return ''

def group_evos(b):
    out = {}
    for e in b['evos']: out.setdefault(e['need'], []).append(e['move'])
    return out

def cards_text(p, var, lang):
    b = var['build']; n = b['spd_cards']
    if lang == 'es':
        out = ["<b>Reflejos</b> (−8 % de recarga, hasta 10): con la recarga baja los frenazos y aturdimientos se encadenan sin huecos.",
               (f"<b>Carrera</b>: {'una carta' if n == 1 else f'unas {n} cartas'} para llegar al tope suave de 130 con Zancada al máximo." if n else "<b>Carrera</b>: con Zancada al máximo ya está en el tope suave de 130; una o dos no sobran para esquivar."),
               "<b>Coraza</b> (hasta 12): la reducción se acumula hasta el tope del 80 % y es lo que más vida te ahorra contra los legendarios.",
               "<b>Vigor</b> (+20 de vida): margen contra los golpes de los legendarios, que escalan un 15 % cada 5 s.",
               "<b>Síntesis</b> (+0,9 vida/s): recupera entre salvas de pilares (el daño de Arceus es porcentual, solo la regeneración lo compensa).",
               "<b>Baya Zidra</b> cuando estés por debajo de la mitad: recupera el 45 % al momento."]
        for need, mvs in group_evos(b).items(): out.append(f"<b>{NEED[lang][need]}</b> al menos una vez: es la condición para que {' y '.join(mname(m, lang) for m in mvs)} {'evolucione' if len(mvs) == 1 else 'evolucionen'} al llegar al nivel máximo.")
        out.append("<b>Potencia</b> (hasta 40) después: el daño apenas cuenta en la Sentencia. Imán y Aprendizaje, solo si no hay nada mejor.")
    else:
        out = ["<b>Reflexes</b> (−8% cooldown, up to 10): with low cooldowns the slows and stuns chain without gaps.",
               (f"<b>Sprint</b>: {'one card' if n == 1 else f'about {n} cards'} to reach the soft cap of 130 with Stride maxed." if n else "<b>Sprint</b>: with Stride maxed it already sits at the soft cap of 130; one or two more still help you dodge."),
               "<b>Armor</b> (up to 12): the reduction stacks up to the 80% cap and saves the most HP against the legendaries.",
               "<b>Vigor</b> (+20 HP): margin against the legendaries’ hits, which scale 15% every 5 s.",
               "<b>Synthesis</b> (+0.9 HP/s): recover between pillar volleys (Arceus’ damage is percentage-based, only regeneration offsets it).",
               "<b>Zidra Berry</b> when below half: heals 45% instantly."]
        for need, mvs in group_evos(b).items(): out.append(f"<b>{NEED[lang][need]}</b> at least once: it is the condition for {' and '.join(mname(m, lang) for m in mvs)} to evolve at max level.")
        out.append("<b>Power</b> (up to 40) afterwards: damage barely matters in the Judgment. Magnet and Learning only if nothing else is left.")
    return out

def strategy(p, lang):
    b = p['base']; s = p['shop']; c = b['comp']; inc = p['incoming']
    worst = [(t, v) for t, v in inc.items() if v > 1.0][:3]
    best = [(t, v) for t, v in inc.items() if v < 0.7][-3:]
    ht = p['hordes']['tier']; T = b['T_mult']
    N = name(p, lang)
    tn = lambda t: TYPE_NAME[lang][t]
    paras = []
    if lang == 'es':
        # decimales con coma en los textos españoles
        _fmt = f'{T:.2f}'.replace('.', ',')
        worst = [(t, float(f'{v:.2f}')) for t, v in worst]; best = [(t, float(f'{v:.2f}')) for t, v in best]
        es_num = lambda v: f'{v:.2f}'.replace('.', ',')
        via = {'S': 'llega al minuto 30 con holgura', 'A': 'llega al minuto 30 sin problema con una build normal', 'B': 'llega al minuto 30 si la partida va limpia', 'C': 'le cuesta llegar al minuto 30: hace falta un buen objeto y evitar riesgos', 'D': 'llegar al minuto 30 ya es un reto; la Sentencia es casi un extra'}[ht]
        tough = ('aguanta muy bien los golpes de los legendarios' if T < 0.75 else 'aguanta los golpes de los legendarios como la media' if T < 0.95 else 'es frágil ante los legendarios') + f" (recibe ×{_fmt} del daño de referencia)"
        w = f" Lo que más le castiga: {', '.join(f'{tn(t)} (×{es_num(v)})' for t, v in worst)}." if worst else ' No tiene ningún tipo que le castigue de verdad.'
        r = f" Lo que mejor aguanta: {', '.join(f'{tn(t)} (×{es_num(v)})' for t, v in reversed(best))}." if best else ''
        paras.append(f"{N} es tier {b['tier']} de la Sentencia (puesto {b['pos']} de 966) y tier {ht} en las hordas: {via}. Frente al pool de legendarios {tough}.{w}{r}")
        tools = []
        sp_pct = slow_pct(b)
        if b['slow']: tools.append(f"{mname(b['slow'], lang)} frena un {sp_pct} % a los legendarios" + (' (van al 80 % de tu velocidad: con eso ya no te alcanzan)' if sp_pct < 50 else ' (se quedan casi parados)'))
        if b['stun']: tools.append(f"{mname(b['stun'], lang)} los aturde por zonas")
        if b['heal'] >= 0.6: tools.append("Acua Aro le da regeneración contra los pilares")
        if tools:
            fin = ("con eso los legendarios dejan de ser una amenaza y solo queda esquivar a Arceus." if (b['stun'] or sp_pct >= 60) else "con eso puedes mantener a los legendarios a raya mientras esquivas a Arceus.")
            paras.append("Sus herramientas naturales para la Sentencia: " + '; '.join(tools) + ". Los jefes ignoran el empuje y resisten los remolinos, pero los frenazos entran al 100 % y los aturdimientos se encadenan con Reflejos: " + fin + (" Si consigues un vínculo en una grieta, fusiona el frenazo y el aturdimiento en un mismo hueco para tenerlos activos a la vez." if (b['slow'] and b['stun']) else ''))
        else: paras.append("No tiene ni frenazo ni aturdimiento naturales a distancia: contra los legendarios solo puede correr y aguantar, así que la Sentencia depende de esquivar y de la regeneración. Con la Tienda Kecleon cambia la cosa (ver la pestaña).")
        sp = b['build']['spd_cards']
        size = 'pequeño, así que los pilares (44 px de radio) y los rayos tienen menos margen para pillarle' if p['r'] <= 11 else 'de tamaño medio' if p['r'] < 17 else 'grande: cuenta como el radio máximo (18 px) y le cuesta un poco más salir de los pilares'
        paras.append(f"Velocidad: {'con Zancada al máximo ya roza el tope suave de 130' if sp == 0 else ('necesita una carta de Carrera' if sp == 1 else f'necesita unas {sp} cartas de Carrera') + ' para llegar al tope suave de 130'}; Arceus corre siempre a 1,22 veces la tuya, así que la velocidad sirve para esquivar y para que los legendarios (al 80 % de tu velocidad) no te alcancen, no para huir de Arceus. Es {size}.")
        paras.append(f"Plan: mantente a 250–400 px de Arceus (su onda solo sale si estás a menos de 210), muévete en círculos amplios por el borde de la arena y gana distancia en sus pausas de ataque (1,1–1,5 s cada vez que lanza). Cuando los legendarios se agrupen, {'lánzales ' + mname(b['stun'], lang) + ' y ' if b['stun'] else ''}{'mantén ' + mname(b['slow'], lang) + ' activo sobre el grupo' if b['slow'] else 'sigue corriendo: no intentes matarlos a partir del tercero'}. Desde el minuto 35 Arceus rompe tu objeto y acelera; desde el 37 su toque quita cada vez más. El récord realista está entre los 5 y los 8 minutos de Sentencia.")
        changes = ', '.join(filter(None, [f"{mname(t['id'], lang)} por MT" for t in s['tms']] + ([f"naturaleza {nname(s['nature'], lang)}"] if s['nature'] else []) + ([f"habilidad {aname(s['ability'], lang)}"] if s['ability'] != b['ability'] else [])))
        if changes:
            paras.append((f"Con la Tienda Kecleon sube al puesto {s['pos']}: " if s['pos'] < b['pos'] else f"Con la Tienda Kecleon queda en el puesto {s['pos']} (mejora, pero otros mejoran más): ") + changes + '.')
    else:
        via = {'S': 'reaches minute 30 comfortably', 'A': 'reaches minute 30 without trouble with a normal build', 'B': 'reaches minute 30 if the run goes cleanly', 'C': 'struggles to reach minute 30: it needs a good item and no risks', 'D': 'reaching minute 30 is already a challenge; the Judgment is almost a bonus'}[ht]
        tough = ('shrugs off the legendaries’ hits' if T < 0.75 else 'takes the legendaries’ hits about as well as average' if T < 0.95 else 'is frail against the legendaries') + f" (it takes ×{T:.2f} of the reference damage)"
        w = f" What punishes it most: {', '.join(f'{tn(t)} (×{v:.2f})' for t, v in worst)}." if worst else ' No type really punishes it.'
        r = f" What it resists best: {', '.join(f'{tn(t)} (×{v:.2f})' for t, v in reversed(best))}." if best else ''
        paras.append(f"{N} is Judgment tier {b['tier']} (rank {b['pos']} of 966) and horde tier {ht}: it {via}. Against the legendary pool it {tough}.{w}{r}")
        tools = []
        sp_pct = slow_pct(b)
        if b['slow']: tools.append(f"{mname(b['slow'], lang)} slows the legendaries by {sp_pct}%" + (' (they run at 80% of your speed: that is enough to keep them off you)' if sp_pct < 50 else ' (they are left almost standing)'))
        if b['stun']: tools.append(f"{mname(b['stun'], lang)} stuns them in zones")
        if b['heal'] >= 0.6: tools.append("Aqua Ring gives it regeneration against the pillars")
        if tools:
            fin = ("with those the legendaries stop being a threat and all that is left is dodging Arceus." if (b['stun'] or sp_pct >= 60) else "with that you can keep the legendaries at bay while you dodge Arceus.")
            paras.append("Its natural Judgment tools: " + '; '.join(tools) + ". Bosses ignore knockback and resist whirlpools, but slows land at 100% and stuns chain with Reflexes: " + fin + (" If you earn a bond in a rift, fuse the slow and the stun into one slot so both stay active at once." if (b['slow'] and b['stun']) else ''))
        else: paras.append("It has neither a natural ranged slow nor a stun: against the legendaries it can only run and endure, so the Judgment comes down to dodging and regeneration. The Kecleon Shop changes that (see the tab).")
        sp = b['build']['spd_cards']
        size = 'small, so pillars (44 px radius) and beams have less margin to catch it' if p['r'] <= 11 else 'medium-sized' if p['r'] < 17 else 'big: it counts as the maximum radius (18 px) and takes slightly longer to leave a pillar'
        paras.append(f"Speed: {'with Stride maxed it already touches the soft cap of 130' if sp == 0 else ('it needs one Sprint card' if sp == 1 else f'it needs about {sp} Sprint cards') + ' to reach the soft cap of 130'}; Arceus always runs at 1.22× your speed, so speed is for dodging and for keeping the legendaries (at 80% of your speed) off you, not for outrunning Arceus. It is {size}.")
        paras.append(f"Plan: stay 250–400 px from Arceus (its shockwave only fires if you are closer than 210), run wide circles along the arena edge and gain distance during its casting pauses (1.1–1.5 s every cast). When the legendaries bunch up, {'drop ' + mname(b['stun'], lang) + ' on them and ' if b['stun'] else ''}{'keep ' + mname(b['slow'], lang) + ' active on the group' if b['slow'] else 'keep running: do not try to kill them after the third'}. From minute 35 Arceus breaks your item and speeds up; from minute 37 its touch hurts more and more. A realistic record sits between 5 and 8 minutes of Judgment.")
        changes = ', '.join(filter(None, [f"{mname(t['id'], lang)} via TM" for t in s['tms']] + ([f"{nname(s['nature'], lang)} nature"] if s['nature'] else []) + ([f"{aname(s['ability'], lang)} ability"] if s['ability'] != b['ability'] else [])))
        if changes:
            paras.append((f"With the Kecleon Shop it climbs to rank {s['pos']}: " if s['pos'] < b['pos'] else f"With the Kecleon Shop it lands at rank {s['pos']} (it improves, but others improve more): ") + changes + '.')
    return paras

def slow_pct(b):
    if not b['slow']: return 0
    return round(min(0.8, MOVES[b['slow']]['slow'] * (2 if b['ability'] == 'serene-grace' else 1)) * 100)

def verdict(p, lang):
    b = p['base']; ht = p['hordes']['tier']
    tools = (b['slow'] is not None) + (b['stun'] is not None) + (b['heal'] > 0)
    if lang == 'es':
        h = {'S': ' Además es de los mejores limpiando hordas: llega al minuto 30 sobrado.', 'A': ' Limpia hordas muy bien: llega al minuto 30 sin problema.', 'B': ' Limpiando hordas es del montón: llega al minuto 30 con una partida normal.',
             'C': ' Limpiando hordas flojea: llegar al minuto 30 cuesta.', 'D': ' Limpiando hordas es de los peores: llegar al minuto 30 es lo difícil.'}[ht]
        if b['tier'] == 'S': return 'De los que más aguantan en la Sentencia: control y resistencia frente a los legendarios.' + h
        if b['tier'] == 'A': return 'Aguanta muy bien la Sentencia' + (': tiene las herramientas de control que importan.' if tools >= 2 else ', aunque le falta alguna herramienta de control.') + h
        if b['tier'] == 'B': return 'Aguanta la Sentencia un rato, pero hay quien lo hace mejor con menos esfuerzo.' + h
        if b['tier'] == 'C': return 'Justo en la Sentencia: le falta control o aguante.' + h
        return 'No aguanta la Sentencia: le faltan herramientas y resistencia. Juégalo por gusto, no por el ranking.' + h
    h = {'S': ' It is also among the best at clearing hordes: reaches minute 30 with ease.', 'A': ' Clears hordes very well: reaches minute 30 without trouble.', 'B': ' Average at clearing hordes: reaches minute 30 with a normal run.',
         'C': ' Weak at clearing hordes: reaching minute 30 is hard.', 'D': ' Among the worst at clearing hordes: reaching minute 30 is the real challenge.'}[ht]
    if b['tier'] == 'S': return 'Among the longest-lasting in the Judgment: control and resistance against the legendaries.' + h
    if b['tier'] == 'A': return 'Lasts very well in the Judgment' + (': it has the control tools that matter.' if tools >= 2 else ', though it lacks a control tool.') + h
    if b['tier'] == 'B': return 'Lasts a while in the Judgment, but others do it better with less effort.' + h
    if b['tier'] == 'C': return 'Marginal in the Judgment: it lacks control or toughness.' + h
    return 'Does not last in the Judgment: it lacks the tools and the resistance. Play it for fun, not for the ranking.' + h

# ---------------- plantillas ----------------
def layout(lang, title, body, active, depth, desc='', extra_head='', path=''):
    U = UI[lang]; root = '../' * depth
    other = 'en' if lang == 'es' else 'es'
    url = f'{SITE}/{path}'
    extra_head += (f'<meta property="og:type" content="website"><meta property="og:site_name" content="Sentencia Tiers"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc or U["tagline"])}">'
                   f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="{"es_ES" if lang == "es" else "en_US"}">'
                   f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc or U["tagline"])}"><meta name="twitter:image" content="{SITE}/og.png">'
                   f'<link rel="canonical" href="{url}"><link rel="alternate" hreflang="{lang}" href="{url}"><link rel="alternate" hreflang="{other}" href="{SITE}/{path.replace(lang + "/", other + "/", 1)}">')
    nav = ''.join(f'<a href="{root}{lang}/{h}" class="{"on" if k == active else ""}">{U[k]}</a>' for k, h in (('nav_tiers', ''), ('nav_judg', 'sentencia/'), ('nav_method', 'metodo/'), ('changes', 'cambios/')))
    nav += f'<a href="{REPO}" rel="noopener">{U["nav_repo"]}</a>'
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
<footer class="wrap"><div>{U['footer_data']}</div><div>{U['footer_fan']} · {U['generated']} {R['generated']} · {U['updated']}: {R['game_commit']} · <a href="{REPO}" rel="noopener">GitHub</a></div></footer>
</body></html>'''

def index_page(lang):
    U = UI[lang]
    data = dict(t=dict(types=TYPE_NAME[lang], slow=U['slow'], stun=U['stun'], regen=U['regen'], slowS=U['slowS'], stunS=U['stunS'], regenS=U['regenS'], count=U['count'], none=U['none'], tier=U['tier'], legs=U['legs'], nonlegs=U['nonlegs'], all=U['all']),
                types=TYPES, typeColors=TC, list=[])
    for p in P:
        row = dict(dex=p['dex'], slug=slug(p), name=name(p, lang), alt=p['nameEn'] if lang == 'es' else p['name'], types=p['types'], leg=p['leg'], hp=p['stats']['hp'], spd=p['stats']['spd'], hordes=p['hordes']['rank'],
                   sc=p['base']['score'], abs={int(k): v for k, v in p['abil_scores'].items()}, ab=p['abils'])
        for k in ('base', 'shop'):
            v = p[k]; row[k] = dict(pos=v['pos'], tier=v['tier'], c=v['comp'], slow=v['slow'], stun=v['stun'], regen=bool(v['heal']) or v['ability'] in ('regenerator', 'natural-cure', 'healer', 'shed-skin'))
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
<label>{U['sort']}<span style="display:flex;gap:4px"><select id="sort">{''.join(f'<option value="{k}">{v}</option>' for k, v in U['sort_opts'])}<option value="you">{U['sort_you']}</option></select><button type="button" class="chip" id="dir" title="asc/desc">↓</button><button type="button" class="chip" id="shuffle">{U['shuffle']}</button></span></label>
<label>{U['group']}<select id="group">{''.join(f'<option value="{k}">{v}</option>' for k, v in U['group_opts'])}</select></label><span class="count" id="count"></span></div>
<div class="row"><label>{U['tier']}<span class="chips" id="tiers">{''.join(f'<button type="button" class="chip" data-tier="{t}">{t}</button>' for t in 'SABCD')}</span></label>
<label>{U['filters']}<span class="chips" id="flags"><button type="button" class="chip" data-f="leg">{U['flag_leg']}</button><button type="button" class="chip" data-f="slow">{U['flag_slow']}</button><button type="button" class="chip" data-f="stun">{U['flag_stun']}</button><button type="button" class="chip" data-f="regen">{U['flag_regen']}</button><button type="button" class="chip" data-f="tmday" title="{esc(U['tmHint'])}">{U['flag_tm']}</button><button type="button" class="chip" data-f="mine" id="flag-mine" hidden>{U['mine']}</button><button type="button" class="chip me" id="me-btn">{U['me']}</button></span></label>
<label>{U['types']}<span class="chips" id="types"></span></label></div>
<p class="small muted" style="margin:0">{U['mode_help']}</p>
<div class="tmday" id="tmday"></div>
</section>
<dialog id="me-dlg" class="panel"><h3>{U['meTitle']}</h3><p class="small">{U['meIntro']}</p><p class="small">{U['meHow']}</p>
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
        out.append(f'<div class="bar" title="{esc(hint)}"><span class="l">{label} <small>{round(R["weights"][k] * 100)} %</small></span><span class="track"><span class="fill base" style="width:{b * 100:.0f}%"></span><span class="fill shop" style="width:{s * 100:.0f}%"></span></span><span class="v">{b:.2f} <em>{s:.2f}</em></span></div>')
    out.append(f'</div><div class="legend"><span><i style="background:var(--yellow)"></i>{U["mode_base"]}</span><span><i style="background:var(--red)"></i>{U["mode_shop"]}</span><span class="muted">{"% = peso en la puntuación · pasa el ratón para ver qué mide" if lang == "es" else "% = weight in the score · hover to see what it measures"}</span></div>')
    return ''.join(out)

def build_panel(p, var, key, lang):
    U = UI[lang]; b = var['build']; tn = TYPE_NAME[lang]
    cards = []
    for i, m in enumerate(b['moves']):
        mv = MOVES[m['id']]; isTM = any(t['id'] == m['id'] for t in var.get('tms', []))
        tag = f'<span class="pill y">{KIND[lang][mv["kind"]]}</span>' + (f'<span class="pill">{CAT[lang][mv["cat"]]}</span>' if mv['cat'] else '') + ('<span class="pill r">MT</span>' if isTM else '')
        cards.append(f'<article class="move" style="--tc:{TC[mv["type"]]}"><span class="slot">{U["slot"]} {i + 1}</span><div class="n">{esc(mname(m["id"], lang))} {typechip(mv["type"], lang)} {tag}</div><div class="d">{esc(mdesc(m["id"], lang))}</div><div class="why"><b>{U["why"]}</b>{reason(m, p, var, lang)}</div></article>')
    kv = [(U['start'], esc(mname(b['start'], lang)) if b['start'] else U['not_available']),
          (U['start2'], esc(mname(b['start2'], lang)) if b['start2'] else U['not_available']),
          (U['bans'], ', '.join(esc(mname(x, lang)) for x in b['bans']) or U['not_available'])]
    items = ''.join(f'<div class="item {"rec" if i == 0 else ""}"><span class="n">{ITEMS[lang][it][0]}{" <span class=pill>" + U["rec_ab"] + "</span>" if i == 0 else ""}</span><span class="small muted">{ITEMS[lang][it][1]}</span></div>' for i, it in enumerate(b['items']))
    shop_html = ''
    if key == 'shop':
        nat = f"<b>{nname(var['nature'], lang)}</b> (+{STAT[lang][NAT_BY[var['nature']]['up']]} −{STAT[lang][NAT_BY[var['nature']]['down']]}): " + (
            ('sube la defensa que más le castigan los legendarios y baja el ataque que no usa.' if NAT_BY[var['nature']]['up'] in ('df', 'sd') else 'sube la velocidad hasta el tope suave de 130 y baja el ataque que no usa.') if lang == 'es' else
            ('raises the defense the legendaries punish most and lowers the attack it does not use.' if NAT_BY[var['nature']]['up'] in ('df', 'sd') else 'raises speed up to the soft cap of 130 and lowers the attack it does not use.')) if var['nature'] else U['nat_none']
        if var['capsule']:
            ab = f"<b>{aname(var['ability'], lang)}</b> ({'Cápsula Habilidad Oculta, 5.000' if var['capsule'] == 'caph' else 'Cápsula Habilidad, 1.500'}{'' if lang == 'es' else ''}): {esc(adesc(var['ability'], p['types'], lang))}"
            if lang == 'en': ab = ab.replace('Cápsula Habilidad Oculta, 5.000', 'Hidden Ability Capsule, 5,000').replace('Cápsula Habilidad, 1.500', 'Ability Capsule, 1,500')
        else: ab = U['ab_same']
        if var['tms']:
            tot = sum(t['price'] for t in var['tms'])
            tms = '<ul class="plain">' + ''.join(f'<li>{esc(mname(t["id"], lang))} · <span class="price">{fmt(t["price"], lang)}</span></li>' for t in var['tms']) + f'</ul><div class="small">{U["total"]}: <span class="price">{fmt(tot, lang)}</span> · {U["tm_note"]}</div>'
        else: tms = U['none_tm']
        shop_html = f'<div class="g3 shop"><div class="panel"><h3>{U["nature"]}</h3><p class="small">{nat}</p></div><div class="panel"><h3>{U["ability"]}</h3><p class="small">{ab}</p></div><div class="panel"><h3>{U["tms"]}</h3>{tms}</div></div>'
    evos = ''.join(f'<li>{U["evo_text"].format(move=esc(mname(e["move"], lang)), need=NEED[lang][e["need"]])}</li>' for e in b['evos'])
    return f'''<div class="tab-panel" data-tab="{key}">
<div class="moves">{''.join(cards)}</div>
{shop_html}
<div class="g3">
<div class="panel"><dl class="kv">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in kv)}</dl>{f'<h3 style="margin-top:10px">{U["evos"]}</h3><ul class="plain small">{evos}</ul>' if evos else ''}</div>
<div class="panel"><h3>{U['items']}</h3><div class="items">{items}</div><p class="small muted" style="margin:6px 0 0">{U['items_note']}</p></div>
<div class="panel"><h3>{U['cards']}</h3><ol class="cards">{''.join(f'<li>{x}</li>' for x in cards_text(p, var, lang))}</ol></div>
</div>
</div>'''

def pokemon_page(p, lang, prev, nxt):
    U = UI[lang]; N = name(p, lang); b = p['base']; s = p['shop']; st = p['stats']; tn = TYPE_NAME[lang]
    abil_html = []
    for i, aid in enumerate(p['abils']):
        if not aid or (i == 1 and aid == p['abils'][0]): continue
        tags = (f'<span class="pill y">{U["default_ab"]}</span>' if i == 0 else '') + (f'<span class="pill c">{U["hidden_ab"]}</span>' if i == 2 else '') + (f'<span class="pill r">{U["rec_ab"]}</span>' if aid == s['ability'] and s['ability'] != b['ability'] else '')
        abil_html.append(f'<div class="a {"rec" if aid == s["ability"] else ""}"><span class="n">{esc(aname(aid, lang))} {tags}</span><span class="small muted">{esc(adesc(aid, p["types"], lang))}</span></div>')
    inc = ''.join(f'<div class="r"><span class="type" style="--tc:{TC[t]}">{tn[t]}</span><span class="track"><span class="fill" style="--tc:{TC[t]};width:{min(100, v / 2.4 * 100):.0f}%"></span></span><span class="v {"bad" if v > 1.05 else "good" if v < 0.75 else ""}">×{v:.2f}</span></div>' for t, v in p['incoming'].items())
    hordes = p['hordes']
    stats = [(STAT[lang]['hp'], f"{st['hp']}"), (STAT[lang]['spd'], f"{st['spd']} <span class=muted>→ {b['S']}</span>"), (STAT[lang]['pa'], f"×{st['pa']:.2f}"), (STAT[lang]['sa'], f"×{st['sa']:.2f}"),
             (STAT[lang]['df'], f"{st['df']} <span class=muted>(×{p['guard']['p']:.2f})</span>"), (STAT[lang]['sd'], f"{st['sd']} <span class=muted>(×{p['guard']['s']:.2f})</span>"), (U['radius'], f"{p['r']} {U['px']}")]
    body = f'''<nav class="crumbs"><a href="../../">{U['back']}</a><span>/</span><span>Nº {p['dex']:03d}</span></nav>
<section class="head"><div class="pic cut"><img class="px" src="../../../img/p/{p['dex']}.png" alt="{esc(N)}" width="120" height="120"></div>
<div class="hd"><div class="sub"><h1>{esc(N)}</h1><span>Nº {p['dex']:03d}</span>{''.join(typechip(t, lang) for t in p['types'])}{'<span class="pill c">' + ('Legendario' if lang == 'es' else 'Legendary') + '</span>' if p['leg'] else ''}<span class="tier {b['tier']}">TIER {b['tier']}</span></div>
<div class="ranks"><div class="rank"><span class="l">{U['rank_base']}</span><span class="v">{b['pos']} <span class="small muted">/ 966</span></span></div>
<div class="rank shop"><span class="l">{U['rank_shop']}</span><span class="v">{s['pos']} <span class="small muted">/ 966 · {U['tier']} {s['tier']}</span></span></div>
<div class="rank ext"><span class="l">{U['rank_hordes']}</span><span class="v">{hordes['rank'] or '—'} <span class="small muted">/ 966 · {U['tier']} {hordes['tier']}</span></span></div></div>
<div class="verdict"><b class="up" style="color:var(--yellow)">{U['verdict']}:</b> {verdict(p, lang)}</div>
<section id="me" class="panel me" hidden data-dex="{p['dex']}" data-pos="{b['pos']}" data-sc="{b['score']}" data-scores="../../../assets/scores.json" data-abils="{esc(json.dumps(p['abils']))}" data-names="{esc(json.dumps([aname(a, lang) if a else '' for a in p['abils']], ensure_ascii=False))}" data-abs="{esc(json.dumps({int(k): v for k, v in p['abil_scores'].items()}))}" data-natures="{esc(json.dumps([dict(id=n['id'], n=nname(n['id'], lang)) for n in NAT_BY.values()], ensure_ascii=False))}" data-t="{esc(json.dumps(dict(title=U['meBlock'], owned=U['owned'], notOwned=U['notOwned'], upgrades=U['upgrades'], ability=U['meAbility'], hidden=U['hidden_ab'].lower(), nature=U['meNature'], loading=U['loading'], rank=U['meRank']), ensure_ascii=False))}"></section></div></section>
<h2>{U['strategy']}</h2><div class="strat">{''.join(f'<p>{x}</p>' for x in strategy(p, lang))}</div>
<div class="g2">
<div class="panel"><h3>{U['components']}</h3>{bars(p, lang)}</div>
<div class="panel"><h3>{U['stats']}</h3><dl class="kv2">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in stats)}</dl>
<p class="small muted" style="margin:6px 0 0">{'Velocidad: base → efectiva en la Sentencia (tope suave 130). Defensas suavizadas: ×0,78 con mucha, ×1,25 con poca.' if lang == 'es' else 'Speed: base → effective in the Judgment (soft cap 130). Softened defenses: ×0.78 with a lot, ×1.25 with little.'}</p></div>
<div class="panel"><h3>{U['incoming']}</h3><div class="inc">{inc}</div></div>
<div class="panel"><h3>{U['abilities']}</h3><div class="abil">{''.join(abil_html)}</div><p class="small muted" style="margin:6px 0 0">{U['ab_note']}</p></div></div>
<div class="tabs"><h2 style="margin:0;align-self:end;padding-right:14px">{U['build']}</h2><button data-tab="base">{U['tab_base']}</button><button data-tab="shop" class="red">{U['tab_shop']}</button></div>
{build_panel(p, b, 'base', lang)}{build_panel(p, s, 'shop', lang)}
<nav class="pager">{f'<a href="../{slug(prev)}/">← #{prev["base"]["pos"]} {esc(name(prev, lang))}</a>' if prev else '<span></span>'}<a href="../../">{U['back']}</a>{f'<a href="../{slug(nxt)}/">#{nxt["base"]["pos"]} {esc(name(nxt, lang))} →</a>' if nxt else '<span></span>'}</nav>
<script src="../../../assets/save.js"></script><script src="../../../assets/page.js"></script>'''
    title = f"{N} · {U['title']}: tier {b['tier']}, {'puesto' if lang == 'es' else 'rank'} {b['pos']}"
    desc = (f"{N} en la Sentencia de Arceus: tier {b['tier']} (puesto {b['pos']} de 966), build, habilidades, objetos y estrategia." if lang == 'es' else f"{N} in Arceus’ Judgment: tier {b['tier']} (rank {b['pos']} of 966), build, abilities, items and strategy.")
    return layout(lang, title, body, None, 3, desc, path=f'{lang}/pokemon/{slug(p)}/')

def prose_page(lang, key, title, html_body, path):
    return layout(lang, f"{title} · {UI[lang]['title']}", f'<article class="prose">{html_body}</article>', key, 2, path=path)

def judgment_text(lang):
    if lang == 'es':
        return '''<h1>Cómo funciona la Sentencia de Arceus</h1><p class="muted">Todo lo de aquí sale del código del juego (systems/judgment.js y compañía), no de la experiencia de nadie.</p>
<h2>Qué pasa en el minuto 30</h2><p>Se acaba la partida normal. Arceus te lleva a las Ruinas del Juicio, una arena redonda de 768 px de radio (24 casillas) de la que nadie sale. Arceus es invencible, lleva una Tabla al azar que le da su tipo, y cada 5 segundos acude un legendario. El ranking tiene dos mitades: el tiempo que aguantas y el daño que le haces a Arceus.</p>
<h2>Arceus</h2><ul>
<li><b>No se le puede dejar atrás.</b> Su velocidad es relativa a la tuya: empieza al 74 % y a los 37 s ya va a 1,22 veces tu velocidad. A los 5 min de Sentencia acelera sin tope.</li>
<li><b>Tope suave de velocidad:</b> lo que pase de 130 cuenta solo un 25 %. Corriendo al máximo te quedas en ~170 en vez de ~290.</li>
<li><b>Sus pausas son tu distancia.</b> Cada ataque lo deja parado entre 1,05 y 1,45 s, y entre ataques solo anda 1,4 s. Si te mueves siempre alejándote, ganas unos 100 px por ciclo hasta el minuto 35.</li>
<li><b>Su daño es porcentaje de vida y puro:</b> ignora tipos, defensa, Coraza y habilidades. Pilares 30 %, rayos en cruz 35 %, onda 40 %, toque 40 % (sube al 100 % entre los minutos 37 y 40). Solo lo contrarrestan la regeneración, esquivar y la Banda Focus.</li>
<li><b>Pilares (la Sentencia):</b> de 4 a 10, radio 44 px, aviso de 1,25 s; el primero cae exactamente donde estás. Tras el primer impacto tienes 0,45 s de invulnerabilidad que absorbe el resto de la salva.</li>
<li><b>Rayos en cruz:</b> 4, y 8 a partir de los 30 s, de 34 px de ancho y 1,1 s de aviso, barriendo toda la arena. A 300 px de Arceus el hueco entre rayos es de unos 200 px; pegado a él no hay hueco.</li>
<li><b>Onda:</b> solo si estás a menos de 210 px, radio 170, aviso de 0,85 s. No te acerques a esa distancia.</li>
<li><b>Minuto 35:</b> Arceus rompe el objeto de todos (Banda Focus incluida).</li></ul>
<h2>Los legendarios</h2><ul>
<li>Uno cada 5 s, al azar entre los 86 del juego. Cada uno tiene un 25 % más de vida y un 15 % más de daño que el anterior.</li>
<li><b>La vida del primero son 3 s de tu propio daño a un solo objetivo</b> (lo que hayas hecho antes del minuto 30). Por eso tu DPS casi no cambia nada: a partir del tercero se acumulan sí o sí.</li>
<li>Corren como mínimo al 80 % de tu velocidad. Los de tipo Psíquico, Eléctrico, Fantasma, Hada, Fuego, Agua, Hielo o Dragón disparan desde 300 px; el resto embiste.</li>
<li>Su daño sí pasa por tus tipos, tu defensa (física o especial según su lado fuerte), Coraza (tope 80 %) y tu habilidad. Contacto: 126 × 1,15ⁿ en el minuto 30.</li>
<li>Dan experiencia (nada más): cada uno sube cartas, y la Baya Zidra cura el 45 %.</li></ul>
<div class="callout"><b>Lo único que les funciona:</b> los <b>frenazos</b> entran al 100 % (Rayo Hielo los deja al 30 % de velocidad y con la recarga reducida es permanente; con Dicha, al 20 %) y los <b>aturdimientos</b> duran el 35 %, pero con Reflejos se encadenan, y un legendario aturdido ni ataca ni te daña al tocarte. El empuje no les afecta, los remolinos solo al 25 %, y veneno y quemadura hacen 1,5 fijo.</div>
<h2>Daño a Arceus</h2><p>Solo cuenta un 5 % de lo que le haces, que baja al 1 % a los 10 minutos, y tus ataques solo le apuntan cuando no queda ningún legendario vivo. Es el segundo ranking; para aguantar más tiempo no cambia nada.</p>
<h2>Qué hacer</h2><ol><li>Mantente a 250–400 px de Arceus y corre en círculos amplios por el borde. Gana distancia en sus pausas.</li><li>Cuando se agrupen los legendarios, aturde y frena al grupo; no intentes matarlos a partir del tercero.</li><li>Lleva Restos (o Banda Focus), sube Reflejos, Coraza y Síntesis, y Carrera solo hasta el tope de 130.</li><li>Antes de la partida: Veto a Placaje, Ataque Rápido y Golpe Cuerpo, y Movimiento inicial + Repertorio para empezar con tu frenazo y tu aturdimiento.</li></ol>'''
    return '''<h1>How Arceus’ Judgment works</h1><p class="muted">Everything here comes from the game’s code (systems/judgment.js and friends), not from anyone’s impressions.</p>
<h2>What happens at minute 30</h2><p>The normal run ends. Arceus takes you to the Ruins of Judgment, a round arena 768 px in radius (24 tiles) nobody can leave. Arceus is invincible, carries a random Plate that sets its type, and every 5 seconds a legendary shows up. The ranking has two halves: how long you last and how much damage you deal to Arceus.</p>
<h2>Arceus</h2><ul>
<li><b>You cannot outrun it.</b> Its speed is relative to yours: it starts at 74% and after 37 s it runs at 1.22× your speed. After 5 minutes of Judgment it accelerates without limit.</li>
<li><b>Soft speed cap:</b> anything above 130 counts only 25%. Fully stacked you end up around 170 instead of 290.</li>
<li><b>Its pauses are your distance.</b> Every cast freezes it for 1.05–1.45 s, and between casts it only walks 1.4 s. If you always move away you gain about 100 px per cycle until minute 35.</li>
<li><b>Its damage is a percentage of HP and pure:</b> it ignores types, defense, Armor and abilities. Pillars 30%, cross beams 35%, shockwave 40%, touch 40% (rising to 100% between minutes 37 and 40). Only regeneration, dodging and the Focus Sash offset it.</li>
<li><b>Pillars (the Judgment):</b> 4 to 10, radius 44 px, 1.25 s warning; the first one lands exactly where you stand. After the first hit you get 0.45 s of invulnerability that absorbs the rest of the volley.</li>
<li><b>Cross beams:</b> 4, and 8 after 30 s, 34 px wide with a 1.1 s warning, sweeping the whole arena. At 300 px from Arceus the gap between beams is about 200 px; right next to it there is no gap.</li>
<li><b>Shockwave:</b> only if you are closer than 210 px, radius 170, 0.85 s warning. Never get that close.</li>
<li><b>Minute 35:</b> Arceus breaks everyone’s item (Focus Sash included).</li></ul>
<h2>The legendaries</h2><ul>
<li>One every 5 s, random among the game’s 86. Each has 25% more HP and 15% more damage than the previous one.</li>
<li><b>The first one’s HP is 3 s of your own single-target damage</b> (measured before minute 30). That is why your DPS barely matters: from the third one on they pile up no matter what.</li>
<li>They run at least at 80% of your speed. Psychic, Electric, Ghost, Fairy, Fire, Water, Ice or Dragon types shoot from 300 px; the rest charge.</li>
<li>Their damage does go through your types, your defense (physical or special, by their strong side), Armor (80% cap) and your ability. Contact: 126 × 1.15ⁿ at minute 30.</li>
<li>They give experience (nothing else): each one levels you up, and the Zidra Berry heals 45%.</li></ul>
<div class="callout"><b>The only things that work on them:</b> <b>slows</b> land at 100% (Ice Beam drops them to 30% speed and with reduced cooldowns it is permanent; with Serene Grace, 20%) and <b>stuns</b> last 35%, but with Reflexes they chain, and a stunned legendary neither attacks nor hurts you on contact. Knockback does nothing, whirlpools only pull 25%, and poison and burn deal a flat 1.5.</div>
<h2>Damage to Arceus</h2><p>Only 5% of what you deal counts, decaying to 1% after 10 minutes, and your attacks only target it when no legendary is alive. It is the second ranking; it does nothing for lasting longer.</p>
<h2>What to do</h2><ol><li>Stay 250–400 px from Arceus and run wide circles along the edge. Gain distance during its pauses.</li><li>When the legendaries bunch up, stun and slow the group; do not try to kill them after the third.</li><li>Hold Leftovers (or a Focus Sash), stack Reflexes, Armor and Synthesis, and Sprint only up to the 130 cap.</li><li>Before the run: Ban Tackle, Quick Attack and Body Slam, and use Starting Move + Repertoire to open with your slow and your stun.</li></ol>'''

def validation_html(lang):
    path = os.path.join(ROOT, 'data', 'records', 'validation.json')
    if not os.path.exists(path): return ''
    V = json.load(open(path, encoding='utf-8')); s = V['spearman']; c = V['componentes']
    f = lambda x: (f'{x:.2f}'.replace('.', ',') if lang == 'es' else f'{x:.2f}')
    names = lambda L: ', '.join(f"{esc(x['name'])} ({'puesto' if lang == 'es' else 'rank'} {x['pos']}, {x['med']} s)" for x in L[:5])
    comp = ''.join(f"<tr><td>{COMP[lang][k][0]}</td><td>{f(c[k])}</td></tr>" for k in ('T', 'U', 'A', 'D', 'S', 'Z', 'V'))
    if lang == 'es':
        return f"""<h2>Contraste con récords reales</h2>
<p>El {V['records_source'].split('leído el ')[-1].split('.')[0]} se leyeron las tablas públicas del juego con las 50 mejores partidas en solitario de cada Pokémon y se calculó, para los {V['n']} Pokémon con al menos {V['min_marcas']} partidas que pasaron del minuto 30, la mediana de segundos aguantados en la Sentencia. Se descartaron las marcas de más de 20 minutos de Sentencia, imposibles con las reglas actuales. Solo se guardan agregados, ningún dato de jugadores.</p>
<table><tr><th>Predicción</th><th>Correlación con la mediana real (Spearman)</th></tr>
<tr><td>Este ranking</td><td>{f(s['modelo'])} (IC 95 %: {f(s['modelo_ic95'][0])} a {f(s['modelo_ic95'][1])})</td></tr>
<tr><td>Ranking en hordas (SurvivorTiers)</td><td>{f(s['hordas'])} (IC 95 %: {f(s['hordas_ic95'][0])} a {f(s['hordas_ic95'][1])})</td></tr>
<tr><td>Simulador propio de la Sentencia (experimental)</td><td>{f(s.get('simulador') or 0)}</td></tr>
<tr><td>Nivel mediano con el que acaban esas partidas</td><td><b>{f(s.get('nivel') or 0)}</b></td></tr></table>
<div class="callout"><b>Qué significa.</b> Ninguna de las dos listas predice bien los récords reales: en la Sentencia manda la pericia del jugador. Por componentes, lo que más se asocia a aguantar es el <b>daño</b> y el <b>tamaño pequeño</b>; el aguante ante los golpes de los legendarios, que es lo que más pesa aquí, apenas se nota. Lo que de verdad explica los récords es el <b>nivel</b> con el que se llega: cuando las cartas con tope se acaban, cada nivel da Vigor (+20 de vida) o Síntesis (regeneración), que no tienen tope. Y el nivel depende de lo bien que el Pokémon limpia hordas antes del minuto 30. El modelo se revisará con estos datos.</div>
<table><tr><th>Componente</th><th>Correlación</th></tr>{comp}</table>
<p class="small">Más arriba aquí que en la realidad: {names(V['sobrevalorados'])}. Más abajo: {names(V['infravalorados'])}.</p>"""
    return f"""<h2>Check against real records</h2>
<p>On {V['records_source'].split('leído el ')[-1].split('.')[0]} the game's public tables with the 50 best solo runs of each Pokémon were read, and for the {V['n']} Pokémon with at least {V['min_marcas']} runs past minute 30 the median seconds survived in the Judgment was computed. Runs above 20 minutes of Judgment, impossible under the current rules, were discarded. Only aggregates are kept, no player data.</p>
<table><tr><th>Prediction</th><th>Correlation with the real median (Spearman)</th></tr>
<tr><td>This ranking</td><td>{f(s['modelo'])} (95% CI: {f(s['modelo_ic95'][0])} to {f(s['modelo_ic95'][1])})</td></tr>
<tr><td>Horde ranking (SurvivorTiers)</td><td>{f(s['hordas'])} (95% CI: {f(s['hordas_ic95'][0])} to {f(s['hordas_ic95'][1])})</td></tr>
<tr><td>Own Judgment simulator (experimental)</td><td>{f(s.get('simulador') or 0)}</td></tr>
<tr><td>Median level those runs end with</td><td><b>{f(s.get('nivel') or 0)}</b></td></tr></table>
<div class="callout"><b>What it means.</b> Neither list predicts real records well: player skill dominates the Judgment. By component, what goes most with lasting is <b>damage</b> and <b>small size</b>; toughness against the legendaries' hits, the heaviest weight here, barely shows. What really explains the records is the <b>level</b> reached: once capped cards run out, every level gives Vigor (+20 HP) or Synthesis (regeneration), which have no cap. And level depends on how well the Pokémon clears hordes before minute 30. The model will be revised with this data.</div>
<table><tr><th>Component</th><th>Correlation</th></tr>{comp}</table>
<p class="small">Higher here than in reality: {names(V['sobrevalorados'])}. Lower: {names(V['infravalorados'])}.</p>"""

def method_text(lang):
    W = R['weights']; pool = R['legendary_pool']
    rows = ''.join(f"<tr><td>{COMP[lang][k][0]}</td><td>{round(W[k] * 100)} %</td><td>{COMP[lang][k][1]}</td></tr>" for k in ('T', 'U', 'A', 'D', 'S', 'Z') if W.get(k))
    pool_html = ', '.join(f"{(BY[l['dex']]['name'] if lang == 'es' else BY[l['dex']]['nameEn']) if l['dex'] in BY else l['name']}" for l in pool)
    if lang == 'es':
        return f'''<h1>Método del ranking</h1>
<p>Cada Pokémon recibe una puntuación de 0 a 1 que suma siete componentes, cada uno normalizado entre los 966 y con su peso. El puesto ordena por esa puntuación; los tiers van por puesto: S 1–30, A 31–120, B 121–320, C 321–620, D 621–966 (los mismos cortes que SurvivorTiers, para comparar).</p>
<table><tr><th>Componente</th><th>Peso</th><th>Qué mide</th></tr>{rows}</table>
<h2>Las dos variantes</h2><ul><li><b>Por defecto:</b> habilidad 1, naturaleza neutra y solo los ataques de sus tipos (más el pool Normal de todos). Es lo que tiene cualquier jugador que acaba de sacarlo del gacha.</li>
<li><b>Tienda Kecleon:</b> se prueban sus habilidades (Cápsula y Cápsula Oculta), las naturalezas que suben Defensa, Defensa Especial o Velocidad bajando el ataque que no usa (Menta), y las MT que aprende en los juegos y vende la tienda. Se queda con la combinación que más puntúa.</li></ul>
<h2>Supuestos</h2><ul><li>Mejoras permanentes al máximo del Pokémon (Vitalidad +80, Zancada ×1,24, Reflejos ×0,76, Golpe Crítico 30 %) y cartas típicas al minuto 30 (15 Vigor, 8 Carrera, 10 Reflejos).</li>
<li>Aguante = vida efectiva dividida por el daño medio que recibe del pool de {len(pool)} legendarios: cada uno pega con su tipo principal y con su lado fuerte (físico o especial), y se aplican la tabla suavizada (×1,6 / ×0,6 / ×0,3), tu defensa correspondiente y tu habilidad.</li>
<li>Control = 55 % el mejor frenazo (por su porcentaje y por lo que cubre: un rayo o un aura cubren más que un golpe cuerpo a cuerpo) y 45 % el mejor aturdimiento (duración ×0,35 en jefes frente a la recarga).</li>
<li>Daño = mejor ataque a distancia de su lado bueno contra el pool, con su habilidad. Pesa poco a propósito: la vida de los legendarios se ajusta a tu propio daño.</li>
<li>Llegar al minuto 30 <b>no puntúa</b>: el ranking mide solo lo que aguanta en la Sentencia. Lo bueno o malo que sea limpiando hordas se enseña en cada ficha (ranking y tier de SurvivorTiers, 441.000 partidas simuladas) y en el veredicto.</li></ul>
<h2>El pool de legendarios</h2><p class="small">{pool_html}.</p>
{validation_html(lang)}
<h2>Lo que no se modela</h2><p>Los objetos (se recomiendan aparte), el clima de las habilidades que lo invocan, la habilidad del jugador al esquivar y los vínculos de las grietas. Los pesos son una decisión de criterio, no una medida: dos Pokémon separados por unos puestos son, en la práctica, iguales.</p>
<h2>Créditos</h2><p>PokéSurvivor es de <a href="https://github.com/JPTER78/pokesurvivor" rel="noopener">JPTER78</a> (código bajo PolyForm Noncommercial). El ranking en hordas es de <a href="https://survivortiers.pages.dev/" rel="noopener">SurvivorTiers</a> (@fildotai). Retratos de <a href="https://github.com/PMDCollab/SpriteCollab" rel="noopener">PMD SpriteCollab</a> (CC BY-NC 4.0, ver sus créditos por artista). Pokémon © Nintendo/Creatures/GAME FREAK. Web hecha por Julio (<a href="{REPO}" rel="noopener">código y datos</a>), sin ánimo de lucro.</p>'''
    return f'''<h1>Ranking method</h1>
<p>Each Pokémon gets a 0–1 score that adds up seven components, each normalized across the 966 and weighted. Rank follows that score; tiers follow rank: S 1–30, A 31–120, B 121–320, C 321–620, D 621–966 (the same cutoffs as SurvivorTiers, for comparison).</p>
<table><tr><th>Component</th><th>Weight</th><th>What it measures</th></tr>{rows}</table>
<h2>The two variants</h2><ul><li><b>Default:</b> ability 1, neutral nature and only its own types’ moves (plus the Normal pool everyone has). What any player has right after pulling it from the gacha.</li>
<li><b>Kecleon Shop:</b> its abilities are tried (Capsule and Hidden Capsule), the natures that raise Defense, Special Defense or Speed while lowering the attack it does not use (Mint), and the TMs it learns in the games and the shop sells. The best-scoring combination is kept.</li></ul>
<h2>Assumptions</h2><ul><li>Permanent upgrades maxed for the Pokémon (Vitality +80, Stride ×1.24, Reflexes ×0.76, Critical Hit 30%) and typical cards by minute 30 (15 Vigor, 8 Sprint, 10 Reflexes).</li>
<li>Toughness = effective HP divided by the average damage taken from the pool of {len(pool)} legendaries: each hits with its primary type and its strong side (physical or special), applying the softened chart (×1.6 / ×0.6 / ×0.3), your matching defense and your ability.</li>
<li>Control = 55% the best slow (by percentage and coverage: a beam or an aura covers more than a melee hit) and 45% the best stun (duration ×0.35 on bosses against its cooldown).</li>
<li>Damage = best ranged same-side attack against the pool, with its ability. Deliberately light: the legendaries’ HP scales with your own damage.</li>
<li>Reaching minute 30 <b>does not score</b>: the ranking measures only how it lasts in the Judgment. How good or bad it is at clearing hordes is shown on each page (SurvivorTiers rank and tier, 441,000 simulated runs) and in the verdict.</li></ul>
<h2>The legendary pool</h2><p class="small">{pool_html}.</p>
{validation_html(lang)}
<h2>What is not modelled</h2><p>Items (recommended separately), the weather summoned by abilities, the player’s dodging skill and rift bonds. The weights are a judgment call, not a measurement: two Pokémon a few ranks apart are, in practice, equal.</p>
<h2>Credits</h2><p>PokéSurvivor is by <a href="https://github.com/JPTER78/pokesurvivor" rel="noopener">JPTER78</a> (code under PolyForm Noncommercial). The horde ranking is by <a href="https://survivortiers.pages.dev/" rel="noopener">SurvivorTiers</a> (@fildotai). Portraits from <a href="https://github.com/PMDCollab/SpriteCollab" rel="noopener">PMD SpriteCollab</a> (CC BY-NC 4.0, see their per-artist credits). Pokémon © Nintendo/Creatures/GAME FREAK. Site by Julio (<a href="{REPO}" rel="noopener">code and data</a>), non-profit.</p>'''

ROOT_INDEX = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Sentencia Tiers</title>
<meta name="description" content="Tier list de PokéSurvivor para la Sentencia de Arceus · PokéSurvivor tier list for Arceus' Judgment"><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="apple-touch-icon.png"><link rel="manifest" href="site.webmanifest">
<link rel="alternate" hreflang="es" href="{SITE}/es/"><link rel="alternate" hreflang="en" href="{SITE}/en/"><link rel="alternate" hreflang="x-default" href="{SITE}/es/">
<link rel="stylesheet" href="assets/style.css"><script>var l=(navigator.language||'es').slice(0,2);location.replace((l==='es'?'es':'en')+'/'+location.hash);</script></head>
<body><main class="wrap" style="padding-top:60px"><h1 style="color:var(--yellow)">SENTENCIA//TIERS</h1><p><a href="es/">Español</a> · <a href="en/">English</a></p></main></body></html>'''
FAVICON = None   # docs/favicon.svg (Poké Ball en la rueda de Arceus) y sus PNG se mantienen a mano; gen.py no los toca.

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
            return (f'<h3>{title}</h3><div class="g2"><div><table class="moves-t">{hd}{"".join(row(v, k) for v, k in ups) or '<tr><td colspan="3" class="muted">—</td></tr>'}</table></div>'
                    f'<div><table class="moves-t">{hd}{"".join(row(v, k) for v, k in downs) or '<tr><td colspan="3" class="muted">—</td></tr>'}</table></div></div>')
        out.append('<h2>' + ('Novedades del último parche' if lang == 'es' else 'Latest patch movers') + '</h2>')
        out.append('<p class="muted">' + (f"Comparado con el ranking del {DELTA['prev']['date']} (juego {esc(DELTA['prev']['game'])}): {len(d)} Pokémon cambian de puesto. En la tier list salen con flecha durante 7 días." if lang == 'es'
                   else f"Compared with the ranking of {DELTA['prev']['date']} (game {esc(DELTA['prev']['game'])}): {len(d)} Pokémon change rank. They carry an arrow in the tier list for 7 days.") + '</p>')
        out.append(tbl(0, UI[lang]['mode_base']) + tbl(1, UI[lang]['mode_shop']))
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
        write(os.path.join(DOCS, lang, 'sentencia', 'index.html'), prose_page(lang, 'nav_judg', UI[lang]['nav_judg'], judgment_text(lang), f'{lang}/sentencia/')); urls.append(f'{SITE}/{lang}/sentencia/')
        write(os.path.join(DOCS, lang, 'metodo', 'index.html'), prose_page(lang, 'nav_method', UI[lang]['nav_method'], method_text(lang), f'{lang}/metodo/')); urls.append(f'{SITE}/{lang}/metodo/')
        write(os.path.join(DOCS, lang, 'cambios', 'index.html'), prose_page(lang, 'changes', UI[lang]['changes'], changes_text(lang), f'{lang}/cambios/')); urls.append(f'{SITE}/{lang}/cambios/')
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
