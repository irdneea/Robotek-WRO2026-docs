# Next steps

## Actualización: coche real (8 de octubre de 2026)

El candidato `open_realcar_v1.yaml` corre con `real_car:=true`, sensores honestos,
servo del modelo real y límite simétrico equivalente ±17,6°. Hay una ronda GUI
square100 CW válida con **30 puntos estimados en 29,312 s simulados / 29,775 s
de pared** desde Start; el candidato actual hizo CCW en 29,811 s simulados.
El juez v2 usa auditoría a 50 Hz y corrige cruces perdidos entre muestras de
telemetría a 10 Hz. El set estándar del candidato solo pasó 3/12 rondas;
no atribuir robustez general a la mejor ronda individual. Los fallos quedan en
el registro. En square100 el candidato logró 6/6 válidas, cinco bajo 30 s
simulados; las cuatro GUI quedaron bajo 30 s simulados. Consultar
la [validación](open-challenge-runs/realcar-open-validation.md).
Consultar la [mejor ronda](open-challenge-runs/best-realcar-open-round.md),
el [historial de hallazgos](open-challenge-runs/realcar-open-history.md) y
la guía actualizada.
Motor: saturación al 100 % PWM, banda muerta y rampa como hardware;
0,60 m/s máximo inferido con batería baja. No extender el objetivo de 30 s
a todos los campos: square180 tiene una cota ideal de al menos 36 s.

## Otras salidas y geometrías: candidato v2 (8 de octubre)

Las 16 salidas graduales de v1 dieron 15 rondas válidas; y = −1,30 m CCW
falló durante detección de sentido. Usar el eje frontal para explorar resolvió
ese caso: 30 puntos estimados en 32,116 s. El perfil `open_realcar_v2.yaml`
adapta el giro al hueco interior y la llegada al LiDAR registrado en Start.
Su set estándar completo v2-r2 aprobó **10/12**, frente a **3/12** de v1.
Square180 CCW y shift140 CW tocaron la isla: queda pendiente reducir los
extremos espurios de LiDAR antes de considerarlo robusto. El juez y el modelo
físico son iguales; no se ha aumentado la velocidad máxima del coche.

La GUI rect100x180 CCW con x = +0,10 m pasó en **40,196 s sim / 41,186 s
pared**, sin contactos, con 11,80 cm de margen mínimo. Los siguientes intentos
GUI y sus fallos quedan en el [historial por salida](open-challenge-runs/realcar-starts-history.md)
y las [mejores por contexto](open-challenge-runs/realcar-robust-best-rounds.md).
Repetir con ruido antes de extrapolar una ronda a toda una geometría.

## Mejora v3: set estándar completo (8 de octubre)

`open_realcar_v3.yaml` mantiene el motor, servo y conducción de v2; amplía el
ajuste lateral del LiDAR y confirma el extremo en dos escaneos distintos.
El escaneo espurio de square180 queda como regresión de código. **112 pruebas
pasan** y el set v3-r1 aprobó **12/12**, todas con 30 puntos estimados, sin
contactos y margen superior a 5 cm. V2-r2 aprobó 10/12; v1, 3/12.

V3 prioriza completar geometrías: square100 CCW/CW tarda 33,416/33,596 s.
No sustituye el récord bajo 30 s de otro perfil/código. Las rondas más rápidas
válidas se conservan por contexto. Falta medir repetibilidad con ruido; las
salidas adicionales y GUI se registran en el historial. Comparación y evidencia:
[sets de robustez](open-challenge-runs/realcar-robust-validation.md),
[historial](open-challenge-runs/realcar-starts-history.md),
[mejores por contexto](open-challenge-runs/realcar-robust-best-rounds.md).

## Retraso de sensores en una salida desplazada: v4 en validación

El barrido rect100x180 x ±10 cm de v3 pasó 3/4; x = +0,10 m CW chocó con
el muro exterior. En el salto de control 2,935 → 4,159 s se mantuvo la
observación LiDAR de stamp 2,9 s y el avance siguió activo. No omitir esta ronda
ni extrapolar el 12/12 estándar a todas las salidas. El historial conserva
el fallo completo y los contactos. El origen del retraso no está aislado.

V4 añade freno ante LiDAR de más de 350 ms o IMU de más de 200 ms y pausa
la máquina de estados hasta recuperar observaciones. Conserva modelo, juez,
velocidades y steering de v3; está desactivado para los perfiles anteriores.
**114 pruebas pasan**, incluyendo el retraso registrado y la publicación de
freno sin avanzar la misión. La primera repetición de la salida fallida pasó;
El set estándar v4-r1 pasó 12/12, con 30 puntos estimados y sin contactos:
el menor margen fue 2,97 cm (rect100x180 CCW); otras once superaron 5 cm.
Square100 tarda 33,916/33,416 s, por encima de 30 s. Se comprueban además
salidas adicionales y GUI antes de promocionarlo. No atribuir diferencias
de tiempo a un parámetro sin controlar la variación del ruido.

## Cierre: v4 comprobado con salidas y GUI (8 de octubre)

V4 terminó **21/21 intentos observados válidos**: set estándar 12/12,
cinco salidas adicionales, tres GUI y un diagnóstico previo. Las GUI fueron
rect100x180 (+10 cm, CW), square180 CCW y shift140 CW: 39,811 / 50,897 /
42,796 s simulados; márgenes 6,14 / 10,20 / 14,02 cm y sin contactos.
La salida y = −1,30 m CCW también pasó, en 34,216 s. Se guardaron los
39 intentos de la iteración v3/v4, incluido el fallo v3 por retraso de sensores.
El historial y la tabla de mejores conservaron todas las promociones anteriores.

**Para continuar:** recuperar el objetivo de 30 s en square100 sin perder
puntos ni margen, manteniendo v4 como referencia de cobertura. La llegada y
la espera de esquina explican parte del tiempo añadido; probar más anticipación
solo cuando el hueco LiDAR lo permita, con el mismo set estándar antes de
promocionar. Repetir rect100x180 CCW (margen mínimo de 2,97 cm en el set v4)
y ampliar salidas gradualmente. No atribuir mejora a una sola repetición con ruido.

> **Para retomar:** leer primero "Dónde estamos" y "Cómo retomar". El trabajo anterior a la
> simulación honesta (antes del 6 oct 2026, tarde) y sus rondas se borraron el 9 oct 2026;
> quedan en el historial de git.

## Dónde estamos (6 de octubre de 2026, tras validar v4)

### Open Challenge — reajuste en **simulación honesta**

- **Descubrimiento clave:** todos los perfiles Open anteriores (`race_entry_v1–v26`,
  `open_fastservo_v1–v3`) se ajustaron con datos que el robot real **no tiene**:
  - distancia recorrida desde la **pose de Gazebo** (`/odom_gt`; respaldo `/odom`
    de ruedas ideales), y el robot real **no tiene encoder**;
  - rumbo desde la **orientación perfecta** de la IMU (el real integra el giroscopio);
  - LiDAR e IMU **sin ruido**.
  Por eso **ningún perfil Open existente está validado para el robot real**.
- **Ya implementado** ([simulación honesta](simulacion-honesta.md)):
  - distancia por **odometría LiDAR** (`open_lidar_odometry.py`, error −1,7 %/+0,2 %
    sobre ~25 m) y rumbo **integrado del giroscopio**: son los valores por defecto;
  - modo **`honest:=true`** (runner `--honest`): la estrategia no recibe `odom`,
    `odom_gt` ni `joint_states`; ruido LiDAR σ 15 mm y giroscopio con ruido/sesgo; la
    pose real se graba aparte (`audit_pose.csv`, incluye `/odom`) **solo para auditoría**
    (juez, márgenes, gráficos);
  - servo rápido estimado (`actuator_model:=true`): ver [modelo de actuadores](open-challenge-runs/actuator-model-findings.md).
- **Base del diagnóstico:** **`open_fastservo_v2`** en modo honesto.
  - Set estándar honesto (intento 1, 5 rondas): 4/5 válidas; (intento 2, 5 rondas): 0/5.
    Los fallos son **intermitentes** (el ruido cambia en cada corrida): el coche toca
    la isla o dispara un giro de más justo después de otro.
  - Diagnóstico agregado: la telemetría registra **`turn_trigger`** (qué condición
    disparó cada giro y con qué valores).
  - **Causa encontrada** (square100 ×4 por sentido, `dbg1..4-honest-fsv2-sq100-*`:
    5/8 válidas): las 3 fallas disparan un giro por "muro de enfrente" a 0,33–0,40 m
    de terminar el anterior. Justo después de un giro el coche sigue ~13° torcido; en
    `ALIGN_EXIT` el muro de enfrente se medía en la dirección **del coche** (no de la
    pista) y veía el **muro exterior** (0,26 m / sin 17° ≈ 0,87 m). FOLLOW usaba ese
    valor y giraba de más contra la isla. Era un error de lógica de esta familia de
    perfiles; el ruido solo cambiaba cuándo aparecía.
  - **Causa real:** `open_fastservo_v2` (heredado de `race_entry_v13`) tiene
    `turn_front_heading_axis` **apagado**: el muro de enfrente se mide siempre en la
    dirección del coche. Con el coche torcido tras una curva, los rayos pegan en el muro
    exterior. Recalculado offline con el eje de la pista: 2,07–2,16 m (sin muro); el nodo
    vio 0,72 m. La corrección de código (medir también en `ALIGN_EXIT`) es correcta pero
    solo actúa con esa opción encendida (`fix1-*`: sin efecto, cortado).
  - **Resultado previo a simplificar:** `open_fastservo_v4` = `v2` + `turn_front_heading_axis: true`:
    **square100 8/8 válidas** (4/4 por sentido, `v4r1..4-honest-fsv4-sq100-*`),
    30 puntos estimados en cada ronda, Start→fin **23,934–24,532 s sim**.
    El intento `v4t*` anterior fue interrumpido y no cuenta como validación.
    Set estándar honesto con tres repeticiones **terminado** (`std12-honest-fsv4-r1..3-*`):
    **35/36 válidas del runner**, 36/36 con 30 puntos estimados,
    Start→fin **23,638–24,828 s sim**, media **24,208 s**.
    Único rechazo: `shift140` CW repetición 2, margen circular −0,91 cm;
    chasis y ruedas auditados: **1,77 cm interiores / 13,08 cm exteriores**, sin
    contacto registrado ni disparo frontal prematuro. Conservar el rechazo original;
    la auditoría separada no lo convierte en puntuación oficial.
    V4 queda archivado al simplificar; su geometría del runner sigue pendiente.
    [Tabla y evidencia](open-challenge-runs/honest-fsv4-validation.md).
  - Hipótesis descartada antes: "el muro lateral se confunde con el de enfrente en FOLLOW"
    (recalculado offline, no se cumplía).
- **Controlador actual simplificado:** `open_sensors_v1.yaml`, mismo control de v4;
  OpenConfig 70 → 42 parámetros y YAML 26 → 12 → 1 (`direction: auto`); defaults sin cambios. Solo LiDAR/giroscopio/cámara;
  constantes físicas y de sensores aparte, sin opciones de pose ideal.
  80 pruebas funcionales, regresión idéntica en
  24.680 observaciones y **2/2 rondas GUI square100**: 30 puntos estimados,
  23,420 / 23,320 s sim. Cambios y límites.
  Refactorización posterior contra `cf5add4`: estados separados, procesamiento
  LiDAR reutilizado, grabador independiente y runner dividido. 17.820 pasos
  idénticos, 189 scans, 38 resúmenes históricos y archivos de evidencia iguales.
  Dos GUI adicionales válidas: CCW 23,231 s / CW 23,419 s sim, 30 puntos
  estimados por ronda. Guía para modificar el código.
  Perfiles anteriores (con pose): borrados el 9 oct 2026; copia en cada ronda (`source/profile.yaml`).
- **Por ruido, una ronda por combinación no alcanza:** el set estándar honesto tiene
  que correrse con **repeticiones** (propuesta: 3 por campo y sentido = 36 rondas).

### Infraestructura de pruebas (vigente)

- **Juez de reglas + validación estándar** para Open y Obstacle ([detalle](juez-y-validacion.md));
  sensores de contacto en muros y pilares; `rounds.jsonl` re-juzgado.
- **Set estándar Open:** `src/robotek_evaluation/tools/open_standard_suite.sh` — 6 campos ×
  2 sentidos, misma salida (y = −1,15) para todos los perfiles; es la única base
  comparable entre perfiles (índice de perfiles).
- **Iteración rápida:** sin GUI y a velocidad máxima (`--no-gui --real-time-factor 0`).
  El control usa el **reloj de simulación** (`use_sim_time`), así que acelerar no cambia
  el resultado (comprobado: Open 29,3–29,5 s a 1× y a máx.; ~1,8× más rápido en reloj
  real). Validar los candidatos finales **con GUI** (AGENTS.md).
- **Cortes automáticos del runner Open:** 180 s simulados (límite del reglamento) y
  30 s sin cambiar de sección ("trabado"); el motivo queda en `abort_reason`.
  **Hasta el 9 oct 2026 no funcionaban** tras un giro disparado por esquina: el
  vigilante descartaba las filas con comas dentro de `turn_trigger` y solo cortaba el
  tiempo máximo de pared (240 s). Ejemplos: `std12-honest-fastservo_v2-square100-cw`
  (6 oct) y una ronda de 803 s simulados en la Mac. Corregido en `tail_rows` (lee con
  `csv`); comprobado en vivo: corte por `no_section_progress_30s`.
- Rondas interrumpidas a mano: carpeta con `INTERRUPTED.md`, sin puntaje.

### Paquetes ROS 2 (7 oct 2026)

`robotek_sim` + `robotek_control` se dividieron en `robotek_description`, `robotek_gazebo`,
`robotek_common`, `robotek_open`, `robotek_obstacle`, `robotek_evaluation` y
`robotek_bringup` ([detalle](paquetes.md)). Las estrategias solo dependen de
`robotek_common`. Compilar con `colcon build`; runners en `src/robotek_evaluation/tools/`;
launch en `robotek_bringup`. Verificado: 77 pruebas, equivalencia Open y Obstacle,
rondas sin GUI y con GUI de ambos desafíos.

### Robot real (7 oct 2026)

`robot.launch.py` + paquete `robotek_hardware` (servo/motor con marcha atrás/LiDAR rotado/botón);
probado de punta a punta contra Gazebo (3 vueltas). Falta medir en el coche:
[lista](robot-real.md#pendiente-de-verificar-en-el-robot-por-ssh).

**Primera sesión en el Pi** (`ssh user@192.168.0.10`, `ROS_DOMAIN_ID=1`,
[detalle](robot-real-pi.md)): repo copiada y compilada; LiDAR (LD19), IMU y cámara vistos en
RViz desde la Mac (imagen en JPEG); `sensors.launch.py` en `peripherals`; detector de pilares
de la simulación (`obstacle_detector`) con colores HSV medidos en el coche (el rojo de la
simulación tomaba el piso de madera); prueba de servo por color (`servo_steer`, sin motor).
Prueba de actuadores (`actuator_test`, motor ≤ 0,25 s por pulso) y `power_monitor`: servo
orden → movimiento ≈ 60 ms; motor orden → aceleración ≈ 65–80 ms; IMU de la placa girada 90°
(adelante = +y); el nodo de motor del equipo no controla STBY (GPIO13) y nuestro
`motor_driver` no movía al 100 % (corregido); la alimentación no pierde potencia (Pi ≥ 4,91 V
con el motor al 100 %); al 100 % desde parado el coche se encabrita.
Motor en el suelo: se mueve desde el 10 %; tras 0,24 s ~0,11 m/s por cada 10 %; desde parado
el morro empieza a levantarse hacia el 50 %. Giro (pulsos de 1 s al 20 %, autorizados a potencia baja, con
vuelta atrás): velocidad de crucero v = 0,0137·(% − 6,5) m/s
(10–30 %, batería baja; `robot.yaml` actualizado: 73 %/m/s, mínimo 6,5 %); las ruedas giran menos de lo pedido (10° → ~4–7°,
25° → ~16–22°); marcha atrás funciona.
Siguiente: ángulo de las ruedas medido directamente (o pulsos más largos), velocidad de
crucero, marcha atrás; calibrar la cámara (HFOV, inclinación); probar en el campo real.

**Simulación del coche real** (`real_car:=true`, [detalle](simulacion-coche-real.md)): perfil
opcional con servo (60 ms, ~70°/s, zona muerta 5°), motor (retardo, respuesta, tabla de
velocidad real), rampas de `base_adapter`, IMU 50 Hz con el ruido real, cámara 6 fps y LiDAR
ciego detrás. Sin el argumento, todo igual que antes (verificado). Falta correrlo en la
máquina de simulación (Open y Obstacle) y re-medir la velocidad con la batería cargada.

### Estacionamiento (Obstacle, 7 oct 2026)

Mundo solo con el estacionamiento (`--layout parking`), estrategia `mode: park`:
entrada fija + A\* con el contorno real y lazo cerrado. **park8: 6/6 con 15 pts
estimados** sin GUI y 2/2 con GUI (48–128 s). [Hallazgos](obstacle-challenge-runs/parking-findings.md).
Siguiente: bajar el tiempo, medir la CPU del robot real, integrarlo tras las 3 vueltas y
probar la salida desde el estacionamiento (+7).

### Obstacle Challenge (sin aparcar)

- **Ya es honesto** (6 oct 2026, [detalle](simulacion-honesta.md#obstacle-honesto-6-de-octubre-de-2026)):
  `obstacle_strategy` solo usa `/scan`, `/imu` (giroscopio integrado) y `/camera/image`;
  distancia por `open_lidar_odometry`; ruido de sensores; pose real y pilares solo en auditoría.
- `obstacle_planner_v8` honesto: **10/13 rondas con 40 pts** (antes 16/16 no honesto). Localización
  correcta (p95 3 cm). Con GUI: reg0 CCW y CW válidas (40 pts, 73,9 y 75,4 s sim). Fallos = trampas del planificador: esquina SO de reg1-ccw (2/3) y reversa
  de recuperación que cruza mal un pilar (reg3-cw).
- **Servo rápido** (`actuator_model:=true`, p=20), semillas 0–4 × CCW/CW, sin GUI:
  - `fs-v8-*` (v8): 9/10 con 40 pts, 4/10 válidas; falla reg2-cw por cruzar mal un pilar al retroceder.
  - Arreglo: la carrocería que corta la línea radial de un pilar debe estar del lado de su color,
    también al retroceder (`BeamPlanner.wrong_side`). `ref-sync-*`: 6/6 con 40 pts.
  - **Refactor** ([obstacle-refactor.md](obstacle-refactor.md)): perfil **`obstacle_sensors_v1`**,
    equivalente a v8 + arreglo (29.304 ciclos idénticos). `os1-*`: **10/10 con 40 pts**, media
    72,4 s, sin contactos, pero **5/10 válidas**: pasadas a < 1 cm de muros o pilares.
    Con GUI: reg0 CCW y CW válidas (64,3 y 79,9 s sim).
- Siguiente: **márgenes con el servo rápido** (`plan_wall_margin`, `plan_pillar_margin`,
  `plan_soft`), repetir ×3, validar con GUI. Después el **aparcamiento** (+22 pts).

### Robot real

- Servo: medido en el coche el 8 oct 2026 (retardo ~60 ms, ángulo real por lado con círculos;
  [robot-real-pi.md](robot-real-pi.md), [simulación del coche real](simulacion-coche-real.md)).
- Sin encoder; LiDAR STL-19P (±45 mm); IMU de la RRC Lite (giroscopio).
- **Hecho el 9 oct 2026:** `battery_guard` copiado al Pi y probado (aviso en rojo bajo 6,8 V, sin
  parar el coche; [detalle](robot-real.md)); el motor tendrá su propia batería, así que la de la
  placa ya no caerá con el motor. **Pendiente:** comparar el `rrc_driver` del equipo con el
  oficial de Hiwonder y revisar qué activa `enable_reception`
  ([guía](ros-robot-controller-oficial.md#comparar-con-el-pi-cuando-conecte)).
  **RRC Lite probada en el coche el 9 oct** ([resultados](rrc-lite-pruebas.md#resultados-en-el-coche-9-oct-2026)):
  IMU 49 Hz, batería ~1 Hz, botones K1 (`id 1`) y K2 (`id 2`) OK, LED 1 y 2 (azules) y los 2 RGB
  OK, dirección OK (+20° → izquierda, servo en J4 = PWM 2). **El zumbador está quemado**: no se oyen
  los pitidos de `start_button`. Hecho: luces de estado en los RGB
  (`status_leds`, brillo 2/255, [estados](robot-real.md#luces-de-estado-rgb-de-la-placa)), probadas en
  el coche con estados simulados. K2 no se usa: las reglas prohíben meter datos con botones (§9.9).
  Pendiente: verlas con una ronda real y probar `battery_guard` con el coche andando.
  **El stack automático del equipo está desactivado** (9 oct): el Pi ya no arranca nodos al encender;
  hay que lanzar a mano y, para volver a activar `open` u `obstacle` al encender, seguir
  [robot-real-pi/autostart](robot-real-pi/autostart/README.md).
  USB comprobados el 9 oct ([nombres estables](robot-real-pi.md#los-usb-y-sus-nombres-estables-9-oct-2026)): placa y
  LiDAR ya iban por id; la cámara se pasó a `/dev/v4l/by-id/…`. Probado el cambio de puerto del LiDAR y la cámara (los nombres estables funcionan; hay que relanzar el stack). Prueba de estrés de USB hecha (placa en 2.0, 0 huecos, 0 errores): [resultados](robot-real-pi.md#los-usb-y-sus-nombres-estables-9-oct-2026). Falta repetirla con el coche en movimiento. Cámara: techo ~22,6 fps (YUYV 640×480), 6,7 con exposición automática, 17 en ROS con exposición manual; se desconectó sola una vez y el nodo no se recupera (reabrir tras fallos). Red Mac↔Pi: Cyclone + dominio 1 por defecto, falta instalar Cyclone en el Pi ([README](../README.md#red-entre-el-mac-y-el-pi-dds)).
- Referencia: en el Mundial 2025 el equipo (como "Ruwance") quedó 43.º de 64 con 33,2 pts
  (Open 5, Obstacle 5,5, documentación 22,7); el top 10 necesitó 30 + 62 y doc ≥ 25.

## Cómo retomar (comandos)

```bash
cd ~/Projects/Robotek && colcon build
source install/setup.zsh && bash src/robotek_evaluation/tools/clean_sim.sh

# 1. Una ronda Open honesta (servo estimado, sin GUI, rápida)
bash src/robotek_evaluation/tools/run_gui_experiment.sh prueba \
  --params-file src/robotek_open/config/open_sensors_v1.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square100.sdf \
  --direction cw --controller-direction auto --spawn-y -1.15 --spawn-yaw 3.141592653589793 \
  --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 \
  --launch-arg actuator_model:=true --honest --no-gui --real-time-factor 0

# 2. Set estándar honesto de un perfil (12 rondas)
bash src/robotek_evaluation/tools/open_standard_suite.sh <tag> <perfil.yaml> \
  --ackermann-steer-p-gain 20 --launch-arg actuator_model:=true --honest --no-gui --real-time-factor 0

# 3. Ver motivo de cada giro en una ronda honesta
python3 - <<'PY'
import csv; [print(r['sim_time'], r['turns'], r['turn_trigger']) for r in csv.DictReader(open('RUN/telemetry.raw.csv'))]
PY

# 4. Re-juzgar y regenerar índice
cd src/robotek_evaluation/tools && python3 judge_open_runs.py
```

Archivos útiles por ronda honesta: `telemetry.csv` (con pose real unida, para analizar),
`telemetry.raw.csv` (lo que vio la estrategia), `audit_pose.csv`, `contacts.jsonl`,
`rule_judge.json`, `summary.json` (`abort_reason`).

## Próximos pasos (en orden)

1. **Pruebas solicitadas terminadas:** v4 pasó square100 8/8 frente a 5/8 de v2;
   set estándar honesto repetido 35/36 según el runner, 36/36 con 30 puntos estimados.
   [Rondas, tiempos y auditoría](open-challenge-runs/honest-fsv4-validation.md).
2. **Resolver la geometría del runner antes de reajustar:** el rechazo de `shift140`
   CW viene del círculo interior conservador; chasis y ruedas dejan 1,77 cm.
   Integrar la geometría auditada sin borrar las clasificaciones históricas.
   Si se cambia la estrategia, aislar un factor y repetir la combinación estrecha.
3. **Validar el candidato con GUI**, especialmente `shift140` CW y square180 en
   ambos sentidos. Square100 GUI ya pasó 4/4 con `open_sensors_v1` (2/2 tras refactorizar); las demás
   geometrías siguen pendientes. El set repetido sin GUI de v4 ya terminó y perfiles.md
   está regenerado. No promover un perfil por un máximo estimado sin validar los márgenes.
4. **Medir el servo real** (video de ruedas en el aire o IMU) y fijar `steer_delay`,
   `steer_rate`, `steer_tau` del `sim_actuator_model`; revalidar.
5. **Obstacle honesto — hecho;** pendiente robustez del planificador (trampas en reg1-ccw y
   reg3-cw), repeticiones, `actuator_model:=true` y validación con GUI.
6. **Aparcamiento** (Obstacle, +22 pts): salida desde el aparcamiento (+7) y aparcar en
   paralelo (+15); agregar muros magenta y reubicación de pilares al generador.
7. **Robot real:** portar la estrategia Open honesta (LiDAR + giroscopio, sin encoder),
   probar Open primero.
   `rrc_test` ya corrido (9 oct; zumbador quemado). Falta vigilar la batería del motor (irá aparte; la placa no la mide),
   las luces de estado con una ronda real y comparar el nodo de la placa con el oficial (ver «Robot real»).
8. **Documentación del cuaderno de ingeniería** en paralelo (fue lo que definió el top 10).

Pendientes menores: rondas Obstacle no deterministas (planificador en hilo con tiempo de
cómputo real); `obstacle_planner_v11` preparado y sin correr; contactos del robot por
sensor propio no funcionan en Gazebo (se usan sensores en muros y pilares).
