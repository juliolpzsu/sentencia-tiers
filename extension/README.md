# Sentencia Tiers · Consejero

Extensión de navegador para [PokéSurvivor](https://pokesurvivor.com/). En cada subida de nivel marca qué carta coger (ataque nuevo, mejora de un ataque o mejora de stat) según la build de la Sentencia de Arceus del Pokémon que juegas, la misma que enseña su ficha en [Sentencia Tiers](https://juliolpzsu.github.io/sentencia-tiers/).

![Pantalla de subida de nivel con el Consejero](../assets/readme/consejero.png)

## Qué hace

- **★ RECOMENDADA** en la mejor carta, **también vale** en las que se quedan cerca y **evitar** en las que estropean la build. Debajo de las cartas, una línea con el motivo, el tier y el puesto del Pokémon y un enlace a su ficha.
- **Ataques nuevos:** los de la build primero (frenazo y aturdimiento, después Acua Aro, ataque principal, segundo ataque y potenciadores). Uno fuera de la build solo se recomienda si te sobran huecos después de contar los que aún pide la build; si no, «evitar».
- **Mejoras de ataques:** las de la build, con el control por delante. Un punto más si con esa mejora llega al máximo y ya tienes la stat que pide su evolución.
- **Stats:** la carta dorada que desbloquea una evolución va primero, y también la stat que pida un ataque de la build aunque aún no esté al máximo. Después Reflejos, Carrera (solo hasta el tope suave de 130 que calcula la web), Coraza, Vigor y Síntesis. La Baya Zidra sube mucho con poca vida (por debajo del 40 %). Potencia y Aprendizaje valen más al principio de la partida (hordas) que al final.
- **Evoluciones:** siempre recomendadas.
- Si las tres cartas estropean la build (ataques que ocupan un hueco que pide otro), marca la menos mala y, si te quedan cambios, sugiere cambiar las cartas. Si hay una carta inofensiva (Imán, Baya Zidra…), la recomienda antes que gastar un cambio.
- Con la **Tienda Kecleon**: si ya has enseñado las MT de su build de tienda, usa esa build en vez de la base.
- **Alt + J** enciende y apaga el Consejero.

## Convivencia con PokeSurvivor Plus

Está hecha para funcionar junto a PokeSurvivor Plus, en cualquier orden de carga:

- Las dos necesitan el objeto interno del juego. Si PokeSurvivor Plus ya lo ha cogido (`window.__psmodNS`), el Consejero usa ese; si no, lo atrapa con el mismo método **encadenado** con la trampa que hubiera, sin quitársela a nadie.
- Solo envuelve `LevelUp.offer`, devolviendo la misma lista sin tocarla. No reescribe las cartas ni cambia lo que hace elegir una: añade una etiqueta dentro de cada carta (PokeSurvivor Plus les fija el alto) y una línea al final de la caja.
- Todo lo suyo lleva el prefijo `sta-` (clases, ids, `localStorage`). Atajo Alt + J, que PokeSurvivor Plus no usa.

## Datos

`data.js` es una copia de los datos de la web que se genera con `python -I build/gen.py` (ver `build/advisor.py`). Una vez al día la extensión baja `assets/advisor.json` de la web, que la Action diaria regenera cuando cambia el ranking; si la web no responde, usa la copia de serie.

## Instalar (Chrome, Edge, Brave, Opera)

1. Abre `chrome://extensions` y activa el **Modo de desarrollador**.
2. **Cargar descomprimida** y elige esta carpeta (`extension/`).
3. Recarga pokesurvivor.com.

## Privacidad

El Consejero no recoge, guarda en servidores ni envía ningún dato del jugador. Lee las cartas de subida de nivel dentro de la propia página del juego para marcarlas, y solo hace una petición de red: una vez al día descarga el fichero público `https://juliolpzsu.github.io/sentencia-tiers/assets/advisor.json` (sin cookies ni identificadores). En el `localStorage` del navegador guarda únicamente esa copia de los datos y si está encendido o apagado (claves `sta:`). No usa analítica ni publicidad.

*Privacy: the Advisor collects, stores remotely or sends no player data. It reads the level-up cards inside the game page to mark them, and its only network request is a daily download of the public `advisor.json` file above (no cookies or identifiers). It keeps only that data copy and its on/off switch in the browser's `localStorage` (`sta:` keys). No analytics, no ads.*

## Limitaciones

- Recomienda para la **Sentencia** (el criterio de la web), no para hordas: antes del minuto 30 da algo más de peso a Potencia y Aprendizaje, pero nada más.
- No conoce tu objeto, tu habilidad ni tu naturaleza; trabaja con la build general del Pokémon.
- El juego cambia casi a diario. Si deja de exponer lo que el Consejero necesita, simplemente no marca nada.

---

## In English

Browser extension for PokéSurvivor: on every level-up it marks which card to take (new move, move upgrade or stat) according to the Arceus Judgment build of the Pokémon you play, the one shown on its [Sentencia Tiers](https://juliolpzsu.github.io/sentencia-tiers/en/) page. Build moves first (slow and stun ahead), off-build moves only when there are spare slots, evolution cards always, then Reflexes, Sprint up to the speed soft cap, Armor, Vigor and Synthesis; Sitrus Berry when HP is low. Alt + J toggles it. Built to run alongside PokeSurvivor Plus in any load order: it reuses its hook into the game when present, chains its own otherwise, only wraps `LevelUp.offer` (returning the same list) and adds a tag to each card plus one line under them. Install with **Load unpacked** on `chrome://extensions` (Developer mode) pointing at this folder.
