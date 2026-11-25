# Robotek — Mapeo y racing en Raspberry Pi 5 (investigación)

**Fecha:** 2026-10-05 · **Estado:** investigación / decisión pendiente de implementar
**Relacionado:** `robotek-open-challenge-strategy.md`,
[`../referencias/04-analisis-codigo-open-challenge.md`](../referencias/04-analisis-codigo-open-challenge.md)

## 0. Pregunta

¿Se puede mapear la pista con LiDAR + IMU en la vuelta 1 y correr las vueltas 2–3 con
el mapa ya construido y a más velocidad, para bajar el tiempo de la ronda? ¿Hay mucho
drift en el sensor? **Restricción: debe correr en una Raspberry Pi 5.**

**Terminología:** *vuelta* = un circuito completo (8 secciones / 4 esquinas). *Ronda* =
una corrida completa del Open = **3 vueltas** con **cronómetro continuo** (máx. 3 min),
que termina al detenerse en la sección de finish tras 3 vueltas o al expirar el timer.
**El tiempo que se puntúa es el de la ronda (3 vueltas), no el de una vuelta.** Por eso
mapear la vuelta 1 y correr las 2–3 más rápido baja el **tiempo de ronda**.

## 1. Conclusión rápida

- **Sí es viable en RPi 5**, pero no todas las opciones cuestan igual. **Evitar
  Cartographer**; si se va a SLAM completo, usar **slam_toolbox**.
- Para este caso, la mejor relación resultado/esfuerzo es la **Opción 1–2** (grabar la
  vuelta 1 y seguirla con **pure pursuit**), **sin SLAM completo**. Es además lo que la
  literatura de racing señala como lo más rápido.
- El **drift no lo arregla el algoritmo**: en la sim actual es ~0 (sensores sin ruido);
  en hardware lo acotan **el muro exterior + loop closure + un EKF**.

## 2. Presupuesto de cómputo en RPi 5

- RPi 5 = **Cortex-A76 ×4 @2.4 GHz**, ~2–3× Pi 4; arm64 es **Tier 1** en Jazzy.
- Sensor ligero: LiDAR 10 Hz × 500 haces ≈ 5 k puntos/s. El cuello de botella no es el
  sensor, es **sumar SLAM + localización + plan + control + cámara sin romper el lazo de
  control**.
- Tuning: instalar `ros-jazzy-slam-toolbox` por **apt** (no compilar); bajar
  `resolution` del mapa y `max_laser_range`; modo **asíncrono**; `scan_queue_size: 1`;
  `governor=performance`; disipación. **No correr mapeo y localización a la vez**
  (secuenciarlos por vuelta).

## 3. Qué dice la evidencia

- **F1TENTH survey** ([arXiv 2402.18558](https://arxiv.org/abs/2402.18558)): el stack
  estándar es **slam_toolbox (mapa) + particle filter (localización) + pure pursuit
  (control)**. Resultado clave: **"optimisation & tracking" (raceline offline + pure
  pursuit) logra los mejores tiempos**; MPCC es más sensible al **error de
  localización**; el error de pose degrada la tasa de completado. Los métodos con mapa
  quedan **restringidos a entornos mapeados**.
- **MDPI 2025** ([slam_toolbox vs Cartographer](https://www.mdpi.com/2079-9292/14/24/4822)):
  slam_toolbox mejor balance; **Cartographer más CPU (~80%) y RAM (~299 MB)**, mapeo más
  lento.
- **Particle filter F1TENTH** usa [`range_libc`](https://github.com/f1tenth/particle_filter)
  para raycasting rápido; en NUC/Jetson va sobrado, en RPi 5 hay que **bajar nº de
  partículas y muestrear el scan** (p. ej. 500 → 108 haces).
- **slam_toolbox** tiene modo **localization** (carga el pose-graph serializado y localiza
  con scan matching, tipo AMCL) y es el mantenido en ROS 2
  ([repo](https://github.com/SteveMacenski/slam_toolbox)).

## 4. Las 4 opciones, evaluadas para RPi 5

| Opción | Cómputo en RPi 5 | Dificultad | Robustez a drift | ¿Cuándo? |
|---|---|---|---|---|
| **1. Replay de trayectoria** | **Muy bajo** (guardar un path; pure-pursuit) | Baja | **Alta** (corrige con muros) | **Primero** |
| **2. Topológico/features** | **Muy bajo** | Baja-media | Alta | Complemento de 1 |
| **3. SLAM + localización** | Medio (slam_toolbox) / Alto (Cartographer) | Alta | Media (necesita loop closure + buen odom) | Si se necesita pose global |
| **4. Raceline** | Bajo en runtime (se calcula entre vueltas) | Media | n/a | Encima de 1/3 |

## 5. Sobre el drift

- **En la sim no se ve**: el IMU (`robotek.urdf.xacro:259`) y el LiDAR **no tienen
  `<noise>`**; `/odom` es dead-reckoning determinista del plugin Ackermann y `/odom_gt`
  es perfecto. Un enfoque con mapa parecerá impecable → **no valida nada**.
- **En hardware**: el **yaw** deriva ~1–10°/min tras calibrar sesgo; la **rueda patina**
  en curvas. La tolerancia de giro actual es 0.12 rad (**~7°**), así que en ~1 min el
  drift pesa.
- **El LiDAR no deriva**; deriva la **pose estimada**. Ventaja: muro exterior continuo +
  lazo corto (~20–40 s) ⇒ **loop closure trivial**.
- **Anclas de corrección**: re-cerrar yaw contra la pared (`wall_yaw`; hoy
  `wall_heading_gain = 0`) y **EKF** (`robot_localization`, fusión `/odom` + `/imu`).

## 6. Arquitectura recomendada para RPi 5

1. **Vuelta 1 (mapeo "gratis")**: conducir a velocidad moderada grabando pose (x,y,yaw) +
   perfil; o correr `slam_toolbox` async y **serializar** el pose-graph.
2. **Entre vueltas**: calcular una **raceline de mínima curvatura + perfil de velocidad**
   (Heilmeier; milisegundos) o simplemente reusar el path grabado.
3. **Vueltas 2–3 (rápidas)**: **pure pursuit** con lookahead dependiente de velocidad,
   corrección lateral por LiDAR (L−R) y un **safety** (follow-the-gap / frenada de
   emergencia). Cap de velocidad por dirección:
   `v = min(v_raceline, sqrt(1.5·g·L/tan|δ|))`.
4. **Solo si se necesita pose global**: `slam_toolbox` localization mode (o PF ligero con
   `range_libc`, pocos cientos de partículas). Mantener **fallback mapless**
   (wall-follower actual) por si falla la localización.

## 7. Reglas y coste/beneficio

- Layout y dirección **aleatorios por ronda** → mapeo **in-run** obligatorio; 3
  vueltas/3 min ⇒ la vuelta 1 se invierte en mapear.
- **La velocidad domina**: los top reales hacen 3 vueltas en **22–43 s a ~2 m/s**; la sim
  va a 0.25 m/s. El mapa ayuda sobre todo a **entrar a las curvas rápido y con seguridad**,
  no baja el tiempo por sí solo.
- Antes de confiar en cualquier enfoque con mapa, **inyectar ruido** en sim
  (sesgo/random-walk de gyro + slip de ruedas) y/o validar en la Pi.

## 8. Apéndice: ¿qué es pure pursuit?

Es el **controlador de seguimiento de trayectoria más usado** en F1TENTH. Dada una
**trayectoria** (waypoints) y la **pose actual**, calcula el ángulo de dirección para
"perseguir" un punto de la trayectoria situado por delante del vehículo.

**Mecanismo:**
1. Se traza un círculo de radio `Ld` (**lookahead**) centrado en el eje trasero (o base).
2. Se toma el punto de la trayectoria que corta ese círculo: el **lookahead point**.
3. Se calcula el ángulo `α` entre el rumbo del coche y la dirección a ese punto.
4. El steering sale de la geometría (modelo de bicicleta):

```
δ = atan( 2 · L · sin(α) / Ld )      # L = distancia entre ejes (wheelbase)
R = L / tan(δ)                        # radio de arco resultante
```

**Intuición:** cuanto más a la izquierda esté el punto de mira (`α>0`), más se gira a la
izquierda; `Ld` controla la agresividad.

**Tuning:**
- `Ld` **pequeño** → responde rápido pero oscila / corta poco.
- `Ld` **grande** → suave pero "corta" las curvas (lag).
- Lo típico es `Ld = k · v` (**lookahead dependiente de velocidad**) y limitar la
  velocidad por el ángulo de dirección para no subvirado:

```
v = min(v_raceline, sqrt(1.5 · g · L / tan|δ|))
```

**Ventajas:** simple, robusto, solo necesita **pose + path**.
**Desventajas:** no modela dinámica a alta velocidad (puede subvirar) y **necesita
localización**.

**En Robotek:** el "path" sería la trayectoria grabada de la vuelta 1 (o la raceline), la
pose sale de IMU + LiDAR, y se añade la corrección lateral y el safety. Encaja directo con
el lazo cascada que ya hay (`open_controller.py`), sustituyendo/añadiendo un término de
seguimiento de waypoints al `steer` actual.

## 9. Referencias

- F1TENTH survey (unsurvey/benchmarks): <https://arxiv.org/abs/2402.18558>
- slam_toolbox vs Cartographer (MDPI 2025): <https://www.mdpi.com/2079-9292/14/24/4822>
- slam_toolbox: <https://github.com/SteveMacenski/slam_toolbox>
- F1TENTH particle_filter / range_libc: <https://github.com/f1tenth/particle_filter>
- ROS 2 en Raspberry Pi: <https://docs.ros.org/en/jazzy/How-To-Guides/Installing-on-Raspberry-Pi.html>
