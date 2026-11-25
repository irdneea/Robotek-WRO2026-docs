# Simulación del coche real (`real_car:=true`, perfil `real_car_v1`)

8 de octubre de 2026. Perfil de simulación con los actuadores y sensores medidos
en el coche ([robot-real-pi.md](robot-real-pi.md), datos en
[robot-real-pi/actuator-runs/](robot-real-pi/actuator-runs/)). **Desde el 9 de octubre es el
valor por defecto** de los launches de Open y Obstacle, y los runners escriben
`real_car:=true` en cada ronda. Primeras rondas sin pasar el argumento: Open square100 CW
válida (30 puntos estimados, 32,8 s) y Obstacle semilla 0 CCW válida (40 puntos
estimados, 82,9 s), en la Mac a ×2. Con `real_car:=false` la simulación es exactamente la
de antes: el modelo de actuadores da la misma salida (20 secuencias aleatorias × 3000
ciclos, diferencia 0) y el URDF es idéntico.

```bash
# Open u Obstacle con el coche real (por defecto; implica el modelo de actuadores; siempre honesto)
bash src/robotek_evaluation/tools/run_gui_experiment.sh ... --launch-arg real_car:=true
bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh ... --launch-arg real_car:=true
```

Con `real_car:=true` no se usan `steer_delay`, `steer_rate`, `steer_tau`, `accel_max` ni
los ajustes de respuesta del servo del modelo: manda
`robotek_evaluation/config/real_car_v1.yaml`. Comparar rondas **solo dentro del mismo perfil**. Usar
`--ackermann-steer-p-gain 20` (Open) o `--steer-p-gain 20` (Obstacle): esta ganancia
sí controla cómo el plugin sigue el ángulo del modelo. Con ganancia 1 se añade
una respuesta lenta que no corresponde al servo calibrado.

## Qué se modela

| Parte | Coche real (medido) | Simulación hasta ahora (`actuator_model:=true`) | `real_car_v1` |
|---|---|---|---|
| Servo: retardo | 52–79 ms orden → reacción del chasis | 0,03 s | `steer_delay` 0,06 s |
| Servo: velocidad | 10° en ~0,10–0,15 s, 25° en ~0,33–0,48 s (cotas) | 4,4 rad/s, τ 0,03 | `steer_rate` 1,2 rad/s (~70°/s), `steer_tau` 0,05 |
| Ángulo de las ruedas | **círculos con las ruedas fijas**: +10° → 8,7°, +25° → ~19,7°, −10° → −8,6°, −25° → ~−17,6° (a fondo gira ~2° más a la izquierda). En el coche `base_adapter` invierte esa tabla por lado y limita a **17,6° simétricos** | igual al pedido, hasta 25° | coche compensado: la rueda hace lo pedido hasta 17,6° (`steer_limit` 0,307 del modelo); las estrategias reciben `steer_limit` 17,6° (`vehicle.REAL_STEER_LIMIT`). El modelo admite la tabla cruda por lado (`steer_table_*`) si se quiere simular sin compensar |
| Arranque / frenada | `base_adapter`: 1,0 / 0,6 m/s² (sin ellos se levanta el morro y derrapa) | 2,0 / 2,0 m/s² | `accel_max` 1,0, `decel_max` 0,6 |
| Motor: retardo y respuesta | 30–80 ms hasta la primera aceleración; ~0,15 s hasta la velocidad | instantáneo | `drive_delay` 0,06 s, `drive_tau` 0,15 s |
| Velocidad real vs pedida | 0,15→0,18; 0,30→0,27; 0,40→0,30; 0,60→0,42 m/s (batería baja); **100 % inferido ≈ 0,60 m/s** | igual a la pedida | tabla `speed_table_cmd`/`speed_table_real` (lineal a tramos) con el punto inferido 1,28 → 0,60; comando limitado a ±1,28 después de la rampa, como el límite de 100 % PWM de `base_adapter` |
| IMU | 49,7 Hz; giroscopio z σ 0,0019 rad/s, sesgo +0,006 rad/s | 100 Hz; σ 0,003, sesgo 0,002 | 50 Hz, σ 0,0019, sesgo 0,006 |
| Cámara | ~6 fps (640×480); columna → ángulo del LiDAR con focal efectiva 486 px (~67°), **girada 4,4° a la izquierda** del LiDAR, inclinada ~10°, a ~8,3 cm | 30 fps, 60°, sin giro, 23° (0,4 rad), 9,5 cm | 6 fps, 1,164 rad, yaw 0,077 rad, pitch 0,17 rad, 8,3 cm; la estrategia Obstacle recibe `camera_hfov`/`camera_pitch`/`camera_yaw` reales |
| LiDAR | LD19 10,1 Hz; ve **±110°**: detrás los rayos dan en el propio coche (2–8 cm); ruido por rayo σ 5 mm mediana (19 mm p90: bordes, superficies oscuras); **~4,3 % de rayos vacíos** por vuelta, al azar | 360°, 500 muestras, σ 15 mm, sin pérdidas | ±110°, 306 muestras (misma resolución), σ 8 mm y `sim_scan_model` que vacía el 4,3 % de los rayos (Gazebo publica `/scan_gz`). En el coche `scan_adapter` descarta lo de fuera de ±110° y < 12 cm (`robot.yaml`), así ambos ven lo mismo |

Las estrategias calculan los ángulos del LiDAR con `angle_min`/`angle_increment`, así que el
campo de visión menor no rompe nada (revisado en Open, Obstacle y la odometría LiDAR).
Campo del LiDAR medido con 30 vueltas, por grado ([datos](robot-real-pi/lidar_fov.json)):
entorno hasta +109,5° y −110,5°; desde ±111° hasta 180°, 2–8 cm (chasis).

La geometría de la cámara pasa a ser parámetro de Obstacle (`camera_hfov`, `camera_pitch`,
`camera_yaw`; por defecto los de `vehicle.py` y giro 0, así la simulación normal no cambia;
`color_blocks` idéntico en 203 imágenes). Los valores reales están en `vehicle.py` (`REAL_CAMERA_*`) y los pasan
`real_car:=true`, `robot.launch.py` y el `sensors.launch.py` del Pi.

## Qué no se modela (o queda dudoso)

- **Batería:** la tabla de velocidad se midió con 7,0–7,4 V (casi descargada). Con la batería
  cargada el coche irá más rápido: re-medir (`test:=cmdvel`) y hacer `real_car_v2`.
- **Velocidades > 0,6 m/s pedidos (> 50 % de motor):** sin datos (faltó espacio). Velocidad al
  100 % **inferida** (`scipy`, 12 puntos 10–50 %): curva de saturación 0,52 m/s (intervalo 90 %
  0,39–0,60), recta 30–50 % 0,71 m/s; se usa 0,60. Con la batería baja el motor parece
  saturarse; con la batería cargada probablemente sea más.
- **Ángulo de las ruedas:** medido con círculos (radio = arco de la odometría LiDAR / giro del
  giroscopio; ángulo = atan(batalla / radio del eje trasero)); a +25° cuatro medidas entre
  18,1° y 20,3°. Una primera estimación con pulsos cortos sugería una zona muerta de 5° y era
  errónea. Puede cambiar con el desgaste o el juego de la dirección.
- **Encabritamiento, derrape y agarre:** no se simulan; en el coche los evita `base_adapter`
  (rampas). En Gazebo las ruedas no patinan como en el piso real.
- **Cámara:** colores (los rangos HSV de la simulación no sirven con la luz real) y la
  **distorsión de barril** de la lente (Gazebo usa una cámara ideal): cerca del centro la focal
  es ~590 px (tamaño del pilar verde), hacia los lados 486 px efectivos. Medido tras reajustar
  la cámara, con un pilar a cada lado ([cuadro](robot-real-pi/frames/camara_calibracion_2.png),
  [scans](robot-real-pi/camara_calibracion_2_scans.json)): con focal 486 px y giro +4,4° la
  cámara da el ángulo del LiDAR con ~0,1° de error en los dos pilares, y el detector los asocia
  en vivo (rojo 0,96 m, verde 1,07 m). La primera medida (cámara mal ajustada, pilares cerca del
  centro: ~54°, 15°) queda obsoleta. Con solo dos puntos, giro y distorsión no se separan del
  todo: confirmar con un pilar justo delante y otros en los bordes. La altura (8,3 cm) no se
  midió directamente.
- **LiDAR:** ruido y pérdidas medidos en una escena quieta de una habitación (121 vueltas);
  pueden cambiar con el material de las paredes del campo y la luz.
- **Retardos de los sensores:** del sello de tiempo a la llegada 0,5 ms (LiDAR), 0,6 ms (IMU),
  7,6 ms (cámara), pero los drivers sellan al publicar: el retardo real del sensor (exposición de
  la cámara, giro del LiDAR) no se ve así y no se modela. Frecuencias medidas: LiDAR 10,1 Hz,
  IMU 47,7 Hz, cámara 6,5 fps (las del perfil).
- **Medidas del coche** (largo, batalla, posición de sensores): siguen las del URDF.

## Validación Open

En la máquina de simulación se compiló el perfil y se inició el reajuste Open con
el máximo simétrico de ±17,6°. Los runners conservan el modo honesto y todos los
intentos, incluidos fallos. [Resultados y ajustes](open-challenge-runs/realcar-open-validation.md).
Los comandos completos están en el [README](../README.md#simular-con-las-medidas-del-coche-real).
La [mejor ronda GUI observada](open-challenge-runs/best-realcar-open-round.md)
obtuvo 30 puntos estimados en 29,312 s simulados / 29,775 s de pared, en square100 CW. Consultar el
[historial](open-challenge-runs/realcar-open-history.md) y las repeticiones:
el candidato hizo CCW en 29,811 s simulados, pasó 6/6 en square100 (cinco bajo
30 s simulados) y solo 3/12 rondas del set completo.
La auditoría del juez v2 evita perder cruces de esquina entre muestras a 10 Hz.

El perfil de motor ahora respeta el 100 % PWM: la interpolación no extrapola
velocidades por encima del punto inferido 0,60 m/s. Esta corrección solo se activa
con `drive_command_limit: 1.28` en `real_car_v1`; el modelo de servo rápido conserva
su comportamiento. La rampa precede a la saturación, como en `base_adapter`.
La banda muerta `drive_deadband: 0.005` reproduce la del adaptador real; permite
mantener control de dirección con un comando diminuto mientras el motor frena.

Queda pendiente validar Obstacle con este modelo y re-medir el motor con batería
cargada. No confundir tiempos del servo rápido con los del coche real.
