# Sentencia Tiers

[![Web](https://img.shields.io/badge/web-juliolpzsu.github.io%2Fsentencia--tiers-fcee0a?labelColor=07070a)](https://juliolpzsu.github.io/sentencia-tiers/)
[![Actualización automática](https://github.com/juliolpzsu/sentencia-tiers/actions/workflows/update.yml/badge.svg)](https://github.com/juliolpzsu/sentencia-tiers/actions/workflows/update.yml)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-ff003c?labelColor=07070a)](LICENSE)
![Sin dependencias](https://img.shields.io/badge/dependencias-ninguna-00e5ff?labelColor=07070a)

Tier list de **PokéSurvivor** para la **Sentencia de Arceus**: los 966 Pokémon ordenados por lo que aguantan a partir del minuto 30, con una ficha por Pokémon (build, habilidades, objetos y estrategia) en español e inglés.

**→ https://juliolpzsu.github.io/sentencia-tiers/** · [English README](README.en.md)

![Tier list](assets/readme/readme-tiers.png)

## Por qué existe

Las tier lists de PokéSurvivor ordenan por lo que un Pokémon aguanta contra las hordas. Pero en el minuto 30 el juego cambia: Arceus baja a la arena, es invencible, corre más que tú, su daño es un porcentaje de tu vida y cada cinco segundos acude un legendario más fuerte. Lo que más explica cuánto aguanta cada Pokémon ahí, según los récords reales, es el **nivel con el que llega** (lo bien que farmea antes) y lo fácil que le resulta **esquivar**. Esta web ordena por eso.

Todo el cálculo sale del **código fuente del juego**, no de la experiencia de nadie: se replican las reglas de la Sentencia, la tabla de tipos suavizada, las defensas, las habilidades y los movimientos tal y como están programados.

## Qué ofrece la web

- **Tier list** de los 966 con buscador, orden (puesto, componentes, vida, velocidad…), agrupación (tier, tipo, legendarios) y filtros (tipo, tier, legendarios, con frenazo, con aturdimiento, con regeneración).
- Dos variantes conmutables: **Por defecto** (habilidad 1, naturaleza neutra, ataques naturales) y **Tienda Kecleon** (mejor habilidad con Cápsula, mejor naturaleza con Menta y las MT que le sirven).
- **Ficha por Pokémon**: veredicto, estrategia generada a partir de sus datos, desglose de la puntuación, estadísticas, daño recibido por cada tipo frente al pool real de legendarios, sus tres habilidades con el efecto exacto en el juego, y la build de cada variante: cuatro movimientos con el porqué, movimiento inicial, vetos, objeto, prioridad de cartas y condiciones de evolución.
- **Mi partida** (opcional): pegas el guardado de tu cuenta y la web marca los Pokémon que tienes, sus mejoras compradas, la habilidad y naturaleza que te tocaron y tu puesto aproximado con esa habilidad. Se queda en tu navegador; no se envía a ningún sitio.
- **MT a la venta hoy**: la web calcula las 8 MT diarias de la Tienda Kecleon con la misma fórmula que el juego (verificado contra la tienda real), marca cuántas builds usan cada una y filtra los Pokémon a los que su build les pide una de hoy.
- El buscador encuentra también por **ataque** (de la build o aprendible por MT) y por **habilidad**.
- Página **Cooperativo**: tier list para jugar en grupo (cuentan también farmear, controlar y la velocidad) y equipos de 2, 3 y 4 con sus builds.
- Página **Cambios** con el historial de las actualizaciones automáticas.
- Los filtros, el orden y la variante viajan en la **URL**, así que cualquier vista se puede compartir con un enlace; cada página lleva su tarjeta de vista previa para Discord, WhatsApp o X.
- Página **La Sentencia**: la mecánica completa, con números, en una pantalla. El método está en [MODELO.md](MODELO.md).
- Estética *Night City*, legible en móvil e iPad, sin dependencias ni rastreadores.
- **Consejero** ([Chrome Web Store](https://chromewebstore.google.com/detail/glehijclpafhcajjdcmmcaepkjeianlo) · [código](extension/README.md)): extensión de navegador que, dentro del juego, marca en cada subida de nivel qué carta coger según la build de la ficha, y además recomienda objeto y vínculo y ayuda durante la Sentencia. Compatible con PokeSurvivor Plus.

![Ficha de un Pokémon](assets/readme/readme-ficha.png)

## Cómo se calcula

El puesto lo dan los **segundos estimados** que aguanta un buen jugador en la Sentencia:

1. **Récords reales**: la mediana de las mejores partidas de cada Pokémon en las tablas públicas del juego.
2. **Predicción** para los 966: una regresión ajustada con los que tienen récords, a partir del ataque, el lado especial, el tamaño, el ranking en hordas, la vida, la velocidad y seis componentes calculados desde el código del juego (aguante ante los legendarios, control, regeneración, daño, velocidad efectiva y tamaño). Acierta el orden fuera de muestra con una correlación de 0,39.
3. Se mezclan en escala logarítmica: cuantas más partidas reales tiene un Pokémon, más pesan.

La variante **Tienda Kecleon** elige la habilidad, la naturaleza y las MT que más segundos estiman. El detalle completo, con las fórmulas y los ficheros del juego de los que sale cada regla, está en [MODELO.md](MODELO.md).

## Estructura del repositorio

```
.
├── build/
│   ├── gamedata.py        Carga y parseo de los datos del juego (data/game)
│   ├── abilfx.py          Descripción de cada habilidad tal como la enseña el juego
│   ├── rank.py            El modelo: calcula data/ranking.json (la guía)
│   ├── gen.py             Genera la web estática (docs/) en ES y EN
│   ├── advisor.py         Datos del Consejero (docs/assets/advisor.json y extension/data.js)
│   ├── coop.py            Tier list del cooperativo y equipos (data/coop.json)
│   ├── icons.py           Iconos pixel art del juego en SVG (docs/img/i)
│   ├── fetch_portraits.py Descarga los retratos (PMD SpriteCollab)
│   └── update.py          Comprueba si el juego cambió y, si afecta al ranking, lo actualiza
├── data/
│   ├── game/              Copia literal de los datos del juego + VERSION y RULES.sha
│   ├── ranking.json       La guía: puesto, tier, componentes y builds de cada Pokémon
│   └── CHANGELOG.md       Historial de las actualizaciones automáticas
├── docs/                  La web publicada con GitHub Pages (generada, no editar a mano)
│   ├── es/ · en/          Índice, fichas y páginas de cada idioma
│   ├── assets/            style.css, app.js (índice), page.js (fichas), save.js (partida del jugador), scores.json
│   └── img/p/             Retratos
├── extension/             Consejero: extensión del navegador para las cartas de subida de nivel
├── tests/                 Pruebas del modelo (unittest, sin dependencias)
├── assets/readme/         Capturas para este README
└── .github/workflows/     update.yml: actualización automática diaria · tests.yml: pruebas en cada push
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

Pruebas (datos, ranking, builds y determinismo): `python -I -m unittest discover -s tests -v`. Corren en cada push (`tests.yml`) y antes de publicar una actualización automática.

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
