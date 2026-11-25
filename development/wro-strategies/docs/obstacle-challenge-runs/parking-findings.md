# Estacionamiento (Obstacle) — mundo solo con el estacionamiento

7 de octubre de 2026. Simulación honesta (LiDAR, giroscopio, cámara con ruido), servo
rápido estimado (`actuator_model:=true`, p = 20), sin GUI salvo indicación.

## Reglas aplicadas

- Estacionamiento en la sección de salida, contra el muro exterior, en el extremo de la
  recta que queda "aguas abajo" en CCW (figuras 4 y 8d): un tope junto a la línea de
  sección (x = 0,5), 20 cm de fondo, largo = 1,5 × largo del robot.
- Robot: 0,19 m de largo con ruedas (chasis 177 mm) × 0,112 m → hueco **0,285 m**.
- Topes magenta 200 × 20 × 100 mm. Tocarlos detiene el robot y anula el estacionamiento.
- 15 pts: proyección completa dentro y paralelo (ruedas del lado del muro difieren
  ≤ 20 mm); 7 pts: parcial o no paralelo (1.8.2/1.8.3). Puntos estimados.

## Cómo correrlo

```bash
bash src/robotek_evaluation/tools/run_obstacle_gui_experiment.sh --name prueba-park \
  --layout parking --direction ccw --launch-arg actuator_model:=true --steer-p-gain 20 \
  --wall-timeout 300 [--no-gui --no-rviz --real-time-factor 0]
```

`--layout parking` arma el mundo (campo sin pilares + topes con sensores de contacto),
fija `mode: park` y juzga con `obstacle_parking_report.py`. El coche sale de la zona de
salida (x = ∓0,25, y = −1,0) como en las rondas normales.

## Estrategia (`robotek_obstacle/obstacle_parking.py`)

1. **Ubicar** los topes con el LiDAR (placas que salen del muro exterior) y ajustar la
   posición del hueco.
2. **Aproximación** paralela al muro hasta un punto 0,41 m más allá del inicio del hueco;
   si el hueco está justo detrás de la salida (CW), alinea primero y **retrocede en recta**.
3. **Entrada fija:** retroceso con dirección a fondo hacia el muro hasta 50°.
4. **A\*** sobre arcos de 3 cm (5 ángulos × avance/retroceso) con el contorno completo
   **y las ruedas delanteras giradas**, margen 1,5 cm a topes y muro; meta 1,5 cm dentro.
   Cartera de pesos (3, 4, 2) en 10 s; si no hay plan, mueve 2 cm y reintenta.
5. **Lazo cerrado:** tras cada arco verifica el resto del plan desde la pose estimada
   (tolera 5 mm); si ya no vale, replanifica. Guarda: frena si 1,5 cm más adelante
   quedaría a < 5 mm de un tope o del muro.

## Iteraciones

| Serie | Cambio | Resultado (15 pts) | Hallazgo |
|---|---|---|---|
| park1 | A\* + ejecución por tramos | 1/1 | quedó a 3,6 mm de la línea del hueco |
| park2 | meta 1,5 cm dentro | 0/4 | todas rozaron un tope: las **ruedas giradas** sobresalen 1,2 cm del contorno |
| park3 | ruedas en el modelo, margen 1,5 cm | 0/4 | roces por **lazo abierto** (≈ 20 cm de tramos sin corregir) |
| park4 | verificar el plan tras cada tramo | 3/4 | una búsqueda bloqueó el nodo minutos (sin límite de tiempo) |
| park5 | límite de tiempo y empujoncito | 5/6 | el empujoncito siempre adelante alejó al coche |
| park6 | aproximación más larga | 2/6 | A\* desde la aproximación no encuentra plan en 4 s con Gazebo en la CPU |
| (tabla) | costo-hasta-aparcar por programación dinámica | descartada | redondeo de la grilla ⇒ costos inalcanzables, ciclos |
| park7 | **entrada fija** + A\* desde dentro | 2/6 | el primer A\* aún excede 4 s |
| **park8** | cartera de pesos, 10 s, reintentos | **6/6** | 48–128 s; topes a ≥ 5 mm; ruedas ≤ 6 mm de diferencia |

**Con GUI** (`gui-park8-*`, tiempo real): CCW 15 pts en 67,4 s sim / 74,5 s pared (13 planes, ruedas
2 mm, topes ≥ 1,5 cm); CW 15 pts en 48,9 s / 54,5 s (7 planes, ruedas 1 mm, topes ≥ 1,3 cm).

Localización: error de la pose estimada < 8 mm durante las maniobras (ICP contra muros).

## Pendiente

- **Tiempo:** 48–128 s (7–24 planificaciones; esperas de servo y de asentamiento).
- **CPU del robot real:** cada plan puede tardar segundos en la Raspberry Pi; medir.
- Integrarlo tras las 3 vueltas (`laps` → `park`) y la salida desde el estacionamiento (+7).
- El hueco depende del largo real del robot: medirlo y ajustar `vehicle.py`.
