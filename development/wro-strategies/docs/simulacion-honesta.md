# Simulación honesta (Open y Obstacle)

Fecha: 6 de octubre de 2026. Objetivo: que la estrategia del Open reciba en simulación
solo lo que tendría el robot real, para que un perfil que funciona aquí no dependa de
datos imposibles en la pista.

## Qué usaba el Open y el robot real no tiene

| Entrada | Uso anterior | Robot real |
|---|---|---|
| `/odom_gt` (pose de Gazebo) | distancia recorrida: rearmado de giros, tramo final, atasco | no existe |
| `/odom` (ruedas ideales) | respaldo de esa distancia | sin encoder |
| orientación absoluta de la IMU | rumbo del controlador | la placa da giroscopio; el rumbo se integra y deriva |
| `/joint_states` (ángulo de rueda) | solo telemetría | el servo no lo informa |
| LiDAR e IMU sin ruido | todo | STL-19P ±45 mm; giroscopio con ruido y sesgo |

**Todos los perfiles Open anteriores se ajustaron con la distancia de Gazebo y el rumbo
perfecto**: sus resultados no garantizan el comportamiento real.

## Cambios

- **Odometría por LiDAR** (`open_lidar_odometry.py`): alinea cada scan con el anterior
  (rotación del giroscopio, traslación por mínimos cuadrados punto-a-línea, 4 iteraciones);
  si faltan correspondencias usa la velocidad comandada × tiempo con aceleración limitada.
  La distancia siempre se obtiene por LiDAR; los selectores `odom`/`gt` fueron
  retirados al simplificar (reproducción histórica con commit `feb2f46`). Verificación offline con scans guardados: −1,7 % y +0,2 %
  de error sobre ~25 m, 99 % de los scans alineados.
- **Rumbo siempre integrado del giroscopio** (selector `yaw_source` retirado), con el sesgo que
  ya calibra el arranque, como hace el código real del equipo.
- **Modo honesto, siempre activo** (desde el 9 oct 2026 ya no existe `honest:=false`; antes `honest:=true`):
  - la estrategia ya no tiene suscripciones a `odom`, `odom_gt` ni `joint_states`;
  - ruido de sensores en el modelo (`sensor_noise`): LiDAR gaussiano σ 15 mm, giroscopio
    σ 0,003 rad/s con sesgo 0,002 rad/s;
  - `audit_pose_recorder` graba la pose real y el ángulo de rueda en `audit_pose.csv`
    solo para auditoría; el runner los une a la telemetría después de la ronda
    (`telemetry.raw.csv` conserva lo que vio la estrategia, con la pose vacía).
- El controlador activo es `open_sensors_v1` (v4 reducido); cambios y verificación.
- El servo se modela aparte con `actuator_model:=true` (servo rápido estimado).

Prueba de humo (`honest-smoke-v6-sq100-ccw`, servo lento): la telemetría propia de la
estrategia no tiene pose; 30 pts por reglas en 30,05 s, válida (margen justo).

## Resultados del reajuste (honesto, servo estimado)

| Intento | Rondas | Válidas | Notas |
|---|---|---|---|
| set estándar honesto 1 (`std12-honest-fastservo_v2-*`) | 5 (cortado) | 4 | square100 CW se trabó contra la isla |
| set estándar honesto 2 (`std12-honest2-fastservo_v2-*`) | 5 (cortado) | 0 | contactos con la isla; giros de más tras otro giro |
| diagnóstico square100 ×4 (`dbg1..4-honest-fsv2-sq100-*`) | 8 | 5 | las 3 fallas: giro extra por "muro de enfrente" a 0,33–0,40 m del giro anterior |
| corrección de código con v2 (`fix1-*`) | interrumpido | sin conclusión | sin efecto: `turn_front_heading_axis` seguía apagado |
| v4 square100 ×4 por sentido (`v4r1..4-honest-fsv4-sq100-*`) | 8 | 8 | 30 puntos estimados, 23,934–24,532 s sim desde Start; sin disparos frontales tras otro giro con `dist < 0,6 m` |
| v4 set estándar ×3 (`std12-honest-fsv4-r1..3-*`) | 36 | 35 | 30 puntos estimados en las 36; 23,638–24,828 s sim; rechazo circular en shift140 CW r2, chasis y ruedas con 1,77 cm interiores |

- Los fallos son **intermitentes**: la misma combinación pasa o falla según el ruido.
  Hace falta repetir cada combinación (≥ 3) para juzgar un perfil.
- Herramientas agregadas para esto: `turn_trigger` (condición y valores que dispararon
  cada giro) y cortes automáticos del runner (180 s simulados, 30 s sin cambiar de sección).
- Causa del fallo: v2 tiene `turn_front_heading_axis` apagado. Tras un giro el coche
  queda ~13° torcido y los rayos frontales ven el muro exterior (≈ 0,87 m), por lo
  que FOLLOW gira de más. La corrección en `open_strategy_node.py` (`on_scan`)
  extiende la medición sobre el eje de la pista a `ALIGN_EXIT`, pero necesita esa
  opción encendida. V4 = v2 + `turn_front_heading_axis: true`.
- [Tabla y evidencia de v4](open-challenge-runs/honest-fsv4-validation.md): square100
  confirmado; set estándar honesto con tres repeticiones terminado. Auditoría
  geométrica separada de los registros originales; candidato pendiente de GUI.
- Hipótesis descartada antes: confusión del muro lateral en FOLLOW (recalculado offline).

## Obstacle honesto (6 de octubre de 2026)

Mismo criterio que el Open: `obstacle_strategy` solo se suscribe a `/scan`, `/imu` y
`/camera/image`.

| Antes | Ahora |
|---|---|
| rumbo = orientación absoluta de la IMU | giroscopio integrado; sesgo de la calibración de arranque |
| posición = `/odom` (ruedas ideales) | distancia de `open_lidar_odometry` (ICP scan a scan; respaldo: velocidad comandada con aceleración limitada) proyectada sobre el rumbo del giroscopio, signo según la marcha comandada; con orden de parada se ignora (ruido del ICP) |
| arranque esperaba `/odom` | arranque con scan, imagen e IMU frescos |
| `/odom_gt`, `/joint_states` en la telemetría | columnas vacías en `telemetry.raw.csv`; `audit_pose_recorder` las graba y el runner las une después (sin pisar `x_odom/y_odom`, que son la estima propia) |
| `/obstacle/pillars_gt` en el nodo | lo graba `obstacle_audit_recorder` (`pillars-gt.jsonl`, mismo formato) |

- `obstacle_challenge.launch.py`: `sensor_noise` siempre activo (el argumento `honest` se
  quitó el 9 oct 2026).
- El planificador sigue corrigiendo su posición con la ICP contra los muros del mapa; la
  estima muerta solo predice entre correcciones.
- Telemetría nueva: `travelled` (m) y `lidar_odom_quality` (`lidar`/`model`).

### Primeras rondas honestas de `obstacle_planner_v8`

Servo del plugin p=5 (igual que la serie v8 original), sin GUI, `--real-time-factor 0`,
distribución reglamentaria. Rondas `honest-v8-*` y `honest-v8b-*`.

| Ronda | Pts est. | Tiempo sim (s) | Pilar / muro mín. (cm) | Nota |
|---|---|---|---|---|
| reg0-ccw (×2) | 40 / 40 | 70,2 / 66,7 | 5,9–5,0 / 3,1–4,6 | la primera, antes de ignorar el ICP con orden de parada |
| reg0-cw | 40 | 73,7 | 1,3 / 2,3 | |
| reg1-ccw (×3) | 20 / 20 / 40 | 180 / 180 / 62,7 | — / 0,0 | 2 incompletas: atrapado en la esquina SO antes del slalom verde (−0,5;−0,9) / rojo (0,5;−1,1), ciclos BLOCKED/RECOVER 140 s |
| reg1-cw | 40 | 67,9 | 4,6 / 3,2 | |
| reg2-ccw | 40 | 94,5 | 2,5 / 1,9 | |
| reg2-cw | 40 | 74,0 | 2,0 / 5,7 | |
| reg3-ccw | 40 | 84,7 | 3,1 / 3,3 | |
| reg3-cw | 27 | 98,5 | 0,4 / 5,3 | vuelta 3: se atasca junto al rojo (−0,5;0,9) y la reversa de recuperación cruza su radio por el lado equivocado (falta 9.24.5) |
| reg4-ccw | 40 | 71,1 | 4,8 / 2,7 | |
| reg4-cw | 40 | 80,7 | 4,2 / 0,1 | |

**Con GUI** (7 oct, a tiempo real, `gui-honest-v8-reg0-*`): ambas **válidas**, 40 pts
estimados, sin faltas ni contactos, parada validada, dirección máx. 25,0°, margen justo.

| Ronda | Tiempo sim / pared (s) | Vueltas sim (s) | Pilar / muro mín. (cm) |
|---|---|---|---|
| reg0-ccw | 73,9 / 83,6 | 24,1 · 20,5 · 27,2 | 5,4 / 4,5 |
| reg0-cw | 75,4 / 85,4 | 21,8 · 21,3 · 29,4 | 2,9 / 2,3 |

Sin GUI: **10/13 con 40 pts** (sin aparcar), frente a 16/16 en la serie no honesta (una ronda por
combinación; `p4-servo20-v8-reg1-ccw` ya había fallado igual con servo p=20).

- **La localización no es la causa:** pose del planificador vs pose real p95 ≈ 3 cm, máx.
  4,4 cm, rumbo ≤ 0,05 rad en las 13 rondas (la ICP contra los muros corrige la estima muerta;
  esta sola deriva ~0,5 m en 26 m).
- Los fallos son trampas del planificador en tramos estrechos; el ruido cambia la
  trayectoria y destapa casos que antes no aparecían. Próximo trabajo: recuperación que no
  cruce radios de pilares por el lado prohibido y salida de esquina con el slalom ya planificado.

## Pendiente

- Ruido de cámara/iluminación y deslizamiento de ruedas no modelados.
- El servo sigue siendo una estimación hasta medir el real.

### Servo rápido y perfil refactorizado (7 oct)

Semillas 0–4 × CCW/CW, honesto, `actuator_model:=true`, p=20, sin GUI:

| Serie | Código | 40 pts | Válidas | Media sim (40 pts) |
|---|---|---|---|---|
| `fs-v8-*` | v8 | 9/10 | 4/10 | 72,2 s |
| `ref-sync-*` | v8 + regla de lado al retroceder, replanificación síncrona | 6/6 | 2/6 | 67,7 s |
| `os1-*` | `obstacle_sensors_v1` (refactor, equivalente) | 10/10 | 5/10 | 72,4 s |

Sin contactos en ninguna; las no válidas pasan a < 1 cm de un muro o pilar (geometría
muestreada). Los puntos ya son estables con el servo rápido; falta margen.

Con GUI (`gui-os1-reg0-*`, servo rápido, tiempo real): ambas **válidas**, 40 pts estimados, sin
faltas ni contactos. CCW 64,3 s sim / 73,0 s pared (vueltas 22,9 · 19,3 · 19,8; margen justo);
CW 79,9 s / 90,7 s (31,1 · 24,4 · 21,2; margen de riesgo: 1,4 cm a muro).
