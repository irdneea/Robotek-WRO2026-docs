# Plan: poner los docs del Open y del Obstacle al día con el coche del 8 nov 2026

Revisión de los docs uno por uno, el 8 nov 2026, por la noche. Abarca dos repositorios:
- robotek-learn: los README de los paquetes;
- Portfolio-Astro: la guía `example.com/learn`, en `src/content/learn/`.

Para cada doc se indica qué está desactualizado y qué poner. Todavía no se ha cambiado nada.

## Cómo funciona hoy el coche (la referencia)

| Tema | Hoy | Lo que dicen los docs viejos |
|---|---|---|
| Motor | 310 (JGA27-310R 20:1) en **M2**, **sin tipo** (`motor_type: -1`), `rrc_motor_port: 2`, `rrc_motor_sign: -1` | M1, tipo 2, signo +1 |
| Engranajes | 54:30 (el grande en el motor), `motor_rps_per_mps` 4,4, máx. ~0,77 m/s; opción 30:54: 13 rps por m/s, 3,24× la fuerza | 1:2, 4,8 rps por m/s, ~0,72 m/s |
| Parada | un 0 normal (desliza 8–35 cm); `brake_reset` y `brake_rps` apagados | parar reiniciando la placa |
| Velocidad baja | la placa sigue desde ~0,02 m/s; con todo el giro, desde parado, no arranca por debajo de ~1 rps. Opciones del adaptador: `motor_min_rps`, `motor_kick_*`, `motor_pulse_*` (apagadas) | «a menos de 2 rps no arranca»; 2,5 rps = 0,45 m/s |
| Freno de pared | **apagado** (`wall_stop_m: 0`) | activo a 0,30 / 0,10 m |
| Cámara | IMX708 Wide por el flex (`camera_driver:=picam`); la USB es la alternativa | cámara USB icSpring |
| Open | v5, `motor_max_rps:=6.7`, 3 rondas perfectas (26,7–28,5 s, ~0,87 m/s) | `motor_max_rps:=2.5`, ~32 s |
| Obstacle | v3, `motor_max_rps:=4`, `obstacle_v3_car_picam.yaml` (giro 17,5°); DONE 118,7 y ~138 s | 3,4 rps; sin aparcamiento en el coche |
| Sin botón | `start_delay` por defecto 12 s; el Obstacle tarda 13–17 s en estar listo → `start_delay:=20` | 12 s |
| Aparcamiento | por archivo de parámetros (`parking: true`, `lot_laps: 0`); el planificado no funciona en el coche; `park_mode: 1` a prueba | «no aparca en el coche» |
| Dirección | ±19° en `robot.yaml` (`wheel_limit_deg`); fallo intermitente: todo el giro y no gira | 17,6° como límite del adaptador |

## robotek-learn

1. **`README.md`** (raíz):
   - L224: «el de `robot.yaml` es 7 rps» → 3,4.
   - L109 y L209: «arranca a los 12 s» → añadir que para el Obstacle hace falta `start_delay:=20`.
   - El resto (Open v5 a 6,7 rps, motor en M2, Obstacle en el coche) ya está al día.
2. **`src/robotek_hardware/README.md`:**
   - L85 y L200: «la dirección se limita a 17,6°» → el adaptador limita a `wheel_limit_deg` (19°). Los 17,6° (Open) y 17,5° (Obstacle en el coche) los pone la estrategia.
   - Añadir el fallo intermitente de la dirección y que la placa se reinicia cuando el coche se queda atascado empujando.
   - Repasar «Quiero que el coche haga la ronda ya» y «Primera vez» con M2 y sin tipo.
3. **`src/robotek_obstacle_v3/README.md`:** al día desde `df759eb`.
   - Cuando termine la sesión del aparcamiento fijo, actualizar «Aparcamiento fijo» con su prueba en el coche.
4. **`src/robotek_obstacle_v3/RESULTADOS.md`** (3 nov, simulación): no está mal, pero es anterior a `real_v3`.
   - Añadir una línea al principio: resultados de Gazebo y del lab del 3 nov; los del coche real están en el README.
5. **`tools/pi-monitor/README.md`:** nada del motor; al día.
6. **Código** (no es doc, pero lo arrastran todos los docs):
   - Subir el `start_delay` por defecto de `car.launch.py` a 20 s, o hacer que el auto-start espere a que la estrategia publique su estado.
   - Así ningún doc tendría que avisarlo. Se decide aparte.

## Guía del Open (Portfolio-Astro, `steps/open-strategy/`)

Es la que más ha envejecido: casi todo lo del coche real es del 1–4 nov (tipo 2, M1, reinicio para frenar).

7. **`armar-y-conectar-el-coche.md`:**
   - L30 y tabla: «Cámara USB (icSpring)» → la IMX708 Wide por el flex (la USB como alternativa). Revisar el paso 10 del montaje (soporte) y el cableado (L124, `wiring-usb.svg`): la cámara ya no va por USB.
   - L32, L126, L136, L152 y L161: M1, `rrc_motor_port: 1`, tipo 2, `rrc_motor_sign: 1.0` → M2, sin tipo, `rrc_motor_sign: -1`. Revisar `wiring-motor.svg` (dibuja M1).
   - L32: «reductora 1:90» → JGA27-310R 20:1, 450 rpm, con engranajes 54:30.
   - L152: «a menos de ~2 rps no arranca» → con la placa sin tipo sí arranca. Con todo el giro hace falta ~1 rps.
8. **`coche-del-equipo-v5.md`:**
   - L19–26, el bloque de estado: tipo 2, «arreglo provisional: parar reiniciando la placa» y «revisar el encoder y M1» → resuelto el 8 nov (sin tipo, M2), con las tres rondas perfectas.
   - Tabla L45, fila 4 «Motor: tipo 2…» → «sin tipo, M2, signo −1, 4,4 rps por m/s».
   - Sección 4 (L476–509) **reescribirla**:
     - qué pasaba con el tipo 2: firmware con PID negativo y el encoder al revés;
     - la tabla medida de 0,1–1,0 rps;
     - los engranajes 54:30 y 30:54;
     - `motor_max_rps:=6.7` en lugar de 2,5;
     - la parada con un 0.
   - Dejar la historia en una línea con enlace a WRO-Strategies `docs/robot-real-pi/obstacle-runs/20261108/`.
   - L419: «`robot.yaml` ya tiene ±19°…»: sigue siendo cierto. Añadir que el Obstacle usa 17,5° en el coche.
9. **`paso-10-el-coche-real.md`:**
   - L52: cámara USB → IMX708 (y la USB como alternativa). Revisar la sección 3 de la cámara (L178, `camera_publisher`, 5–15 fps) para la picam.
   - L53, L67, L328 y L339–348: M1, tipo 2, 2,5 rps y 4,8 rps por m/s → M2, sin tipo, 4,4. La prueba de 3.6 con +rps hacia delante sigue valiendo con el signo nuevo.
   - L86: el freno de pared → apagado por defecto. Explicar por qué (el Obstacle) y cómo encenderlo (`wall_stop_m: 0.10`).
   - L358: `motor_max_rps:=2.5` → empezar a 2,5 para la primera ronda está bien, pero el equipo corre a 6,7: decirlo.
   - L381: la segunda pulsación «reiniciando la placa» → un 0 normal.
10. **`paso-11-solucion-de-problemas.md`:**
    - Las tablas de casos del 4 nov (L69–96) son historia: se quedan. Añadir una tabla del **8 nov**:
      - el motor no paraba / iba al revés → el tipo 2 (arreglado);
      - a poca velocidad con todo el giro no arranca → `motor_min_rps` o 30:54;
      - todo el giro y no gira (intermitente, sin resolver);
      - el auto-start antes de que la estrategia esté lista → WAIT_START.
    - Caso 8 (L465, L485): la velocidad con el tipo 2 → la tabla nueva.
    - Caso 12: añadir el reinicio de la placa al quedar atascado.
11. **`paso-12-afinar.md`:** consejos de simulación; L133–135 (±19°) siguen bien. Sin cambios, salvo quizá la velocidad real máxima (~0,77 m/s con 54:30) en L503.
12. **`paso-0` a `paso-9`** (simulación) y **`guides/open-strategy.md`:** no hablan del coche real; nada que cambiar.

## Guía del Obstacle (Portfolio-Astro, `steps/obstacle-strategy/`)

13. **`paso-10-el-v3.md`** (sección «En el coche real», de `351319c`):
    - L124: `motor_max_rps:=3.4` → 4.
    - L128: «con `button:=false` arranca a los 12 s» → `start_delay:=20`, y por qué.
    - L145: «la velocidad mínima ya no hace falta» → matizar: con todo el giro desde parado sí.
    - Añadir:
      - dónde colocar el coche (~1,55–1,60 m de la pared, centrado);
      - el giro a 17,5°;
      - la imagen a 5 Hz;
      - la segunda ronda (~138 s);
      - un párrafo del aparcamiento en el coche: las vueltas salen, el planificado no tiene fuerza ni precisión, y el fijo (`park_mode: 1`) está a prueba.
14. **`paso-8-aparcar.md`:** describe el aparcamiento planificado (A*, arcos de 3 cm a poca velocidad).
    - Añadir al final una nota «En el coche real»: el plan necesita 0,06 m/s y el coche no los da con todo el giro. Enlazar el aparcamiento fijo cuando esté probado.
    - El código del paso no cambia.
15. **`paso-3-ver-las-senales.md`** (IMX708, L46): al día.
16. **`paso-0-preparar.md`** y **`paso-9-medir-y-limites.md`:** solo enlazan; al día. Comprobar que el enlace del paso 0 al montaje del Open lleve al montaje ya corregido (punto 7).
17. **`guides/obstacle-strategy.md`:** sin datos del coche; nada.

## Orden propuesto

1. Guía del Open, puntos 7–10: es lo que lee el equipo para montar y lanzar, y hoy los manda a M1 y al tipo 2, la configuración que rompía el motor. Es lo urgente.
2. robotek-learn, puntos 1–2, y el `start_delay` (punto 6, si se decide cambiar el código).
3. Guía del Obstacle, puntos 13–14.
4. Cuando la sesión del aparcamiento fijo tenga su prueba en el coche: los puntos 3, 13 y 14 con su resultado.
5. Commit en cada repo y push al terminar.

Imágenes que hay que revisar a mano: `public/learn/assembly/wiring-motor.svg` (M1) y `wiring-usb.svg` (la cámara por USB).

## Fuera de alcance

- WRO-Strategies `docs/open-estado.md` y `docs/obstacle-estado.md`: son las páginas de estado de la simulación. Las mantiene cada sesión del lab.
