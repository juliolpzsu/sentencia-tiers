# Sentencia Tiers

[![Web](https://img.shields.io/badge/web-juliolpzsu.github.io%2Fsentencia--tiers-fcee0a?labelColor=07070a)](https://juliolpzsu.github.io/sentencia-tiers/)
[![Actualización automática](https://github.com/juliolpzsu/sentencia-tiers/actions/workflows/update.yml/badge.svg)](https://github.com/juliolpzsu/sentencia-tiers/actions/workflows/update.yml)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-ff003c?labelColor=07070a)](LICENSE)
![Sin dependencias](https://img.shields.io/badge/dependencias-ninguna-00e5ff?labelColor=07070a)

Tier list de **PokéSurvivor** para la **Sentencia de Arceus**: los 966 Pokémon ordenados por lo que aguantan a partir del minuto 30, con una ficha por Pokémon (build, habilidades, objetos y estrategia) en español e inglés.

**→ https://juliolpzsu.github.io/sentencia-tiers/** · [English README](README.en.md)

![Tier list](assets/readme/readme-tiers.png)

## Por qué existe

Las tier lists de PokéSurvivor ordenan por lo que un Pokémon aguanta contra las hordas. Pero en el minuto 30 el juego cambia: Arceus baja a la arena, es invencible, corre más que tú y cada cinco segundos acude un legendario más fuerte. Lo que importa ahí no es el daño (la vida de los legendarios se ajusta a tu propio daño), sino **frenarlos, aturdirlos, aguantar sus golpes y regenerar** el daño porcentual de Arceus. Esta web ordena por eso.

Todo el cálculo sale del **código fuente del juego**, no de la experiencia de nadie: se replican las reglas de la Sentencia, la tabla de tipos suavizada, las defensas, las habilidades y los movimientos tal y como están programados.

## Qué ofrece la web

- **Tier list** de los 966 con buscador, orden (puesto, componentes, vida, velocidad…), agrupación (tier, tipo, legendarios) y filtros (tipo, tier, legendarios, con frenazo, con aturdimiento, con regeneración).
- Dos variantes conmutables: **Por defecto** (habilidad 1, naturaleza neutra, ataques naturales) y **Tienda Kecleon** (mejor habilidad con Cápsula, mejor naturaleza con Menta y las MT que le sirven).
- **Ficha por Pokémon**: veredicto, estrategia generada a partir de sus datos, desglose de la puntuación, estadísticas, daño recibido por cada tipo frente al pool real de legendarios, sus tres habilidades con el efecto exacto en el juego, y la build de cada variante: cuatro movimientos con el porqué, movimiento inicial, vetos, objeto, prioridad de cartas y condiciones de evolución.
- Páginas **La Sentencia** (la mecánica completa, con números) y **Método** (pesos, supuestos, pool de legendarios y créditos).
- Estética *Night City*, legible en móvil e iPad, sin dependencias ni rastreadores.

![Ficha de un Pokémon](assets/readme/readme-ficha.png)

## Cómo se calcula

Seis componentes normalizados entre los 966 y ponderados:

| Componente | Peso | Qué mide |
|---|---|---|
| Aguante ante legendarios | 36 % | Vida efectiva frente al daño medio del pool de 86 legendarios (tipos, defensas, habilidad) |
| Control | 32 % | Frenazos (entran al 100 % en jefes) y aturdimientos (×0,35 pero encadenables) |
| Regeneración | 10 % | Lo único que compensa el daño porcentual de Arceus |
| Daño a un legendario | 10 % | Mejor ataque a distancia de su lado bueno |
| Velocidad efectiva | 8 % | Con el tope suave de 130 que impone la Sentencia |
| Tamaño | 4 % | Radio de colisión: más pequeño, más fácil esquivar |

Llegar al minuto 30 **no puntúa**: lo bueno o malo que sea limpiando hordas se indica en cada ficha (ranking de SurvivorTiers) y en el veredicto. El detalle completo, con las fórmulas y los ficheros del juego de los que sale cada regla, está en [MODELO.md](MODELO.md).

## Estructura del repositorio

```
.
├── build/
│   ├── gamedata.py        Carga y parseo de los datos del juego (data/game)
│   ├── abilfx.py          Descripción de cada habilidad tal como la enseña el juego
│   ├── rank.py            El modelo: calcula data/ranking.json (la guía)
│   ├── gen.py             Genera la web estática (docs/) en ES y EN
│   ├── fetch_portraits.py Descarga los retratos (PMD SpriteCollab)
│   └── update.py          Comprueba si el juego cambió y, si afecta al ranking, lo actualiza
├── data/
│   ├── game/              Copia literal de los datos del juego + VERSION y RULES.sha
│   ├── ranking.json       La guía: puesto, tier, componentes y builds de cada Pokémon
│   └── CHANGELOG.md       Historial de las actualizaciones automáticas
├── docs/                  La web publicada con GitHub Pages (generada, no editar a mano)
│   ├── es/ · en/          Índice, fichas y páginas de cada idioma
│   ├── assets/            style.css, app.js (índice), page.js (fichas)
│   └── img/p/             Retratos
├── assets/readme/         Capturas para este README
└── .github/workflows/     update.yml: actualización automática diaria
```

## Reproducir o modificar

Solo hace falta **Python 3.12 o superior**; no hay dependencias externas.

```bash
python -I build/rank.py             # recalcula data/ranking.json
python -I build/gen.py              # regenera docs/
python -I build/fetch_portraits.py  # solo si faltan retratos
python -I build/update.py           # baja los datos del juego y actualiza si el ranking cambia
```

Para probar la web en local: `python -m http.server 8000 -d docs` y abrir `http://localhost:8000/es/`.

Los pesos están en `W` dentro de `build/rank.py`; la lógica de la build, en `choose_build`; los textos de la web, en los diccionarios `UI`, `ITEMS` y las funciones `reason`, `cards_text`, `strategy` y `verdict` de `build/gen.py`.

## Actualización automática

Una GitHub Action corre cada día a las 06:30 UTC (y a mano desde la pestaña *Actions*, con la opción `force`):

1. Descarga los ficheros de datos del juego desde su repositorio público y el índice de SurvivorTiers.
2. Si alguno cambió, anota el commit del juego en `data/game/VERSION` y recalcula el ranking.
3. Si el ranking cambia (puestos, puntuaciones o builds), regenera la web, escribe la entrada en `data/CHANGELOG.md` y publica el commit como `sentencia-tiers[bot]`. Si el juego cambió pero el orden es el mismo, no toca nada.
4. Si cambian los ficheros de **reglas** que el modelo replica a mano (`judgment.js`, `combat.js`, `enemy.js`, `player.js`, `stats.js`), lo marca con **REVISAR REGLAS**: hay que leer el cambio y adaptar `rank.py`.

## Contribuir

Las correcciones de datos, de textos o del modelo son bienvenidas: lee [CONTRIBUTING.md](CONTRIBUTING.md). Si ves un error en una ficha, abre una incidencia con la plantilla *Error en una ficha*.

## Créditos y licencia

- **PokéSurvivor** es de [JPTER78](https://github.com/JPTER78/pokesurvivor) (código bajo PolyForm Noncommercial 1.0.0). Los datos de `data/game/` son copia de su repositorio.
- El ranking en hordas que se muestra en cada ficha es de [SurvivorTiers](https://survivortiers.pages.dev/) (@fildotai).
- Retratos de [PMD SpriteCollab](https://github.com/PMDCollab/SpriteCollab), CC BY-NC 4.0 (créditos por artista en su repositorio).
- Pokémon © Nintendo / Creatures / GAME FREAK.

El código de este repositorio (`build/`, `docs/assets/`) es [MIT](LICENSE). Los datos del juego, los retratos y los nombres pertenecen a sus autores y se usan en un proyecto de fans sin ánimo de lucro, sin relación con los autores del juego ni con Nintendo.
