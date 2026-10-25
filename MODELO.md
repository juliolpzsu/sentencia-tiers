# El modelo: cómo se ordenan los 966 Pokémon

Este documento explica con detalle qué calcula `build/rank.py`, de dónde sale cada número y qué supuestos hace. La versión corta está en la página **Método** de la web.

## 1. Qué se mide

El ranking mide **lo que un Pokémon aguanta en la Sentencia de Arceus** (lo que ocurre a partir del minuto 30 de una partida de PokéSurvivor). No mide lo bien que limpia hordas antes del minuto 30: ese dato se muestra en cada ficha (ranking y tier de SurvivorTiers) y se comenta en el veredicto, pero **no puntúa**. Fue una decisión del autor: "el que aguante más es mejor; si además es muy bueno limpiando, que se diga en su descripción".

## 2. Reglas del juego que se replican

Todo sale del código fuente del juego ([JPTER78/pokesurvivor](https://github.com/JPTER78/pokesurvivor)). Los ficheros relevantes y lo que se toma de cada uno:

| Fichero del juego | Qué se usa |
|---|---|
| `js/systems/judgment.js` | Arceus corre a 1,22× tu velocidad (más desde los 5 min), tope suave de velocidad en 130 (lo que pasa cuenta un 25 %), daño porcentual y puro (pilares 30 %, rayos 35 %, onda 40 %, toque 40 %→100 %), un legendario cada 5 s con ×1,25 vida y ×1,15 daño, vida del primero = 3 s de tu daño a un solo objetivo, legendarios a ≥80 % de tu velocidad, objetos rotos en el minuto 35. |
| `js/entities/enemy.js` | Los jefes ignoran el empuje; aturdimiento ×0,35 en jefes; los frenazos entran enteros; veneno y quemadura hacen 1,5 fijo en la Sentencia; tipo de ataque de un enemigo = su primer tipo; pega con su lado fuerte (físico o especial). |
| `js/systems/combat.js` | Zona de aturdir con 0,45 s de aviso; remolinos atraen ×0,25 a los jefes; crítico ×1,5. |
| `js/entities/player.js`, `js/systems/stats.js` | Defensas suavizadas: `clamp((75/def)^0,35, 0,78, 1,25)`; monotipo +20 % con ataques de su tipo; reducción de daño con tope 80 %. |
| `js/data/types.js` | Tabla de tipos suavizada: ×1,6 / ×0,6 / ×0,3, dos tipos se multiplican con tope [0,3, 2,4]. |
| `js/data/ability-fx.js` | Efecto de cada habilidad (absorber un tipo, ×daño recibido, esquivar, Robustez, regeneración, +daño). |
| `js/data/moves.js` | Catálogo de movimientos, escalera de mejoras (nivel 1→5) y evoluciones; qué movimientos frenan (`slow`) o aturden (`kind: stun`). |
| `js/data/pokedex.js`, `abilities.js`, `natures.js`, `tms.js`, `sprites-meta.js` | Stats, habilidades (1, 2, oculta), naturalezas, MT que aprende cada Pokémon y tamaño del sprite (radio de colisión del jugador, con tope en 18 px). |

Los datos viven en `data/game/` como copia literal. `build/gamedata.py` los parsea.

## 3. El pool de legendarios

Los 86 legendarios que pueden acudir a la Sentencia (todos los `leg` del juego con sprite, menos Arceus). Para cada uno se toma su tipo de ataque (primer tipo) y su lado fuerte. Distribución de tipos de ataque: Psíquico 18, Dragón 8, Agua 7, Acero 7, Eléctrico 6, Fuego 5, Normal 5, Lucha 5, Planta 4, Hielo 3, Roca 3, Siniestro 3, Hada 3, Veneno 3, Tierra 2, Fantasma 2, Volador 1, Bicho 1. De ellos, 52 disparan desde 300 px (tipos Psíquico, Eléctrico, Fantasma, Hada, Fuego, Agua, Hielo o Dragón) y el resto embiste.

## 4. Componentes de la puntuación

Cada componente se calcula en bruto, se normaliza entre los 966 (mín→0, máx→1; los de escala amplia en logaritmo) y se pondera:

| Componente | Peso | Cálculo en bruto |
|---|---|---|
| **Aguante ante legendarios (T)** | 36 % | `vida efectiva / daño medio recibido`. Vida efectiva = vida base + 80 (Vitalidad) + 300 (15 cartas de Vigor), ×1,25 si tiene Robustez. Daño medio = media sobre los 86 legendarios de `tabla(tipo atacante, tus tipos) × defensa suavizada (física o especial según el legendario) × habilidad (×daño recibido, absorber, esquivar)`. Normalizado en log. |
| **Control (U)** | 32 % | `0,55 × frenazo + 0,45 × aturdimiento`. Frenazo = mejor `min(0,8, slow × 2 si Dicha) × cobertura del tipo de ataque` (rayo 1,0 · aura 0,95 · ráfaga 0,9 · perseguidor y meteoros 0,85 · proyectil 0,7 · minas 0,65 · abanico 0,6…) dividido por 0,8. Los frenazos cuerpo a cuerpo no cuentan (obligan a pegarse a los legendarios). Aturdimiento = `min(1, duración × 0,35 / recarga efectiva)`; con Reflejos al máximo los cuatro aturdimientos del juego llegan a 1. |
| **Regeneración (A)** | 10 % | Habilidad (Regeneración 0,6 %/s, Cura Natural y Alma Cura 0,3 %/s, Mudar 0,4 %/s) + Acua Aro en su pool + Robustez + habilidades que multiplican las curas. Normalizado en log1p. |
| **Daño a un legendario (D)** | 10 % | Mejor ataque a distancia de su lado bueno: `daño/s al nivel máximo evolucionado × ataque del lado × monotipo × eficacia media contra el pool × habilidad`, con penalización ×0,5 para los que obligan a estar pegado. Pesa poco a propósito: la vida de cada legendario se ajusta a tu propio daño. |
| **Velocidad efectiva (S)** | 8 % | `tope_suave(velocidad × 1,24 (Zancada) × 1,07⁸ (Carrera))` con el tope de 130; Impulso y Fuga suman. |
| **Tamaño (Z)** | 4 % | `1 / (44 + 0,6 × radio)²`: el área en la que te pilla un pilar. Radio del jugador según el sprite, con tope en 18 px. |

Tiers por puesto: S 1–30, A 31–120, B 121–320, C 321–620, D 621–966 (los mismos cortes que SurvivorTiers, para poder comparar).

## 5. Las dos variantes

- **Por defecto**: habilidad 1 (a cada cuenta le toca al azar la 1 o la 2; la oculta 1 de cada 20), naturaleza neutra, solo los movimientos de sus tipos más el pool Normal común.
- **Tienda Kecleon**: se prueban todas sus habilidades (Cápsula Habilidad para la 2, Cápsula Habilidad Oculta para la oculta), las naturalezas que suben Defensa, Defensa Especial o Velocidad y bajan el ataque que no usa (Menta), y las MT que aprende en los juegos y vende la tienda. Se queda la combinación con mayor puntuación. La normalización es la de la pasada por defecto, para que ambas variantes se comparen en la misma escala.

## 6. La build recomendada

Para cada variante se eligen cuatro huecos en este orden: frenazo a distancia → aturdimiento → ataque principal (el mejor a distancia de su lado bueno; una MT solo entra como principal si rinde un 30 % más que el mejor natural) → Acua Aro si lo tiene → potenciador de su lado (Danza Espada, Danza Dragón o Maquinación) → segundo ataque natural → Agilidad. Además: movimiento inicial (el frenazo si es un ataque, si no el principal), segundo inicial para Repertorio (el aturdimiento), tres vetos (Placaje, Ataque Rápido, Golpe Cuerpo…), la condición de evolución de cada ataque elegido, el número de cartas de Carrera hasta el tope de 130, y el objeto recomendado (Restos, o Banda Focus si ya regenera con Acua Aro).

Los empates se deshacen a favor del movimiento natural y, después, por nombre: el resultado es **determinista** (tres ejecuciones con semillas distintas producen el mismo fichero).

## 7. Supuestos y límites

- Mejoras permanentes al máximo del Pokémon y cartas típicas al minuto 30 (15 Vigor, 8 Carrera, 10 Reflejos). Coraza llega al tope del 80 % para todos, así que no diferencia.
- Un solo movimiento activo a la vez: frenazo y aturdimiento solo coinciden con un vínculo de grieta. El componente de control los suma igualmente; la ficha recomienda fusionarlos.
- No se modelan los objetos (se recomiendan aparte), el clima de las habilidades que lo invocan, los vínculos ni la pericia del jugador al esquivar.
- Los pesos son una decisión de criterio, no una medida: dos Pokémon separados por unos puestos son, en la práctica, iguales.
- La verificación del sorteo de habilidad y naturaleza por cuenta (hash FNV con la fecha de creación de la partida) se hizo contra una cuenta real, pero la web no personaliza: usa la habilidad 1.

## 8. Regenerar y actualizar

```
python -I build/rank.py      # data/ranking.json (la guía)
python -I build/gen.py       # docs/ (la web)
python -I build/update.py    # comprueba el juego y, si el ranking cambia, actualiza ambos
```

La Action `.github/workflows/update.yml` ejecuta `update.py` a diario. Si el juego cambia alguno de los ficheros de reglas de la tabla del apartado 2, la entrada de `data/CHANGELOG.md` lleva la marca **REVISAR REGLAS**: hay que leer el cambio y adaptar `rank.py` a mano, porque las reglas no se leen del juego, se replican.

## 9. Contraste con récords reales y simulador (24-10-2026)

**Datos.** Se leyeron una vez, desde una sesión iniciada en el juego, las tablas públicas `lbs/s_all4_p<dex>` (top 50 en solitario de cada Pokémon desde el parche del 23-10). Se guardan solo agregados por Pokémon en `data/records/records.json`: número de marcas, cuántas pasan del minuto 30, mediana/p75/p90 de segundos de Sentencia y nivel final mediano. Se descartan 23 marcas de más de 20 min de Sentencia (imposibles con las reglas). La mediana por Pokémon es muy fiable: entre dos mitades aleatorias de sus marcas, Spearman 0,86 (0,93 con todas).

**Resultados** (`build/validate.py`, 195 Pokémon con ≥10 marcas en Sentencia, Spearman con la mediana real):

| Predicción | Correlación |
|---|---|
| Este ranking | 0,08 |
| Ranking en hordas (SurvivorTiers) | 0,12 |
| Simulador (`build/sim.py`) | ≈0 |
| Ataque base | 0,24 |
| **Nivel final mediano** | **0,64** (0,73 con ≥20 marcas) |

Dentro de cada Pokémon, más nivel también es más Sentencia (Spearman medio 0,22, positivo en 121 de 144). Explicación compatible con el código: con el nivel típico del minuto 30 las cartas con tope ya se han agotado y cada nivel extra da Vigor (+20 de vida) o Síntesis (+0,9 PS/s), sin tope. El nivel depende de lo bien que el Pokémon limpia hordas (el ataque explica el nivel con 0,39). Es decir: **lo de antes del minuto 30 sí importa para la Sentencia**, no por llegar, sino por el nivel con el que se llega.

**Simulador** (`build/sim.py`). Reproduce la arena, el ciclo de Arceus, los legendarios con su vida mínima y crecimiento, el contacto y las zonas con aviso, la build por defecto y un bot que huye por la pared y esquiva lo que ve venir. Simula 966 × 16 partidas en ~70 s. Hoy no predice los récords: el bot muere casi siempre por los toques de Arceus, que quitan un porcentaje y no dependen de la vida, mientras que los buenos jugadores casi no los reciben. Para que sirva hace falta un bot que evite esos toques y modelar el nivel al minuto 30. Se publica como experimental y no entra en la puntuación.

## 10. Ranking empírico + modelo (desde el 25-10-2026)

Decisión de Julio tras el contraste del apartado 9: el puesto ya no lo da la puntuación de los componentes, sino los **segundos estimados** que aguanta un buen jugador en la Sentencia (`build/blend.py`, lo llama `rank.py`).

1. **Predicción** para los 966: regresión ridge sobre ataque, log del radio, ranking en hordas, vida, velocidad, BST, legendario y los seis componentes T, U, A, D, S, Z. Objetivo: log de la mediana real. Se ajusta con los Pokémon con ≥10 marcas en Sentencia; alpha por validación cruzada (5 particiones × 6 repeticiones). Acierta el orden fuera de muestra con Spearman ≈ 0,29; la puntuación antigua sola, ≈ 0,09.
2. **Mezcla** en escala log: `est = (nj·real + K·pred) / (nj + K)` con K = 10 (con 10 partidas reales, mitad y mitad).
3. **Tienda Kecleon**: `est_tienda = est · exp(pred(componentes de tienda) − pred(componentes por defecto))`.
4. Puestos y tiers por `est`; los puestos de la puntuación antigua quedan en `model_pos`. La ficha enseña los segundos y de dónde salen.

Sesgo conocido: los récords son el top 50 de cada Pokémon; los raros los juegan sobre todo veteranos con más mejoras. La estimación es "en buenas manos". El puesto personal de "Mi partida" sigue usando la puntuación de componentes con tu habilidad y naturaleza.
