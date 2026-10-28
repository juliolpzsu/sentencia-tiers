# El modelo: cómo se ordenan los 966 Pokémon

Este documento explica con detalle qué calcula `build/rank.py`, de dónde sale cada número y qué supuestos hace. La web no tiene página de método: este es el sitio.

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
- **Tienda Kecleon**: se prueban todas sus habilidades (Cápsula Habilidad para la 2, Cápsula Habilidad Oculta para la oculta), las naturalezas que bajan el ataque que no usa y suben el que usa, la Defensa, la Defensa Especial o la Velocidad (Menta; la de Velocidad solo si con Zancada al máximo no llega al tope de 130), y las MT que aprende en los juegos y vende la tienda. Desde el 28-10-2026 se queda la combinación que más **segundos estimados** da (la predicción del apartado 10), no la de mayor puntuación de componentes; la versión por defecto también es candidata, así que la tienda nunca aguanta menos. La normalización es la de la pasada por defecto, para que ambas variantes se comparen en la misma escala.

## 6. La build recomendada

Desde el 27-10-2026 la build sigue cómo juegan los que más aguantan (el nivel con el que se llega al minuto 30 es lo que más explica la Sentencia, apartado 9), por huecos:

- **Hueco 1, el grupo que farmea** (hasta 4, para fusionarlos en las grietas: un grupo fusionado se lanza a la vez y solo dispara el hueco activo): el ataque principal, el potenciador de su lado (Danza Espada, Danza Dragón o Maquinación) y dos ataques más. Los ataques se ordenan por **daño en hordas**: daño × enemigos que alcanza de media cada tipo de ataque (ráfaga, cono, cadena, rebote, meteoro…) ÷ recarga, con su lado y el bonus de un solo tipo. Se prefieren los de distancia; una MT solo entra si rinde un 30 % más que el mejor natural.
- **Hueco 2, Ataque Rápido** (lo aprenden los 966): cada embestida deja 0,3 s invulnerable y la recarga es de 0,75 s; con los 10 Reflejos (×0,434) y la Garra Rápida (−20 %) baja a 0,26 s, invulnerable sin pausa frente a las hordas y los legendarios. No protege del toque de Arceus ni de sus pilares, rayos y onda (ponen la invulnerabilidad a cero).
- **Huecos 3 y 4**: frenazo a distancia, aturdimiento y Acua Aro si los tiene. Solo afectan a los legendarios que acuden (Arceus se mueve con su propia fórmula), y con los cuatro huecos llenos dejan de salir ataques nuevos en las cartas.

Además: movimiento inicial (el principal), segundo inicial para Repertorio (otro ataque del grupo), hasta tres vetos (Placaje, Golpe Cuerpo, Giro Rápido…; ya no Ataque Rápido), la condición de evolución de cada ataque elegido, el número de cartas de Carrera hasta el tope de 130 y los objetos (Garra Rápida, Restos, Banda Focus).

Los empates se deshacen a favor del movimiento natural y, después, por nombre: el resultado es **determinista** (tres ejecuciones con semillas distintas producen el mismo fichero).

## 7. Supuestos y límites

- Mejoras permanentes al máximo del Pokémon y cartas típicas al minuto 30 (15 Vigor, 8 Carrera, 10 Reflejos). Coraza llega al tope del 80 % para todos, así que no diferencia.
- Un solo hueco activo a la vez: los ataques solo se lanzan juntos si se fusionan con un vínculo de grieta. Por eso la build agrupa en el hueco 1 lo que farmea. Con el grupo completo no conviene entrar en más grietas: cada fusión libera un hueco y las cartas vuelven a ofrecer ataques nuevos en vez de mejoras (`LevelUp.candidates` solo ofrece ataques nuevos con huecos libres).
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

**Desde el 28-10-2026 el objetivo es la fuerza ajustada por jugador** (apartado 11); lo que sigue describe la versión del 25-10, que se mantiene como reserva si no hay fuerza en `records.json`.

1. **Predicción** para los 966: regresión ridge sobre ataque, log del radio, ranking en hordas, vida, velocidad, BST, legendario, **lado especial** (si es especial y log At. Esp./Ataque, desde el 27-10-2026) y los seis componentes T, U, A, D, S, Z. Objetivo: log de la mediana real. Se ajusta con los Pokémon con ≥10 marcas en Sentencia; alpha por validación cruzada (5 particiones × 6 repeticiones). Acierta el orden fuera de muestra con Spearman ≈ 0,39 (≈ 0,29 sin el lado especial); la puntuación antigua sola, ≈ 0,09. En los récords los especiales aguantan una mediana de 118 s frente a 88 s de los físicos y llegan con más nivel (229 frente a 215); no es por las defensas de los enemigos (como mucho un 1 % a favor del especial), sino porque los ataques especiales son de distancia y en área (ráfagas, auras, rayos, rebotes) y los físicos, sobre todo cuerpo a cuerpo.
2. **Mezcla** en escala log: `est = (nj·real + K·pred) / (nj + K)` con K = 10 (con 10 partidas reales, mitad y mitad).
3. **Tienda Kecleon**: `est_tienda = est · exp(pred(componentes de tienda) − pred(componentes por defecto))`.
4. Puestos y tiers por `est`; los puestos de la puntuación antigua quedan en `model_pos`. La ficha enseña los segundos y de dónde salen.

Sesgo conocido: los récords son el top 50 de cada Pokémon; los raros los juegan sobre todo veteranos con más mejoras. La estimación es "en buenas manos". El puesto personal de "Mi partida" sigue usando la puntuación de componentes con tu habilidad y naturaleza.

## 11. Fuerza ajustada por jugador (desde el 28-10-2026)

Problema de la versión anterior: la mediana del top 50 mezcla lo bueno que es el Pokémon con lo bueno que es quien lo juega (los raros los juegan veteranos), y solo contaba las partidas que llegan a la Sentencia, así que los Pokémon sin marcas en la Sentencia quedaban a merced de la predicción.

1. **Datos**: el 28-10-2026 se releyeron una vez los top 50 en solitario de los 966 (2,5 s entre lecturas). De cada marca se guarda solo tiempo total, nivel, enemigos y una huella anónima del jugador (SHA-256 recortado con sal local) que **nunca sale del PC**; al repo solo llegan agregados (`data/records/records.json`: n, nj, mediana, p75, p90, nivel, enemigos/min, nº de jugadores y fuerza). Limpieza: fuera marcas de más de 20 min de Sentencia (imposibles con las reglas actuales), de nivel ≤ 1 o sin enemigos. Quedan 23.931 marcas de 18.602 jugadores; 3.143 jugadores tienen marcas con más de un Pokémon, y son los que permiten separar Pokémon y jugador.
2. **Modelo**: `log(segundos totales) = media + fuerza(Pokémon) + habilidad(jugador) + ruido`, ajustado alternando medias encogidas (λ = 3 marcas para ambos). Cuenta también las partidas que no llegan al minuto 30.
3. **Fiabilidad**: con dos mitades al azar de las marcas, la fuerza de los Pokémon con ≥ 10 marcas coincide con Spearman 0,90. La habilidad del jugador varía poco frente a la fuerza (desviación 0,11 frente a 0,46 en log), y la fuerza ajustada sigue a la mediana cruda (0,98): el sesgo de veteranos existe pero es pequeño. Los iniciales salen por debajo de la media, así que la popularidad no infla.
4. **Predicción** de la fuerza para los 966 con la misma ridge (variables del apartado 10 más log de enemigos/min del banco de partidas del bot), ajustada con los Pokémon con ≥ 5 marcas: CV Spearman **0,60** (0,41 con el objetivo anterior).
5. **Mezcla** (revisada el 28-10-2026 por la noche): `fuerza = (n·real' + K·pred) / (n + K)`, con n = marcas totales, `real' = real·(n + 3)/n` (se deshace el encogimiento del paso 2, que si no se aplicaba dos veces) y `K = σ²/τ² ≈ 1,9`: σ = 0,43 es el ruido de una marca en log (con mitades al azar de las marcas sale lo mismo) y τ = 0,31 el error de la predicción fuera de muestra, descontado el ruido de la fuerza real con que se compara. Antes era K = 8 a ojo sobre la fuerza encogida; prediciendo una mitad de las marcas con la otra (el 20 % frente al 80 %), el error cuadrático baja de 0,053 a 0,026 y el Spearman sube de 0,88 a 0,91. Frente a la mediana real de Sentencia de los Pokémon con ≥ 45 marcas (≥ 30 en la Sentencia), el error medio de los segundos baja de 59 s a 31 s.
6. **Segundos**: la fuerza se pasa a segundos totales **emparejando cuantiles** con las medianas reales del tiempo total de los Pokémon con ≥ 10 marcas (el puesto en fuerza recibe la mediana de ese mismo puesto; fuera del rango, pendiente 1 en log). Una recta única encogía hacia el centro y dejaba por debajo del minuto 30 a Pokémon cuyas 50 marcas lo pasan. Se muestra `total − 1800` como segundos de Sentencia y, si no llega al minuto 30, "hasta el min X". Es la estimación para un jugador medio del top 50: si los que juegan un Pokémon son mejores que la media, sale por debajo de su mediana cruda.
7. **Tienda Kecleon**: la ridge entre Pokémon da a los componentes signos poco fiables (están mezclados con las estadísticas), así que la combinación de tienda se elige por la puntuación de mecánicas y su ganancia se pasa a fuerza con la **pendiente parcial** de la puntuación con las estadísticas fijas (≈ 0,09; la pendiente sin fijarlas, ≈ 0,9, confunde "puntúa alto" con "es un Pokémon fuerte").
8. **Margen**: el error típico de la fuerza mezclada es `1/√(n/σ² + 1/τ²)`; la ficha enseña el intervalo del 80 % (±1,28 errores) pasado a segundos de Sentencia. Es grande arriba porque los segundos de Sentencia son la cola de un total de ~40 min: un ±7 % del total son ±200 s. Dice cuánto se sabe de la mediana de un buen jugador, no lo que dura cada partida.

El análisis de las marcas está en `../_ext/analisis-records.py` (fuera del repo por las huellas). No se vuelven a leer las tablas sin motivo (cuota gratuita del juego).
