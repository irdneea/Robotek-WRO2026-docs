# Vídeos de una ronda Obstacle v3 (3 nov 2026)

Ronda grabada en el Mac con GUI: Obstacle v3, campo `reg1-ccw` con aparcamiento (`regulation-park`, semilla 1),
CCW, salida en x −0,25, y −1,0, rumbo 0, ganancia de dirección 20, `real_car:=true`, modo honesto, a 1x.
Coche de `2b17266`. **55 puntos (24 + 3 + 3 + 10 + 15), válida, 129,02 s** desde Start; termina aparcada.

Los vídeos están en esta carpeta, solo en local (`.gitignore`):

| Archivo | Qué muestra | Tamaño |
|---|---|---|
| `gazebo.mp4` | Gazebo, vista inclinada de todo el campo (la parte que no tapa RViz) | 1956×1888 px, 30 fps, 134,7 s |
| `rviz.mp4` | RViz: arriba la cámara con las detecciones (*Direction evidence*); abajo el robot, el LiDAR, la flecha cian de la dirección mandada y la línea al próximo pilar recordado (roja o verde) | 1068×1880 px, 30 fps, 134,7 s |
| `gazebo-rviz.mp4` | los dos lado a lado, sincronizados (salen de la misma grabación), como el del Open | 3028×1888 px, 30 fps, 134,7 s |

Empiezan 1 s antes del Start y terminan 3 s después de aparcar.

## Cómo se grabó

- La ronda se abrió con `--param auto_start=false` y `--no-rviz`. RViz se abrió aparte con una configuración de
  grabación: modelo del robot, LiDAR, marcadores de `/obstacle/detections` y la imagen *Direction evidence*.
  No se tocó la del repo.
- El usuario colocó las ventanas. La cámara de Gazebo se puso con `/gui/move_to/pose` (posición 0,35, −2,15,
  2,45, mirando al centro). Después se publicó `/start`.
- Se grabó la pantalla con `ffmpeg` (`avfoundation`, 30 fps) y se recortó cada parte.

## Límite conocido

En los últimos ~35 s (el aparcamiento), la línea al pilar apunta hacia atrás, a un pilar ya pasado. La misión
no actualiza el próximo pilar al aparcar. Está corregido en `5cf3771` (la línea solo se dibuja durante las
vueltas), después de esta toma.

## Las tomas anteriores

En el registro como intentos de grabación:

| Ronda | Resultado | Por qué no se usó |
|---|---|---|
| `20261103-191459-video-obs-v3-reg1-ccw` | 55 pts, válida, 128,62 s | en la grabación salían otras ventanas y la cámara cambió a mitad de ronda; la grabación se borró |
| `…-ccw-b` a `…-ccw-e` | abiertas sin arrancar y cerradas | se cerraron para cambiar RViz (modelo del robot, LiDAR, líneas y flecha) |
