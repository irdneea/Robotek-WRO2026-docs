# Open fastservo v4 — validación honesta

## Square100: cuatro rondas por sentido

`open_fastservo_v4` cambia únicamente `turn_front_heading_axis: true` respecto a v2.
Pruebas con `run_gui_experiment.sh`, `--honest`, sin GUI, RTF máximo,
`actuator_model:=true`, ganancia Ackermann 20, límite de velocidad 4 m/s,
salida (0, −1,15), yaw 0 CCW / π CW y dirección del controlador `auto`.
Dirección ordenada limitada a ±25°. La pose real se conserva solo para auditoría.

**Resultado: 8/8 válidas (4/4 CCW y 4/4 CW), frente a 5/8 de v2**
en `dbg1..4-honest-fsv2-sq100-*` (se excluye el intento `dbg` previo).
Las ocho rondas tienen 30 puntos estimados, sin contactos y parada observada ≥30 s sim.
Start→fin incluye calibración y detección: 23.934–24.532 s sim, media 24.160 s;
13.949–14.399 s de pared (ejecución acelerada).

| Ronda | Puntos estimados | Válida | Start→fin sim (s) | Start→fin pared (s) |
|---|---:|---|---:|---:|
| [v4r1-honest-fsv4-sq100-ccw](20261006T190930Z-v4r1-honest-fsv4-sq100-ccw/round.json) | 30 | sí | 23.934 | 13.949 |
| [v4r1-honest-fsv4-sq100-cw](20261006T191027Z-v4r1-honest-fsv4-sq100-cw/round.json) | 30 | sí | 24.532 | 14.399 |
| [v4r2-honest-fsv4-sq100-ccw](20261006T191118Z-v4r2-honest-fsv4-sq100-ccw/round.json) | 30 | sí | 23.936 | 14.237 |
| [v4r2-honest-fsv4-sq100-cw](20261006T191209Z-v4r2-honest-fsv4-sq100-cw/round.json) | 30 | sí | 24.045 | 14.067 |
| [v4r3-honest-fsv4-sq100-ccw](20261006T191300Z-v4r3-honest-fsv4-sq100-ccw/round.json) | 30 | sí | 24.132 | 14.120 |
| [v4r3-honest-fsv4-sq100-cw](20261006T191350Z-v4r3-honest-fsv4-sq100-cw/round.json) | 30 | sí | 24.040 | 14.070 |
| [v4r4-honest-fsv4-sq100-ccw](20261006T191440Z-v4r4-honest-fsv4-sq100-ccw/round.json) | 30 | sí | 24.234 | 14.165 |
| [v4r4-honest-fsv4-sq100-cw](20261006T191530Z-v4r4-honest-fsv4-sq100-cw/round.json) | 30 | sí | 24.430 | 14.272 |

Cada carpeta conserva `round.json`, `rule_judge.json`, parámetros, código, logs,
telemetría, sensores y pose de auditoría. El ledger `rounds.jsonl` conserva cada intento.
Los parciales por vuelta están separados en el registro: no sustituyen el tiempo de ronda.

Auditoría de `turn_trigger`: los tres fallos de v2 contienen un disparo frontal
a 0,33 / 0,37 / 0,40 m desde el giro anterior. En las ocho rondas de v4
no hay disparos frontales posteriores al primer giro con `dist < 0,6 m`;
el menor valor registrado es 0,75 m. Es evidencia favorable al diagnóstico
de falsa pared frontal, sin atribuir una garantía general a ocho intentos.

La mejora permite pasar al set estándar; estas ocho observaciones no demuestran
robustez en otras geometrías ni validan el robot real. El bonus de parada es provisional
y la puntuación oficial permanece desconocida.

## Set estándar honesto: tres repeticiones completas

**35/36 válidas según la validación estándar del runner.**
Todas conservan 30 puntos estimados por el juez de simulación; un máximo estimado
no sustituye la validación de margen ni es puntuación oficial.
Ejecutadas con `open_standard_suite.sh honest-fsv4-r1..3`, mismo perfil y opciones
que square100: `--honest --no-gui --real-time-factor 0`, servo estimado y ganancia 20.

Start→fin: 23.638–24.828 s sim, media 24.208 s; 13.701–14.467 s de pared.

| Campo | CCW válidas | CW válidas | Menor margen runner (cm) | Menor margen chasis y ruedas (cm) |
|---|---:|---:|---:|---:|
| square100 | 3/3 | 3/3 | 12.71 | 12.07 |
| square180 | 3/3 | 3/3 | 1.22 | 5.21 |
| rect100x180 | 3/3 | 3/3 | 7.67 | 10.46 |
| rect180x100 | 3/3 | 3/3 | 11.44 | 10.63 |
| shift140 | 3/3 | 2/3 | -0.91 | 1.77 |
| east140x100 | 3/3 | 3/3 | 7.13 | 9.12 |

### Cada ronda del set

| Ronda | Puntos estimados | Válida runner | Start→fin sim (s) | Start→fin pared (s) | Margen runner (cm) | Interior auditado (cm) | Exterior auditado (cm) |
|---|---:|---|---:|---:|---:|---:|---:|
| [std12-honest-fsv4-r1-square100-ccw](20261006T193850Z-std12-honest-fsv4-r1-square100-ccw/round.json) | 30 | sí | 23.638 | 13.708 | 12.71 | 41.01 | 12.07 |
| [std12-honest-fsv4-r1-square100-cw](20261006T193940Z-std12-honest-fsv4-r1-square100-cw/round.json) | 30 | sí | 23.744 | 13.701 | 17.37 | 44.99 | 16.83 |
| [std12-honest-fsv4-r1-square180-ccw](20261006T194030Z-std12-honest-fsv4-r1-square180-ccw/round.json) | 30 | sí | 24.236 | 14.067 | 7.74 | 11.93 | 13.14 |
| [std12-honest-fsv4-r1-square180-cw](20261006T194120Z-std12-honest-fsv4-r1-square180-cw/round.json) | 30 | sí | 24.429 | 14.149 | 6.20 | 10.48 | 13.52 |
| [std12-honest-fsv4-r1-rect100x180-ccw](20261006T194211Z-std12-honest-fsv4-r1-rect100x180-ccw/round.json) | 30 | sí | 23.749 | 13.783 | 11.58 | 15.54 | 14.22 |
| [std12-honest-fsv4-r1-rect100x180-cw](20261006T194301Z-std12-honest-fsv4-r1-rect100x180-cw/round.json) | 30 | sí | 24.136 | 14.041 | 11.62 | 15.71 | 14.16 |
| [std12-honest-fsv4-r1-rect180x100-ccw](20261006T194351Z-std12-honest-fsv4-r1-rect180x100-ccw/round.json) | 30 | sí | 24.640 | 14.222 | 13.93 | 21.08 | 13.47 |
| [std12-honest-fsv4-r1-rect180x100-cw](20261006T194441Z-std12-honest-fsv4-r1-rect180x100-cw/round.json) | 30 | sí | 24.231 | 14.042 | 11.58 | 15.56 | 14.42 |
| [std12-honest-fsv4-r1-shift140-ccw](20261006T194531Z-std12-honest-fsv4-r1-shift140-ccw/round.json) | 30 | sí | 24.433 | 14.104 | 11.39 | 15.00 | 12.93 |
| [std12-honest-fsv4-r1-shift140-cw](20261006T194622Z-std12-honest-fsv4-r1-shift140-cw/round.json) | 30 | sí | 24.038 | 13.909 | 2.88 | 7.43 | 13.60 |
| [std12-honest-fsv4-r1-east140x100-ccw](20261006T194712Z-std12-honest-fsv4-r1-east140x100-ccw/round.json) | 30 | sí | 24.338 | 14.118 | 14.17 | 18.45 | 13.32 |
| [std12-honest-fsv4-r1-east140x100-cw](20261006T194802Z-std12-honest-fsv4-r1-east140x100-cw/round.json) | 30 | sí | 23.639 | 13.766 | 9.37 | 13.27 | 16.43 |
| [std12-honest-fsv4-r2-square100-ccw](20261006T194852Z-std12-honest-fsv4-r2-square100-ccw/round.json) | 30 | sí | 23.641 | 13.720 | 13.02 | 48.24 | 12.57 |
| [std12-honest-fsv4-r2-square100-cw](20261006T194942Z-std12-honest-fsv4-r2-square100-cw/round.json) | 30 | sí | 24.043 | 13.903 | 17.79 | 46.11 | 17.14 |
| [std12-honest-fsv4-r2-square180-ccw](20261006T195032Z-std12-honest-fsv4-r2-square180-ccw/round.json) | 30 | sí | 24.234 | 14.099 | 3.12 | 7.11 | 10.60 |
| [std12-honest-fsv4-r2-square180-cw](20261006T195122Z-std12-honest-fsv4-r2-square180-cw/round.json) | 30 | sí | 24.828 | 14.467 | 4.02 | 7.23 | 8.42 |
| [std12-honest-fsv4-r2-rect100x180-ccw](20261006T195213Z-std12-honest-fsv4-r2-rect100x180-ccw/round.json) | 30 | sí | 23.937 | 13.916 | 11.00 | 15.71 | 10.58 |
| [std12-honest-fsv4-r2-rect100x180-cw](20261006T195303Z-std12-honest-fsv4-r2-rect100x180-cw/round.json) | 30 | sí | 24.532 | 14.207 | 9.29 | 12.84 | 11.03 |
| [std12-honest-fsv4-r2-rect180x100-ccw](20261006T195354Z-std12-honest-fsv4-r2-rect180x100-ccw/round.json) | 30 | sí | 24.529 | 14.176 | 11.44 | 15.14 | 10.63 |
| [std12-honest-fsv4-r2-rect180x100-cw](20261006T195444Z-std12-honest-fsv4-r2-rect180x100-cw/round.json) | 30 | sí | 24.233 | 14.079 | 11.52 | 15.08 | 11.05 |
| [std12-honest-fsv4-r2-shift140-ccw](20261006T195534Z-std12-honest-fsv4-r2-shift140-ccw/round.json) | 30 | sí | 24.437 | 14.195 | 9.77 | 13.92 | 9.05 |
| [std12-honest-fsv4-r2-shift140-cw](20261006T195625Z-std12-honest-fsv4-r2-shift140-cw/round.json) | 30 | no | 24.233 | 14.111 | -0.91 | 1.77 | 13.08 |
| [std12-honest-fsv4-r2-east140x100-ccw](20261006T195715Z-std12-honest-fsv4-r2-east140x100-ccw/round.json) | 30 | sí | 24.430 | 14.220 | 12.48 | 17.27 | 11.79 |
| [std12-honest-fsv4-r2-east140x100-cw](20261006T195805Z-std12-honest-fsv4-r2-east140x100-cw/round.json) | 30 | sí | 24.338 | 14.194 | 7.13 | 11.09 | 10.52 |
| [std12-honest-fsv4-r3-square100-ccw](20261006T195856Z-std12-honest-fsv4-r3-square100-ccw/round.json) | 30 | sí | 24.431 | 14.176 | 15.12 | 52.40 | 14.32 |
| [std12-honest-fsv4-r3-square100-cw](20261006T195946Z-std12-honest-fsv4-r3-square100-cw/round.json) | 30 | sí | 24.432 | 14.190 | 15.41 | 51.58 | 14.62 |
| [std12-honest-fsv4-r3-square180-ccw](20261006T200036Z-std12-honest-fsv4-r3-square180-ccw/round.json) | 30 | sí | 24.234 | 14.048 | 5.83 | 9.53 | 12.13 |
| [std12-honest-fsv4-r3-square180-cw](20261006T200126Z-std12-honest-fsv4-r3-square180-cw/round.json) | 30 | sí | 24.342 | 14.190 | 1.22 | 5.21 | 6.69 |
| [std12-honest-fsv4-r3-rect100x180-ccw](20261006T200217Z-std12-honest-fsv4-r3-rect100x180-ccw/round.json) | 30 | sí | 24.233 | 14.038 | 11.83 | 15.72 | 11.55 |
| [std12-honest-fsv4-r3-rect100x180-cw](20261006T200307Z-std12-honest-fsv4-r3-rect100x180-cw/round.json) | 30 | sí | 24.134 | 14.069 | 7.67 | 11.97 | 10.46 |
| [std12-honest-fsv4-r3-rect180x100-ccw](20261006T200358Z-std12-honest-fsv4-r3-rect180x100-ccw/round.json) | 30 | sí | 23.941 | 13.944 | 12.45 | 15.93 | 13.12 |
| [std12-honest-fsv4-r3-rect180x100-cw](20261006T200448Z-std12-honest-fsv4-r3-rect180x100-cw/round.json) | 30 | sí | 24.340 | 14.130 | 12.80 | 16.59 | 13.02 |
| [std12-honest-fsv4-r3-shift140-ccw](20261006T200538Z-std12-honest-fsv4-r3-shift140-ccw/round.json) | 30 | sí | 24.232 | 14.085 | 7.08 | 11.35 | 11.51 |
| [std12-honest-fsv4-r3-shift140-cw](20261006T200628Z-std12-honest-fsv4-r3-shift140-cw/round.json) | 30 | sí | 24.234 | 14.060 | 10.90 | 14.77 | 10.37 |
| [std12-honest-fsv4-r3-east140x100-ccw](20261006T200719Z-std12-honest-fsv4-r3-east140x100-ccw/round.json) | 30 | sí | 24.338 | 14.158 | 15.09 | 19.73 | 14.27 |
| [std12-honest-fsv4-r3-east140x100-cw](20261006T200809Z-std12-honest-fsv4-r3-east140x100-cw/round.json) | 30 | sí | 23.940 | 13.881 | 8.16 | 11.89 | 9.12 |

### Interpretación y pendientes

El único rechazo es [shift140 CW, repetición 2](20261006T195625Z-std12-honest-fsv4-r2-shift140-cw/round.json):
24,233 s sim / 14,111 s de pared desde Start, 30 puntos estimados,
margen interior circular −0,91 cm y sin contactos registrados. Sus disparadores
frontales después del primer giro tienen `dist` de 1,07–1,38 m; no aparece el
disparo prematuro a menos de 0,6 m observado en v2.
La [auditoría de chasis y ruedas](20261006T195625Z-std12-honest-fsv4-r2-shift140-cw/honest-fsv4-margin-audit.json)
da 1,77 cm interiores (rueda trasera derecha, TURN con 11 giros completados,
sim 22,635 s) y 13,08 cm exteriores. Es la menor separación auditada de todo
el set. No se sobrescribe el rechazo original ni se infiere contacto del
valor negativo de la aproximación circular.

El runner calcula la separación interior con un círculo conservador de radio
0,102 m y la exterior con un rectángulo aproximado. Se conserva ese método
para no alterar los registros ni la comparación original. La auditoría aparte
reutiliza `race-tuning-driver/v6_margin_audit.py` (borrado el 9 oct 2026 con el trabajo no honesto; en el historial de git hasta `1f950d1`), verifica el URDF archivado
y proyecta chasis y ruedas con ambos ángulos de dirección medidos.

Cada ronda tiene `honest-fsv4-margin-audit.json` y `honest-fsv4-margin-trace.json`;
[resumen conjunto](honest-fsv4-margin-audits.json). Los márgenes auditados son
muestreados, con pose y articulaciones asíncronas; no certifican ausencia de
contacto entre muestras. Los sensores de contacto y el juez se conservan aparte.

La corrección mejora square100 frente al 5/8 de v2. Los rechazos de margen
del set requieren considerar la geometría exacta antes de cambiar la estrategia.
No se promociona como perfil final: falta validar el candidato con GUI,
resolver el criterio geométrico del runner y medir el servo real.
