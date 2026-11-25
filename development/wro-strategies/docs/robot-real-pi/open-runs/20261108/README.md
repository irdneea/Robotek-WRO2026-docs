# Open v5 en el coche real, 8 nov 2026: motor sin tipo, en M2, a velocidad controlada

**Configuración** (robotek-learn `c5107c6`):
- **Motor:** en M2, sin mandar el tipo; `rrc_motor_sign` −1 y 13 rps por m/s. Los engranajes son 30:54.
- **Parada:** con un 0 normal, sin reiniciar la placa.
- **Cámara y estrategia:** IMX708 con `open_v5_car_picam.yaml`.
- **Lanzamiento:** `open-debug-run.sh`, sin botón. La causa de todo el cambio de configuración está en
  [../../obstacle-runs/20261108/](../../obstacle-runs/20261108/README.md).

Los logs (`launch.log`) y eventos están en cada carpeta. La telemetría y las bolsas se quedan en el Pi y en el Mac.
No hay juez ni posición de salida medida.

| Ronda | Tope | Giros | FINISH desde Start | Vueltas | Media (odometría LiDAR) |
|---|---|---|---|---|---|
| `20261108-143756-open-debug` / `143811-open-v5` | 7,8 rps (0,60 m/s) | **12** | 53,2 s | 18,6 / 17,7 / 17,2 s | 0,38 m/s |
| `20261108-143944-open-debug` / `143959-open-v5` | 7,8 rps | **12** | 51,6 s | 17,1 / 17,8 / 16,9 s | 0,40 m/s |
| `20261108-144204-open-debug` / `144214-open-v5` | **10 rps** (~0,77 m/s; la lanzó el usuario) | 6 | — (paró con el botón a 45 s) | 16,9 s | 0,46 m/s |

Las dos primeras, según el usuario, "perfectas":
- 12 giros, FINISH y DONE;
- ningún reinicio de la placa;
- el sentido horario lo eligió la cámara.

## Ronda 3: en el giro 7 el servo recibe todo el giro y el coche no gira

- **El giro 6 fue bien:** el giroscopio marca −0,83 rad/s.
- **En el giro 7 (TURN, ~28 s):**
  - el bag muestra `/rrc/acker_servo/set_state` a **1793 µs**, todo el giro a la derecha, desde el primer momento, y
    el motor a −10 rps;
  - el **giroscopio se queda en ~0** (−0,1 a +0,1 rad/s) durante 2 s;
  - el coche sigue recto contra la pared: la izquierda baja de 0,8 a 0,2 m y luego sale inf.
- **Después:** atascado contra la pared, empujando. 7 s después del choque la placa se reinicia (hueco de 3,6 s,
  «Board data back after 3.6 s»). El reinicio es una consecuencia, no la causa.
- **Es el mismo fallo que las pruebas 19 y 27 del 4 nov:** el servo con todo el giro mandado y sin rotación.
- La placa seguía mandando el IMU, así que no estaba colgada. La causa está por confirmar: el servo (temperatura,
  alimentación o el mecanismo de la dirección) o que la placa deja de mover el PWM del servo.
- Esta ronda iba más rápida (tope de 10 rps). A 7,8 rps las dos rondas completas no lo tuvieron.

## Otros

- `open-debug-run.sh` se mataba a sí mismo: su propio `car-clean` lo tomaba por un proceso viejo. Arreglado en
  robotek-learn `44639ca`: `car-clean` ya no mata a sus llamadores.
- Antes de estas rondas, la placa dejó de responder (sin batería ni IMU por USB) hasta apagar y encender el coche.

## Engranajes 54:30 otra vez (15:03–15:25): tres rondas perfectas seguidas en ~27 s

Volvió el engranaje grande al motor (54:30) y se midió en el suelo con el adaptador. Medidas en
[../../obstacle-runs/20261108/](../../obstacle-runs/20261108/README.md):
- con el factor 4,0: 0,15 / 0,30 / 0,50 m/s pedidos → 0,16 / 0,28 / 0,45 reales;
- por eso `motor_rps_per_mps` **4,4** (robotek-learn `f9c668b`);
- con un 0 normal se desliza 8–35 cm.

Las rondas las lanzó el usuario con `open-debug-run.sh`, sin botón y con distintos topes de `motor_max_rps`:

| Ronda (debug / telemetría) | Tope | Giros | FINISH / DONE desde Start | Vueltas | Media (odometría LiDAR) |
|---|---|---|---|---|---|
| `151400` / `151410` | 2,64 rps (0,60 m/s) | 12 | 48,8 / 50,6 s | 25,4 / 11,7 / 11,7 s | 0,47 m/s |
| `151544` / `151559` | 5 rps | 0 | — | — | — |
| `151754` / `151916` | 5 rps (1,14 m/s) | **12** | **28,5 / 30,4 s** | 11,0 / 8,6 / 9,0 s | 0,86 m/s |
| `152101` / `152117` | 6,7 rps (sin recorte: el Open pide 1,28) | **12** | **26,7 / 28,7 s** | 9,6 / 8,5 / 8,9 s | 0,87 m/s |
| `152249` / `152259` | 7,8 rps (sin recorte) | **12** | **26,7 / 29,1 s** | 9,6 / 8,5 / 8,7 s | 0,89 m/s |

- **Las tres últimas, "perfectas" según el usuario:**
  - 12 giros, FINISH y DONE;
  - sentido horario elegido por la cámara;
  - ningún reinicio de la placa;
  - el giroscopio llega a 2,28 rad/s en las curvas.
  - Son tan rápidas como las mejores del 4 nov (25–28 s con el motor embalado), pero ahora con la velocidad
    controlada y parando con un 0.
- **`151544`, sentido mal:**
  - la cámara no decidió: azul ~390 px y naranja ~413 px, confianza 0,05–0,10;
  - a 1 s tomó `direction_fallback: ccw`;
  - el LiDAR lo cambió a horario al abrirse el hueco a la derecha, pero el coche no giró a la derecha: giroscopio
    +0,05–0,14 rad/s;
  - se quedó contra la pared izquierda.
  - Su bag no se pudo copiar (el coche se apagó).
  - Todas las rondas de esta pista son en sentido horario: con `direction_fallback: cw` habría ido bien.
- **`150916`** (lanzada por mí a 2,64 rps): sin giros y con 2 reinicios de la placa. Sin analizar.
- **El arranque automático del coche queda con `motor_max_rps:=6.7`.**
