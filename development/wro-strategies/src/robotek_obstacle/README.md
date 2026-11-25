# robotek_obstacle

Estrategia del **Obstacle Challenge** (nodo `obstacle_strategy`, tres vueltas, sin
aparcamiento todavía): planificador con mapa, solo LiDAR, giroscopio y cámara.
Depende solo de `robotek_common`. Perfil activo `config/obstacle_sensors_v1.yaml`
(valores en `obstacle_config.py`); los históricos se borraron (9 oct 2026) y cada ronda conserva su copia.

Cómo funciona, dónde editar cada comportamiento y verificación:
[docs/obstacle-refactor.md](../../docs/obstacle-refactor.md).

Nodo `obstacle_detector`: solo la percepción de pilares (misma `color_blocks` +
`scan_clusters` + `associate`), sin manejar, para comprobarla en el coche real: marcadores y
imagen para RViz, colores HSV del coche real como parámetros y `/obstacle/steer` para la
prueba de servo. [docs/robot-real-pi.md](../../docs/robot-real-pi.md#detector-de-pilares-en-el-coche-real-obstacle_detector).
