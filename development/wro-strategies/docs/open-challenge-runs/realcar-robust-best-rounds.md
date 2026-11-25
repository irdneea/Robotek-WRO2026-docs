# Mejores rondas Open por geometría y salida

Motor `real_car_v1`, sensores honestos, dirección equivalente simétrica ±17,6°.
Se comparan **puntos primero y tiempo total desde Start después**, exigiendo
validación interna aprobada. Los puntos son estimados, no oficiales. Cada fila
conserva su contexto: campo, salida, sentido y GUI. Las pruebas sin GUI son
diagnósticos; confirmar los candidatos finales con GUI y repetir con ruido.
No reemplazar un récord de otra salida para presentar una mejora ficticia.

Candidato de cobertura comprobado al 8 de octubre: **`open_realcar_v4.yaml`**.
Se elige porque pasó el set estándar 12/12, cinco salidas adicionales, tres
validaciones GUI y el diagnóstico previo (21/21 intentos observados). Corrige
el ajuste lateral, confirma dos escaneos y frena ante sensores antiguos.
La física permanece idéntica. Son puntos estimados y una muestra limitada;
no garantiza futuras repeticiones. En square100 tarda 33,4–33,9 s: el récord
rápido histórico se conserva aparte y el objetivo de 30 s sigue pendiente aquí.

[Historial de promociones y fallos](realcar-starts-history.md).
[Cómo ejecutar las pruebas](../guia-correr-open-v4.md#coche-real-y-registro-de-mejoras).
[Récord histórico de la salida original](best-realcar-open-round.md).

| Evidencia de la mejor | Campo / sentido | Salida x, y, yaw | GUI | Puntos estimados | Start → fin sim / pared (s) | Margen mínimo (cm) | Por qué |
|---|---|---|---|---:|---:|---:|---|
| [std12-realcar-symmetric-final-r1-east140x100-ccw](20261008T052300Z-std12-realcar-symmetric-final-r1-east140x100-ccw/round.json) | east140x100 / CCW | 0.00, -1.15, 0.000 | no | 30 | 33.115 / 14.777 | 3.41 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v2-r2-east140x100-cw](20261008T063612Z-std12-realcar-starts-v2-r2-east140x100-cw/round.json) | east140x100 / CW | 0.00, -1.15, 3.142 | no | 30 | 38.216 / 17.062 | 10.30 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v3-r1-rect100x180-xm10-ccw](20261008T070420Z-realcar-starts-v3-r1-rect100x180-xm10-ccw/round.json) | rect100x180 / CCW | -0.10, -1.15, 0.000 | no | 30 | 41.133 / 18.254 | 9.56 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v4-r1-rect100x180-ccw](20261008T071552Z-std12-realcar-starts-v4-r1-rect100x180-ccw/round.json) | rect100x180 / CCW | 0.00, -1.15, 0.000 | no | 30 | 40.216 / 17.868 | 2.97 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v4-r1-rect100x180-xp10-ccw](20261008T072449Z-realcar-starts-v4-r1-rect100x180-xp10-ccw/round.json) | rect100x180 / CCW | 0.10, -1.15, 0.000 | no | 30 | 41.516 / 18.559 | 13.89 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v2-gui-rect100x180-xp10-ccw](20261008T063754Z-realcar-starts-v2-gui-rect100x180-xp10-ccw/round.json) | rect100x180 / CCW | 0.10, -1.15, 0.000 | sí | 30 | 40.196 / 41.186 | 11.80 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v3-r1-rect100x180-xm10-cw](20261008T070510Z-realcar-starts-v3-r1-rect100x180-xm10-cw/round.json) | rect100x180 / CW | -0.10, -1.15, 3.142 | no | 30 | 41.815 / 18.607 | 6.14 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v2-gui-rect100x180-xm10-cw](20261008T064136Z-realcar-starts-v2-gui-rect100x180-xm10-cw/round.json) | rect100x180 / CW | -0.10, -1.15, 3.142 | sí | 30 | 39.996 / 42.967 | 11.71 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v4-r1-rect100x180-cw](20261008T071641Z-std12-realcar-starts-v4-r1-rect100x180-cw/round.json) | rect100x180 / CW | 0.00, -1.15, 3.142 | no | 30 | 40.316 / 17.943 | 5.37 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v4-r1-rect100x180-xp10-cw](20261008T072539Z-realcar-starts-v4-r1-rect100x180-xp10-cw/round.json) | rect100x180 / CW | 0.10, -1.15, 3.142 | no | 30 | 40.033 / 17.754 | 10.22 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v4-gui-rect100x180-xp10-cw](20261008T072832Z-realcar-starts-v4-gui-rect100x180-xp10-cw/round.json) | rect100x180 / CW | 0.10, -1.15, 3.142 | sí | 30 | 39.811 / 40.396 | 6.14 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v2-r2-rect180x100-ccw](20261008T063223Z-std12-realcar-starts-v2-r2-rect180x100-ccw/round.json) | rect180x100 / CCW | 0.00, -1.15, 0.000 | no | 30 | 42.315 / 18.972 | 12.81 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v2-r2-rect180x100-cw](20261008T063313Z-std12-realcar-starts-v2-r2-rect180x100-cw/round.json) | rect180x100 / CW | 0.00, -1.15, 3.142 | no | 30 | 41.895 / 18.763 | 13.18 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v2-r2-shift140-ccw](20261008T063404Z-std12-realcar-starts-v2-r2-shift140-ccw/round.json) | shift140 / CCW | 0.00, -1.15, 0.000 | no | 30 | 40.616 / 18.087 | 13.06 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v3-r1-shift140-cw](20261008T070013Z-std12-realcar-starts-v3-r1-shift140-cw/round.json) | shift140 / CW | 0.00, -1.15, 3.142 | no | 30 | 42.706 / 18.991 | 13.92 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v4-gui-shift140-cw](20261008T073508Z-realcar-starts-v4-gui-shift140-cw/round.json) | shift140 / CW | 0.00, -1.15, 3.142 | sí | 30 | 42.796 / 43.426 | 14.02 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xm25-ccw](20261008T061229Z-realcar-starts-v1-r1-sq100-xm25-ccw/round.json) | square100 / CCW | -0.25, -1.15, 0.000 | no | 30 | 32.333 / 14.477 | 10.70 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xm10-ccw](20261008T060404Z-realcar-starts-v1-r1-sq100-xm10-ccw/round.json) | square100 / CCW | -0.10, -1.15, 0.000 | no | 30 | 31.116 / 13.817 | 9.53 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v2-probe-sq100-ym15-ccw](20261008T061905Z-realcar-starts-v2-probe-sq100-ym15-ccw/round.json) | square100 / CCW | 0.00, -1.30, 0.000 | no | 30 | 32.116 / 14.255 | 14.98 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-ym05-ccw](20261008T060803Z-realcar-starts-v1-r1-sq100-ym05-ccw/round.json) | square100 / CCW | 0.00, -1.20, 0.000 | no | 30 | 30.231 / 13.156 | 8.62 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-symmetric-final-r1-square100-ccw](20261008T051639Z-std12-realcar-symmetric-final-r1-square100-ccw/round.json) | square100 / CCW | 0.00, -1.15, 0.000 | no | 30 | 29.730 / 13.264 | 7.72 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-yp05-ccw](20261008T060633Z-realcar-starts-v1-r1-sq100-yp05-ccw/round.json) | square100 / CCW | 0.00, -1.10, 0.000 | no | 30 | 29.834 / 13.227 | 10.53 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-yp15-ccw](20261008T061400Z-realcar-starts-v1-r1-sq100-yp15-ccw/round.json) | square100 / CCW | 0.00, -1.00, 0.000 | no | 30 | 29.937 / 13.315 | 10.17 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xp10-ccw](20261008T060234Z-realcar-starts-v1-r1-sq100-xp10-ccw/round.json) | square100 / CCW | 0.10, -1.15, 0.000 | no | 30 | 29.832 / 13.300 | 10.98 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xp25-ccw](20261008T061058Z-realcar-starts-v1-r1-sq100-xp25-ccw/round.json) | square100 / CCW | 0.25, -1.15, 0.000 | no | 30 | 30.115 / 13.358 | 11.22 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xm25-cw](20261008T061315Z-realcar-starts-v1-r1-sq100-xm25-cw/round.json) | square100 / CW | -0.25, -1.15, 3.142 | no | 30 | 30.498 / 13.369 | 10.32 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xm10-cw](20261008T060449Z-realcar-starts-v1-r1-sq100-xm10-cw/round.json) | square100 / CW | -0.10, -1.15, 3.142 | no | 30 | 30.029 / 13.387 | 11.51 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-ym15-cw](20261008T061552Z-realcar-starts-v1-r1-sq100-ym15-cw/round.json) | square100 / CW | 0.00, -1.30, 3.142 | no | 30 | 31.116 / 13.841 | 10.38 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-ym05-cw](20261008T060848Z-realcar-starts-v1-r1-sq100-ym05-cw/round.json) | square100 / CW | 0.00, -1.20, 3.142 | no | 30 | 30.030 / 13.351 | 8.48 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-symmetric-final-r1-square100-cw](20261008T051724Z-std12-realcar-symmetric-final-r1-square100-cw/round.json) | square100 / CW | 0.00, -1.15, 3.142 | no | 30 | 30.034 / 13.373 | 8.82 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-yp05-cw](20261008T060718Z-realcar-starts-v1-r1-sq100-yp05-cw/round.json) | square100 / CW | 0.00, -1.10, 3.142 | no | 30 | 30.032 / 13.334 | 10.53 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-yp15-cw](20261008T061444Z-realcar-starts-v1-r1-sq100-yp15-cw/round.json) | square100 / CW | 0.00, -1.00, 3.142 | no | 30 | 29.656 / 13.229 | 10.74 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xp10-cw](20261008T060319Z-realcar-starts-v1-r1-sq100-xp10-cw/round.json) | square100 / CW | 0.10, -1.15, 3.142 | no | 30 | 31.615 / 13.979 | 9.88 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v1-r1-sq100-xp25-cw](20261008T061143Z-realcar-starts-v1-r1-sq100-xp25-cw/round.json) | square100 / CW | 0.25, -1.15, 3.142 | no | 30 | 31.831 / 14.179 | 10.23 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v2b-narrow-square180-ccw](20261008T062522Z-realcar-starts-v2b-narrow-square180-ccw/round.json) | square180 / CCW | 0.00, -1.15, 0.000 | no | 30 | 51.016 / 22.686 | 12.83 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [realcar-starts-v2-gui-square180-standard-ccw](20261008T064548Z-realcar-starts-v2-gui-square180-standard-ccw/round.json) | square180 / CCW | 0.00, -1.15, 0.000 | sí | 30 | 49.677 / 50.419 | 4.93 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |
| [std12-realcar-starts-v2-r2-square180-cw](20261008T062950Z-std12-realcar-starts-v2-r2-square180-cw/round.json) | square180 / CW | 0.00, -1.15, 3.142 | no | 30 | 49.516 / 22.054 | 6.16 | Máximo estimado, parada y validaciones aprobadas; menor tiempo del contexto. |

Cada ejecución conserva `source/profile.yaml`, código Open, `manifest.json`,
sensores, contactos y pose independiente de auditoría. Consultar su copia de
código antes de reproducir parámetros históricos. La velocidad máxima del motor
(0,60 m/s con batería baja) es inferida, pendiente de medir en el coche.
