# Obstacle v3 en el coche real, 4 nov 2026

Primeras rondas del Obstacle v3 (robotek-learn, `robotek_obstacle_v3`) en el coche, con la cámara IMX708 Wide.

Configuración:

- **Lanzamiento:**

  ```bash
  ros2 launch robotek_course car.launch.py strategy:=robotek_obstacle_v3 camera_driver:=picam motor_max_rps:=2.5 \
      strategy_params:=$HOME/.config/robotek/obstacle_v3_car_picam.yaml
  ```

- **Cámara:** 640x360 a 30 fps.
- **Motor:** en M1, tipo 2.
- **Freno:** reinicio de la placa al final.
- **Rangos de la cámara:** ver el README de `robotek_obstacle_v3` en robotek-learn.
- **Medición de la cámara:** con tres pilares a ~0,9 m comparados con los grupos del LiDAR.
  - El HFOV sale en ~102°, así que es la versión Wide, aunque `rpicam` la lista solo como "imx708".
  - El error de rumbo es de 0,8° rms.
  - Con los valores de la cámara USB, no veía el pilar rojo y emparejaba un verde con un objeto a 2,1 m.

Las bolsas (`bag/`, ~80 MB cada una) se quedaron en el Mac (`/tmp/obsrun/`) y en el Pi (`~/runs/`). Aquí van
`launch.log` y `metadata.yaml` de cada ronda.

No hay juez ni pose real. Ninguna ronda pasó la primera esquina, así que la puntuación es 0 en las dos.

## Ronda 1 (`20261104-224901-obstacle-v3`): esquivó el pilar y chocó contra la pared exterior

Grabación sin imagen de detecciones.

- **0–19 s:** la estrategia pide 0,30 m/s (~1,4 rps de la placa), pero el coche no se mueve. El LiDAR marca 0,73 m
  delante todo el rato. El motor 310 no movía el coche con 1,3 rps o menos (3 nov). Hay que confirmar si el
  usuario lo empujó.
- **~19 s:** arranca y rodea el pilar girando a tope a la izquierda. El giroscopio lo confirma (+1 rad/s).
- **Después:** queda con el morro contra la pared izquierda. Pide 0,15 m/s con la dirección a tope a la derecha y,
  como la v3 no tiene marcha atrás, se queda ahí hasta ~48 s.

## Ronda 2 (`20261104-225602-obstacle-v3`): giró a la derecha del pilar rojo y chocó con la isla

Grabación con RViz y la imagen de detecciones (`ronda2-salida.jpg`: SETUP, RUN, comienzo del giro y el pilar
pasado).

- **Salida:** pilar rojo de frente a 0,95 m (rumbo −4°), bien detectado y emparejado.
- **Giro:** la v3 decide pasar por la derecha, que es lo correcto para el rojo, y gira a tope (−17,8°) desde t = 0.
  - A t = 1,1 s el rumbo ya es 27°, pero sigue a tope.
  - Hasta t = 1,4 s no cambia de lado.
- **Choque:** a t = 1,6 s el rumbo es 54° con solo ~0,35 m recorridos, que es el radio mínimo (0,37 m). A t = 2 s la
  isla queda a menos de 0,12 m delante.
- **Recuperación:** se libera hacia t = 7 s, pero luego va casi todo el tiempo a tope a la derecha (t = 13–40 s).
- **Final:** se paró con el botón a los 45 s.
- **Placa:** se reinició sola 3 veces mientras el coche avanzaba, a t = 15,5, 25,7 y 35,2 s, una cada ~10 s.
  - Cada reinicio dejó 2,6 s sin IMU (`Board data back after 2.6 s`) y la v3 se quedó en WAIT_SENSOR.
  - La batería estaba en 7,15–7,45 V, a 1 Hz.
  - En las rondas del Open no pasa. Aquí la dirección estuvo a tope casi todo el tiempo; sospecha: el servo
    bloqueado contra el tope tira de la alimentación de la placa. No está confirmado.

## Reproducción de la ronda 2 sin el coche

Se pasó la bolsa por la `Strategy` de robotek-learn (`tools/replay.py <bag> [s]`; `tools/read.py` resume la bolsa): LiDAR, IMU, señales emparejadas
(`/obstacle/signs`) y Start, con un tick por cada `/cmd_vel_raw` grabado. La dirección coincide con la del coche
(el cambio de lado, a 6,6 s en los dos). Los tiempos de la reproducción cuentan desde el botón: el RUN empieza a
4,9 s y equivale al t = 0 de la ronda.

1. **Posición inicial:** la v3 se ubica bien, en el centro del carril, al principio de la recta de salida.
   - En el marco espejado del sentido horario: x −0,46, y −1,00, rumbo 2°, phi 0,04.
   - Coincide con el LiDAR, que da 0,49 / 0,47 m a los lados.
2. **Pilar:** el rojo a 0,95 m está en phi ≈ 1. En el marco espejado sale como "green" a la izquierda, porque el
   sentido horario cambia los colores.
3. **Plan:** pide pasarlo por el lado de la isla, a +0,30 m del centro (y = −0,70).
   - El plan se construye desde la vuelta anterior, así que el desvío ya vale 0,30 justo donde está el coche
     (phi 0). No hay rampa desde el centro del carril.
4. **Dirección:** el coche empieza 0,30 m fuera de su línea.
   - La realimentación lateral vale 6 rad/m, así que 1,8 rad, muy por encima del límite de 0,307 rad.
   - La dirección queda a tope hasta que el término de rumbo la compensa, con ~46° de rumbo y 0,17 m de error.
5. **Choque:** con el retraso del servo, llega a la línea (error ≈ 0, t ≈ 7,0) con 57° de rumbo.
   - Para volver a 0° a tope (radio 0,37 m) se pasa unos 0,37 · (1 − cos 57°) ≈ 0,17 m hacia la isla.
   - La línea está a 0,20 m de la isla y el coche mide 0,065 m de semiancho: choca.

Conclusión: no es un fallo de la cámara ni de la ubicación. Es un salto lateral de 0,30 m sin rampa a la salida,
con un pilar en la recta de salida. Ahí la ley de dirección satura y llega a la línea con un ángulo del que no
puede volver.

Arreglos posibles; los dos cambian la estrategia y hay que validarlos antes en el lab y en Gazebo:

- **Ángulo máximo de aproximación:** limitar el rumbo con el que se busca la línea (p. ej. 25°) en lugar de
  sumar el término lateral sin límite.
- **Rampa en la salida:** que el plan empiece en el desvío real del coche.

## Pendiente

- **Mismo caso en el lab:** compararlo con `--car real_v2`, con un pilar en la recta de salida a ~1 m.
- **Reinicios de la placa:** ver si coinciden con la dirección a tope; probarlo con el coche quieto y el servo a
  ±17,8°.
- **Velocidad mínima:** confirmar si el motor arranca con la v3 a 0,15–0,30 m/s (0,7–1,4 rps).
