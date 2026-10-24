# Contribuir · Contributing

Gracias por el interés. Esto es un proyecto de fans mantenido en ratos libres; las contribuciones pequeñas y concretas son las que más ayudan.

## Qué se puede mejorar

- **Errores en una ficha** (un texto que no cuadra, una build que no tiene sentido, un dato mal): abre una incidencia con la plantilla *Error en una ficha* indicando el Pokémon, el idioma y qué esperabas.
- **Reglas del juego mal replicadas**: el modelo no lee las reglas del juego, las copia a mano desde su código (ver [MODELO.md](MODELO.md), apartado 2). Si una regla ha cambiado o está mal interpretada, cita el fichero y la línea del repositorio de PokéSurvivor.
- **Textos y traducciones**: los textos viven en `build/gen.py` (diccionarios `UI`, `ITEMS` y funciones `reason`, `cards_text`, `strategy`, `verdict`). Los nombres de movimientos y habilidades en inglés salen del propio juego (`data/game/js_data_lang-en.js`), no se traducen aquí.
- **Pesos y criterio**: los pesos (`W` en `build/rank.py`) son una decisión. Si propones otros, explica el porqué con casos concretos; un cambio de pesos reordena a los 966.

## Cómo proponer un cambio

1. Haz un fork y crea una rama.
2. Cambia solo lo necesario en `build/` o `data/game/`. **No edites `docs/` ni `data/ranking.json` a mano**: se generan.
3. Regenera y comprueba que no hay errores:
   ```bash
   python -I build/rank.py
   python -I build/gen.py
   python -m http.server 8000 -d docs   # y abre http://localhost:8000/es/
   ```
4. Si tu cambio reordena el ranking, incluye en la descripción del pull request los Pokémon que más se mueven (el script lo imprime al final) y por qué está bien que lo hagan.
5. Abre el pull request. Incluye los ficheros generados (`docs/` y `data/ranking.json`) para que la web se publique con el merge.

## Normas

- Python 3.12+, biblioteca estándar solamente. No añadas dependencias.
- Textos en español como idioma fuente, con su equivalente en inglés en el mismo cambio.
- Nada de datos personales ni de cuentas de jugadores en el repositorio.
- Respeta las licencias: el código del juego es PolyForm Noncommercial, los retratos CC BY-NC 4.0. Este proyecto no puede tener fines comerciales.

---

## In English

Small, concrete contributions help most. Report mistakes on a Pokémon page with the *Error en una ficha* issue template (English is fine). For misreplicated game rules, cite the file and line in the PokéSurvivor repository. Texts live in `build/gen.py`; weights in `W` inside `build/rank.py`. Never edit `docs/` or `data/ranking.json` by hand: run `python -I build/rank.py` and `python -I build/gen.py` and commit the generated files with your change. Python 3.12+, standard library only; Spanish is the source language, add the English text in the same change; no player data; non-commercial only (PolyForm Noncommercial game code, CC BY-NC 4.0 portraits).
