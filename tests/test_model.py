"""Pruebas del modelo y de los datos generados (biblioteca estándar, sin dependencias).
Uso: python -I -m unittest discover -s tests -v
"""
import json, os, sys, unittest, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import gamedata as G   # noqa: E402

RANK = os.path.join(ROOT, 'data', 'ranking.json')

class TestGameData(unittest.TestCase):
    def test_pokedex(self):
        self.assertEqual(len([d for d in G.DEX if d in G.META]), 966)
        self.assertEqual(G.DEX[802]['name'], 'Marshadow')
    def test_moves_and_pools(self):
        self.assertGreaterEqual(len(G.MOVES), 100)
        self.assertEqual(G.MOVES['ice-beam']['slow'], 0.7)
        self.assertEqual(G.MOVES['freeze-dry']['kind'], 'stun')
        self.assertIn('ice-beam', G.natural_pool(91))          # Cloyster
        self.assertIn('ice-beam', G.tm_extra(809))              # Melmetal por MT
    def test_type_chart(self):
        self.assertEqual(len(G.CHART), 18)
        self.assertAlmostEqual(G.tmult('fighting', ['steel']), 1.6)
        self.assertAlmostEqual(G.tmult('ghost', ['normal']), 0.3)
        self.assertAlmostEqual(G.tmult('ice', ['dragon', 'flying']), 2.4)   # tope
    def test_guard(self):
        self.assertAlmostEqual(G.guard(75), 1.0)
        self.assertEqual(G.guard(300), 0.78); self.assertEqual(G.guard(10), 1.25)
    def test_abilities_and_tms(self):
        self.assertEqual(G.DEX_ABIL[91], ['shell-armor', 'skill-link', 'overcoat'])
        self.assertIn('ice-beam', G.TM_MOVES)
    def test_english(self):
        self.assertEqual(G.en('Rayo Hielo'), 'Ice Beam')
        self.assertEqual(G.en('+8 % de daño con movimientos de tipo Agua.'), '+8% damage with Water-type moves.')

class TestRanking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = json.load(open(RANK, encoding='utf-8')); cls.P = cls.R['pokemon']
    def test_shape(self):
        self.assertEqual(len(self.P), 966)
        for key in ('base', 'shop'):
            pos = sorted(p[key]['pos'] for p in self.P)
            self.assertEqual(pos, list(range(1, 967)), key)
        self.assertAlmostEqual(sum(self.R['weights'].values()), 1.0)
    def test_tiers_by_position(self):
        for p in self.P:
            pos, tier = p['base']['pos'], p['base']['tier']
            exp = 'S' if pos <= 30 else 'A' if pos <= 120 else 'B' if pos <= 320 else 'C' if pos <= 620 else 'D'
            self.assertEqual(tier, exp, p['name'])
    def test_builds(self):
        for p in self.P:
            for key in ('base', 'shop'):
                b = p[key]['build']; ids = [m['id'] for m in b['moves']]
                self.assertEqual(len(ids), len(set(ids)))
                # huecos (27-10-2026): 1 = grupo que farmea (hasta 4, para fusionar), 2 = Ataque Rápido, 3-4 = control
                slots = [m['slot'] for m in b['moves']]
                self.assertLessEqual(slots.count(1), 4, p['name']); self.assertTrue(set(slots) <= {1, 2, 3, 4}, p['name'])
                self.assertLessEqual(len({s for s in slots if s >= 3}), 2, p['name'])
                self.assertEqual(slots, sorted(slots), p['name'])
                self.assertEqual(b['moves'][0]['code'], 'primary', p['name'])
                self.assertIn('quick-attack', ids, p['name']); self.assertNotIn('quick-attack', b['bans'])
                self.assertTrue(any(G.MOVES[i]['kind'] != 'buff' for i in ids), p['name'])
                self.assertLessEqual(sum(1 for i in ids if G.MOVES[i]['kind'] == 'buff'), 2, p['name'])
                if b['start']: self.assertIn(b['start'], ids); self.assertNotEqual(G.MOVES[b['start']]['kind'], 'buff')
                if p[key]['slow']: self.assertNotIn(G.MOVES[p[key]['slow']]['kind'], ('melee', 'spin', 'aura', 'dash', 'orbit', 'trail'), p['name'])
            # la build por defecto solo usa movimientos naturales
            nat = G.natural_pool(p['dex'])
            for m in p['base']['build']['moves']: self.assertIn(m['id'], nat, p['name'])
    def test_advisor_data(self):
        """Los datos de la extensión (Consejero) cubren a los 966 y usan papeles y stats que conoce."""
        import advisor
        d = advisor.advisor_data(self.R, lambda p: str(p['dex']))
        self.assertEqual(len(d['mons']), 966)
        roles = {'slow', 'stun', 'primary', 'second', 'buff', 'aquaring', 'agility', 'dash'}
        stats = {'hp', 'atk', 'spd', 'cd', 'def', 'rgn', 'mag', 'xp'}
        for e in d['mons'].values():
            for b in filter(None, (e['b'], e.get('k'))):
                self.assertTrue(b["m"] and all(e[1] in roles and e[2] in (1, 2, 3, 4) for e in b["m"]))
                self.assertTrue(set(b.get('e', {}).values()) <= stats)
        self.assertEqual(d['mons']['91']['b']['m'][0][1], 'primary')
        self.assertIn(['quick-attack', 'dash', 2], d['mons']['91']['b']['m'])
    def test_shop_never_worse(self):
        """La Tienda elige habilidad, naturaleza y MT por segundos estimados: nunca aguanta menos que por defecto."""
        for p in self.P: self.assertGreaterEqual(p['shop']['est'], p['base']['est'], p['name'])
    def test_no_wasted_speed_nature(self):
        """Ninguna Menta de +Velocidad para quien ya llega al tope suave de 130 con Zancada al máximo."""
        import rank
        for p in self.P:
            n = p['shop']['nature']
            if n and G.NATURES[[x['id'] for x in G.NATURES].index(n)]['up'] == 'spd':
                self.assertLess(p['stats']['spd'] * rank.UPG_SPD, 130, p['name'])
    def test_known_facts(self):
        by = {p['name']: p for p in self.P}
        self.assertLess(by['Dialga']['base']['T_mult'], by['Snom']['base']['T_mult'])          # Acero/Dragón aguanta más que Bicho/Hielo
        self.assertEqual(by['Cloyster']['base']['slow'], 'ice-beam'); self.assertEqual(by['Cloyster']['base']['stun'], 'freeze-dry')
        self.assertIsNone(by['Kartana']['base']['slow']); self.assertIsNone(by['Kartana']['base']['stun'])
        self.assertIn('ice-beam', [t['id'] for t in by['Melmetal']['shop']['tms']])
        self.assertIn('0', by['Cloyster']['abil_scores'])
    def test_nature_scores(self):
        """an_scores: 25 naturalezas por habilidad; las neutras coinciden con abil_scores y la mejor no baja de la neutra."""
        import gamedata as G2
        neutral = [i for i, n in enumerate(G2.NATURES) if not n['up']]
        for p in self.P:
            for slot, row in p['an_scores'].items():
                self.assertEqual(len(row), 25, p['name'])
                for i in neutral: self.assertAlmostEqual(row[i] / 10000, p['abil_scores'][slot], places=3)
    def test_blend_order(self):
        """El puesto sigue a los segundos estimados (empírico + modelo) y la predicción mejora a la puntuación sola."""
        self.assertIn('blend', self.R)
        for key in ('base', 'shop'):
            order = sorted(self.P, key=lambda p: p[key]['pos'])
            ests = [p[key]['est'] for p in order]
            self.assertEqual(ests, sorted(ests, reverse=True), key)
        self.assertGreater(self.R['blend']['cv_spearman'], self.R['blend']['model_only_cv'])
    def test_deterministic(self):
        """rank.py produce el mismo fichero dos veces (con semillas de hash distintas)."""
        tmp = os.path.join(ROOT, 'data', 'ranking.json')
        before = open(tmp, 'rb').read()
        try:
            for seed in ('1', '424242'):
                env = dict(os.environ, PYTHONHASHSEED=seed)
                r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'build', 'rank.py')], capture_output=True, text=True, env=env, encoding='utf-8')
                self.assertEqual(r.returncode, 0, r.stderr[-2000:])
                now = json.load(open(tmp, encoding='utf-8')); ref = json.loads(before)
                now.pop('generated'); ref.pop('generated')
                self.assertEqual(hashlib.sha256(json.dumps(now, sort_keys=True).encode()).hexdigest(), hashlib.sha256(json.dumps(ref, sort_keys=True).encode()).hexdigest(), f'seed {seed}')
        finally:
            open(tmp, 'wb').write(before)

if __name__ == '__main__':
    unittest.main()
