# Máquina remota para las pruebas pesadas

Decisión del usuario (26 oct 2026): las rondas de Gazebo **sin GUI**, el lab de Obstacle y el de Open,
y los lotes (`tools/obstacle_suite_quiet.sh`, `tools/open_suite_quiet.sh`, el set estándar) se corren en
la máquina remota, no en el Mac. Las rondas **con GUI** (validación de candidatos finales) siguen en el Mac.

| | |
|---|---|
| Dirección | `REMOTE_HOST` (Tailscale SSH, usuario `user`) |
| Sistema | Windows con WSL2, Ubuntu 24.04, 24 núcleos, 15 GB de RAM |
| ROS y Gazebo | ROS 2 Jazzy de apt en `/opt/ros/jazzy`, gz 8.15 (Harmonic) |
| Repo | `~/Projects/WRO-Strategies` (clon de GitHub; la copia antigua `~/Projects/Robotek` no se tocó) |
| Shell | zsh: los comandos van con `bash -lc` y `source /opt/ros/jazzy/setup.bash` |

## Cómo se usa

`tools/remote.sh` hace todo desde el Mac:

```bash
tools/remote.sh sync                                           # copia src, tools y docs (sin rondas) y compila
tools/remote.sh run python3 tools/obstacle_lab_suite.py --seeds 0-4
tools/remote.sh run tools/obstacle_suite_quiet.sh <tag>        # lote de Gazebo sin GUI
tools/remote.sh fetch                                          # trae las rondas nuevas y sus líneas del registro
```

- `sync` copia el árbol de trabajo del Mac, **con los cambios sin commitear**, así que no hace falta hacer
  push para probar un cambio. `src` y `tools` quedan idénticos a los del Mac.
- `fetch` trae las carpetas de rondas nuevas (con la telemetría, que queda solo en local como siempre) y
  añade al `rounds.jsonl` del Mac las líneas nuevas del remoto, marcadas con `host`. `sync` pone en el
  remoto el registro del Mac: haz `fetch` antes de volver a correr rondas en el Mac o de otro `sync`.
- Los lotes largos conviene lanzarlos en segundo plano. Si se corta el SSH se corta el lote.

## Rondas de Gazebo en paralelo

`tools/obstacle_gazebo_batch.py` corre rondas sin GUI de Obstacle en paralelo. Cada trabajo tiene su
propio `ROS_DOMAIN_ID` y `GZ_PARTITION`, y la puerta de calidad y la velocidad real se miden por ronda.

```bash
tools/remote.sh run python3 tools/obstacle_gazebo_batch.py <tag> --jobs 2 --rtf 1 --gpu
```

- **2 trabajos a la vez, a 1x, con `--gpu`.** Con 2 los resultados son idénticos a una sola ronda.
- Con 4 aparecen rondas que no pasan la puerta de calidad y márgenes peores.
- El límite es la CPU, no la GPU (medido el 26 oct 2026, tabla en
  [obstacle-v2-next-steps.md](obstacle-v2-next-steps.md)).
- La máxima velocidad (`--rtf 0`) llega a ~1,5x y no pasa la puerta de calidad.

## CPU o GPU

- **Lab:** solo CPU, en paralelo (`--workers`, por defecto núcleos − 2). Es Python sin imágenes: la GPU no
  aporta. 100 rondas tardan ~50 s.
- **Gazebo:** `--gpu` para el render (cámara), pero el límite es la CPU: 2 rondas a la vez.
- No correr el lab durante un lote de Gazebo: le quita CPU y rompe la puerta de calidad.

## Leer resultados sin gastar contexto

- `python3 tools/round_digest.py <ronda> [...]`: 4–5 líneas por ronda.
  - Incluye puntos, validez, vueltas, márgenes, problemas, estados y el error de pose contra la verdad.
  - `--at fault` (o `--at <s>`) añade una tabla corta alrededor del primer fallo.
  - Leer `round.json` cuesta ~4k tokens; la telemetría o `planner.jsonl`, ~100k.
- `tools/obstacle_lab_suite.py --brief`:
  - con `--against`, solo las rondas que cambian;
  - sin `--against`, solo las inválidas.
- El runner de Obstacle termina con una línea JSON corta; el informe completo sigue en `round.json`.
- `tools/obstacle_gazebo_batch.py` muestra de cada error solo su última línea.

## Verificación (26 oct 2026)

- Lab de Obstacle, set estándar (campos 0–4 en los dos sentidos, semilla 0): **mismos puntos, tiempos y
  márgenes que en el Mac** (7/10 válidas, 108,7 s de media). Tarda 14 s con 22 procesos.
- Ronda de Gazebo sin GUI `remote-smoke-reg0-ccw` (campo 0, antihorario, `real_car`, ganancia 20,
  `--real-time-factor 0`): 40 puntos estimados, 81,8 s de Gazebo en 51 s de reloj de pared, sin señales
  movidas. Está en `docs/obstacle-challenge-runs/20261026-111733-remote-smoke-reg0-ccw/`.
- Los lotes `*_suite_quiet.sh` leen la carga con `/proc/loadavg` en Linux y con `sysctl` en macOS.
