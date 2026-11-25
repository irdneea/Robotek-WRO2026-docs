# Open lab: rondas del Open en 2 segundos, sin Gazebo

Código: [`open_lab.py`](../src/robotek_evaluation/robotek_evaluation/open_lab.py), pruebas:
[`test_open_lab.py`](../src/robotek_evaluation/test/test_open_lab.py). Es el paso 1 de
[open-reimpl-v5.md](open-reimpl-v5.md): un simulador de lazo cerrado para comparar estrategias Open rápido.

```bash
source tools/macos_env.sh
export PYTHONPATH=$(ls -d src/*/ | tr '\n' ':')
python3 -m robotek_evaluation.open_lab                          # set estándar de 12 rondas, ~25 s
python3 -m robotek_evaluation.open_lab --field square100 --direction ccw --param inner_gap=0.20
python3 -m robotek_evaluation.open_lab --car real_v2 --param inner_gap=0.35   # el coche real del 4 nov, square100 CCW y CW
```

Perfiles del coche (`--car real_v1`, el de Gazebo y por defecto, o `real_v2`, el coche real del 4 nov): ver
[open-estado.md](open-estado.md), «Perfiles del coche en el lab».

## Qué modela

| Pieza | Cómo | Se comprobó contra Gazebo |
|---|---|---|
| Campo | las cajas de pared del SDF real; rayos y choques contra ellas | los escaneos grabados de una ronda: diferencia de rango de ±1,4 cm (el ruido del sensor) y 4,3 % de rayos vacíos |
| LiDAR LD19 | 10 Hz, 306 rayos a ±110°, ruido de 8 mm, 4,3 % de pérdidas, cada escaneo entregado 3 veces como en Gazebo | igual que arriba |
| Giroscopio | 50 Hz, sesgo 0,006 rad/s, ruido 0,0019 | contra el giro real: escala 1,002, retraso ≤ 0,02 s, sin deriva |
| Actuadores | `Actuators`: copia de `SimActuatorModel` con `real_car_v1.yaml` y el servo medido (ver abajo) | escalones de dirección en Gazebo: error rms 0,008 rad en el ángulo de la rueda |
| Cinemática | **eje trasero** (bicicleta): `base_link` se desliza de lado `atan(0,0587·ω/v)` | en Gazebo 0,142 rad con la dirección al tope, esperado 0,141 |
| Estrategia | el v5 (`V5Strategy`, la misión de `robotek_open.v5`); el v4 se borró el 26 oct 2026 | — |
| Distancia | la `LidarOdometry` real, con su respaldo por modelo | — |
| Cámara | conoce el sentido a los 0,3 s del Start (Gazebo: antes de 0,44 s) | — |
| Juez | el `judge_open` y `standard_validation` de las rondas de Gazebo, sobre la trayectoria del laboratorio | mismo código |

### Servo de Gazebo (medido con escalones)

Para identificar la dirección se lanzó Gazebo sin estrategia en un campo vacío y se mandaron escalones de dirección a 50 Hz
(`tools/open_lab/`). El ángulo medido de las ruedas sigue la orden del modelo de actuadores con **0,10 s de retardo**
(el 0,06 s del modelo más el del plugin), **1,2 rad/s** de velocidad máxima y un filtro de **0,06 s**
(error rms 0,0076 rad; con los valores anteriores, 0,0235). El giro del cuerpo sigue al ángulo medido de la rueda **sin retardo**:
`v·tan(δ)/0,1174` (error rms 0,03 rad/s).

## Resultado

Set estándar con el v4: **12/12 válidas, 30 puntos, margen «cómodo»**. Contra `refac3-a` de Gazebo, el laboratorio
tarda **−0,65 s de media** (entre −0,92 y −0,32 s). Una ronda tarda ~2 s (Gazebo: ~1 min).
Los márgenes de las configuraciones que **pasan** en Gazebo coinciden a ±2 cm (distancia mínima del contorno a la pared,
`square100` CCW):

| Configuración | Gazebo | Laboratorio |
|---|---|---|
| v4 | 0,148 m | 0,144 m |
| `margin0` | 0,142 m | 0,141 m |
| `latency0` | 0,198 m | 0,202 m |
| `kd0` | 0,160 m | 0,140 m |
| `brake0` | 0,125 m | 0,144 m |

## Límite importante: no reproduce lo que rompe a Gazebo

Con `turn_rate_damping=0`, `turn_exit_angle=0`, `corner_lookahead=0` o `corner_endpoint_confirmations=1` Gazebo
falla las rondas (9–24 puntos, un contacto con la isla), y el laboratorio las **sigue pasando**. Lo que se descartó:

- **No es el modelo de la dirección ni el retardo de la orden** (se barrieron retardos de 0,06–0,30 s, velocidades de 0,85–1,2 rad/s y hasta 0,1 s de latencia).
- **No es el sensor**: el LiDAR y el giroscopio coinciden con los de Gazebo.
- **No es una sobrecarga de la máquina**: en todas esas rondas los atascos del lazo de control aparecen *después* del primer contacto, no antes (el choque hace más lenta la simulación).
- **Sí se vio** que en las rondas que fallan el arco termina con el coche aún girando a 1,5 rad/s (en el v4 termina a 0,3–0,6 rad/s) y que la rueda tarda más de 0,5 s en deshacer el giro. Falta explicar por qué en esas rondas el arco no llega al final con el giro ya recogido; son diferencias de pocos centímetros y décimas de segundo.

**Cómo usarlo:**

- Una ronda **válida en el laboratorio no demuestra nada**: Gazebo es más exigente y la diferencia está sin explicar.
- Una ronda **que falla en el laboratorio** sí es una mala señal para el diseño.
- Sirve para iterar rápido (rangos de parámetros, regresiones, trayectorias y márgenes), y todo candidato se confirma con el set estándar de Gazebo.

## Hallazgos de paso

1. **La cinemática era la de un monociclo en `base_link`**; Gazebo gira sobre el eje trasero. Con la dirección al tope el
   punto medio del coche se desliza 0,14 rad de lado. Corregirlo cambió la distancia a la isla en 2 cm y los tiempos en 1,3 s.
2. **El registro de contactos tiene su `sim_time` ~1 s adelantado** respecto al sello del mensaje (`stamp`) y a la trayectoria:
   el contacto de `endpoint0` figura en 30,48 s y la pared se toca en 31,36 s en la pose grabada.
3. **`sim_actuator_model` usa `wheelbase=0.13`** por defecto y `real_car_v1.yaml` no lo cambia: el modelo del simulador
   no sigue la distancia entre ejes medida (0,1174 m). Cambiarlo mueve todas las referencias de Gazebo: no se tocó.
4. **El juez usa un contorno viejo del coche** (chasis de 0,177 × 0,09 m, de antes de las medidas del 21 oct); el coche
   mide 0,233 × 0,148 m. El laboratorio calcula sus choques con el contorno nuevo.
5. **El `/scan` llega 3 veces por cada sello de tiempo** en las rondas de Gazebo (30 mensajes/s para un sensor de 10 Hz).
6. **Los contactos de las rondas de ablación son del `lidar_nose_col`** (la caja del LiDAR) contra la isla, con 0,4 mm de profundidad.
7. **El oráculo `golden_open.py` no sirve como simulador** (no tiene choques ni actuadores): `ccw_lane60` y `cw_lane60`
   graban un coche que sale del campo.
