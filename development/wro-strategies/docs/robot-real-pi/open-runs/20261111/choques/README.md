# Choques del Open v5 en el coche, 11 nov 2026: diagnóstico

Los siete choques del día pasados por el detector de choques (`crash_watch.py`) y por la lista de causas de
`robotek-learn/tools/plot-crash.py`. Los `crash-*.json` se rehicieron desde la telemetría de cada ronda
(`/tmp/opencrash`, telemetría a ~10 Hz, sin `imu_age` ni `scan_age`): la dirección sale de `w_cmd/v_cmd`, no del
servo. Desde el commit `75a77ef` de robotek-learn el coche escribe el archivo él solo, a 50 Hz y con las edades de los
sensores. Salida completa en [diagnostico.txt](diagnostico.txt); un gráfico por choque (`choque-<hora>.png`).

| Ronda | ¿Perdió scans el LiDAR antes del impacto? | Coche | Causa probable |
|---|---|---|---|
| 14:53 | No | giró como pedía | TURN tarde: empezó con 0,63 m delante (primera curva) |
| 15:28 | No | giró como pedía | TURN tarde: 0,76 m |
| 15:42 | Un hueco de 0,2 s, 1,4 s antes | giró como pedía | TURN tarde: 0,75 m (tercera curva) |
| 16:18 | Hueco de 0,4 s en plena curva, 0,8 s antes | giró como pedía | TURN tarde (0,77 m) y LiDAR perdido en la curva (antes de `turn_scan_max_age`) |
| 16:29 | Dos de 0,2 s, lejos del impacto | giró como pedía | Roces en curva 6 (TURN con 1,06 m) |
| 17:59 | No | **no giró**: dirección pedida y giroscopio ~0 desde 1,4 s antes | Servo congelado |
| 18:01 | No | **giró al revés**: pedía +22° (izquierda) y giraba a −100 °/s desde 1,0 s antes | Servo congelado a la derecha |

Conclusión: el LiDAR no causó los choques salvo, en parte, el de las 16:18. Los cuatro primeros fueron giros tardíos
(después se cambiaron `corner_lookahead`, `brake_margin` y `corner_speed`); los dos últimos, el servo.

## Por qué el LiDAR perdía scans (11 nov 2026, 18:20)

Medido por capas con el coche quieto:

1. `/scan`, `/robotek/scan` y la estrategia: los huecos ya están en el `/scan` del driver, con el mismo tamaño en la
   hora de llegada y en el sello (latencia ~1 ms). No los pierde DDS, `scan_adapter`, la CPU ni la estrategia.
2. Puerto serie, sin el driver (`robotek-learn/tools/lidar-raw-check.py`): 7922 paquetes en 20 s, 0 con CRC malo,
   ninguno perdido en el cruce de 0°; el LD19 gira a 9,91 Hz. La línea está limpia.
3. El driver solo (`ldlidar_stl_ros2`): 5 huecos de 0,2 s en 40 s, igual con la CPU cargada. Causa: su bucle ROS
   pregunta cada 100 ms (`WallRate(10)`) por la última vuelta, sin esperar, y el LD19 cierra una cada 100,9 ms; las dos
   fases se cruzan cada ~10 s y una vuelta se pisa con la siguiente.

Arreglo (robotek-learn `5efc074`): preguntar a 200 Hz. Después: 0 huecos en 120 s (en reposo y con 3 núcleos
ocupados), 9,91 Hz publicados (antes 9,87) y 2,4 % de CPU del driver.

Con el motor en marcha (coche levantado, 3,7 rps ≈ 0,85 m/s, 25 s entre 10 s parado antes y después; solo el driver
de la placa lanzado): 18750 paquetes, 0 CRC malos, ninguno perdido en 0°, el LD19 a 9,89-9,93 Hz igual que parado. El
motor no ensucia la línea serie. Límites: levantado el motor consume menos que en el suelo, y no giraba el servo ni
había golpes. La prueba final es una ronda en el suelo con el driver nuevo, mirando los huecos de `/robotek/scan`.
