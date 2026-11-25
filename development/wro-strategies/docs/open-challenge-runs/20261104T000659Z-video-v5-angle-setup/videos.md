# Vídeos de una ronda Open v5 (3 nov 2026)

Ronda grabada en el Mac con GUI: Open v5, campo `square100`, CCW, salida en x 0, y −1,15, rumbo 0,
ganancia de dirección 20, `real_car:=true`, modo honesto, a 1x (`--real-time-factor 1`). Coche de
`2b17266`. **30 puntos, válida, 33,054 s** desde Start (reloj de pared 33,55 s).

Los vídeos están en esta carpeta, solo en local (`.gitignore`):

| Archivo | Qué muestra | Tamaño |
|---|---|---|
| `gazebo.mp4` | Gazebo con la vista inclinada de todo el campo (elegida por el usuario) | 2076×1888 px, 30 fps, 36,6 s |
| `rviz.mp4` | RViz: arriba la cámara del coche con el diagnóstico de dirección (*Direction evidence*), abajo el LiDAR en 3D | 914×1850 px, 30 fps, 36,6 s |
| `gazebo-rviz.mp4` | los dos lado a lado, sincronizados (salen de la misma grabación) | 3008×1888 px, 30 fps, 36,6 s |

Los dos empiezan 1 s antes del Start y terminan 2 s después del final.

## Cómo se grabó

- La ronda se abrió con `--param auto_start=false`. El usuario colocó las ventanas y la vista, y después se
  publicó `/start` (`ros2 topic pub --once /start std_msgs/msg/Bool "{data: true}"`).
- Se grabó la pantalla completa con `ffmpeg` (`avfoundation`, 30 fps) y se recortó cada ventana por su
  rectángulo. La grabación completa se borró al terminar.

## Las tomas anteriores

Están en el registro como intentos de grabación. Todas son válidas, con 30 pts:

| Ronda | Tiempo | Por qué no se usó |
|---|---|---|
| `20261103T235516Z-video-v5-sq100-ccw` | 33,296 s | corrió a máxima velocidad (el `world.sdf` venía de una ronda sin ventana); las ventanas se colocaron después del Start |
| `20261103T235707Z-video-v5-sq100-ccw-1x` | 32,785 s | RViz en media pantalla: los paneles tapaban la vista 3D |
| `20261103T235948Z-video-v5-sq100-ccw-1x-b` | 32,682 s | igual; plegar paneles desde la configuración no funciona en RViz 2 |
| `20261104T000146Z-video-v5-sq100-ccw-1x-c` | 33,207 s | buena, pero con la cámara de Gazebo fija sobre una recta: el coche se perdía detrás de la isla |
| `20261104T000408Z-video-v5-sq100-ccw-1x-d` | 33,297 s | se movió la vista durante la grabación |
