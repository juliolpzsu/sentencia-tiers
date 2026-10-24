# Sentencia Tiers

Tier list de **PokéSurvivor** para la **Sentencia de Arceus** (minuto 30): los 966 Pokémon ordenados por lo que aguantan contra Arceus y los legendarios que acuden, no por las hordas. En español e inglés.

**Web:** https://juliolpzsu.github.io/sentencia-tiers/

## Qué hay

- `data/ranking.json` — la guía: puesto, tier, componentes, build por defecto y build con Tienda Kecleon (habilidad, naturaleza, MT) de cada Pokémon. Es lo que genera la web.
- `docs/` — la web estática publicada con GitHub Pages (una página por Pokémon e idioma).
- `build/rank.py` — calcula el ranking replicando las reglas del código del juego.
- `build/gen.py` — genera la web a partir del ranking.
- `build/fetch_portraits.py` — descarga los retratos de PMD SpriteCollab.
- `data/game/` — copia de los datos del juego (Pokédex, movimientos, habilidades, naturalezas, MT, sprites) y del índice de SurvivorTiers.

## Cómo se calcula

Siete componentes normalizados entre los 966 y ponderados: llegar al minuto 30 (ranking en hordas de SurvivorTiers), aguante frente al pool de 86 legendarios (vida, defensas, tipos, habilidad), control (frenazos y aturdimientos, lo único que afecta a los jefes), regeneración frente al daño porcentual de Arceus, daño a un legendario, velocidad efectiva con el tope suave de 130 y tamaño de colisión. El detalle está en la página **Método** de la web.

## Regenerar

```
python -I build/rank.py      # data/ranking.json
python -I build/gen.py       # docs/
python -I build/fetch_portraits.py   # sólo si faltan retratos
```

Sin dependencias fuera de la biblioteca estándar de Python 3.

## Créditos

- PokéSurvivor es de [JPTER78](https://github.com/JPTER78/pokesurvivor) (código bajo PolyForm Noncommercial 1.0.0). Las reglas replicadas corresponden al commit `5a23d49` (23-10-2026).
- Ranking en hordas: [SurvivorTiers](https://survivortiers.pages.dev/) (@fildotai).
- Retratos: [PMD SpriteCollab](https://github.com/PMDCollab/SpriteCollab), CC BY-NC 4.0 (créditos por artista en su repositorio).
- Pokémon © Nintendo / Creatures / GAME FREAK. Proyecto de fans sin ánimo de lucro.

## Licencia

El código de este repositorio (`build/`, `docs/assets/`) es MIT. Los datos del juego, los retratos y los nombres de Pokémon pertenecen a sus autores y se usan sin ánimo de lucro.
