# Actualizaciones automáticas del ranking

## 2026-11-04 · juego c121040 (2026-11-02): los datos ya se leen del bundle

- El 30-10 el juego dejó de publicar sus ficheros y pasó a un único bundle ofuscado, y la actualización diaria llevaba desde entonces sin leer nada (salía en verde). Ahora los datos se extraen de ese bundle sin ejecutarlo y, si no se puede, la Action falla.
- Comparado con los datos que había: Pokémon, ataques y sus mejoras, MT y sus precios, tipos, naturalezas, habilidades y sprites, **sin ningún cambio**. Solo cambian 108 textos en inglés del juego y aparecen 4 iconos de medallas que la web no usa.
- Según las novedades del propio juego, desde el 28-10 solo hay cambios ajenos al combate: fin de Halloween (30-10 al 2-11), banner de noticias, Discord, guardado y detección de trampas.
- Reglas: el aviso de REVISAR REGLAS sigue, ahora con una huella de cada módulo del bundle (Judgment, Combat, Enemy, Player, Stats, Hazards, Items, Upgrades). Esta es la primera huella. No cambió entre el 30-10 y el 2-11; frente al código del 24-10 no se aprecian cambios en los números de equilibrio; lo nuevo es lógica menor y el Gran Gengar de Halloween.
- Pokémon que cambian de puesto: 0.

## 2026-10-28 · mezcla de récords y predicción revisada (no es un parche del juego)

- Las marcas reales pesan más frente a la predicción (la predicción vale unas 2 marcas, no 8) y ya no se encogen dos veces. Comprobado prediciendo una mitad de las marcas con la otra: la mitad de error. Los segundos estimados se acercan a la mediana real (error medio de 59 s a 31 s).
- La ficha enseña el margen del 80 % de los segundos estimados.
- Pokémon que cambian de puesto: 950 (casi todos poco; en la parte alta, sobre todo los que tienen pocas marcas).
  - Froslass: 103 → 55
  - Gardevoir: 82 → 37
  - Tyranitar: 84 → 50
  - Koraidon: 47 → 94
  - Enamorus: 43 → 81
  - Shaymin: 54 → 91

## 2026-10-25 · nuevo método del ranking (no es un parche del juego)

- El puesto pasa a ordenarse por los segundos estimados en la Sentencia: récords reales de cada Pokémon mezclados con una predicción (acierta el orden fuera de muestra con 0.29; la puntuación anterior, 0.09). Detalle en Método.
- Pokémon que cambian de puesto: 966. Las flechas de estos días miden el cambio de método, no un cambio del juego.
  - Poliwrath: 22 → 935
  - Baxcalibur: 31 → 939
  - Gyarados: 111 → 950
  - Dunsparce: 890 → 65
  - Golisopod: 113 → 930
  - Phione: 134 → 940

## 2026-10-24 · juego a45019a (2026-10-23)

- Ficheros del juego cambiados: js_data_pokedex.js, js_data_moves.js.
- Pokémon que cambian de puesto: 0.

