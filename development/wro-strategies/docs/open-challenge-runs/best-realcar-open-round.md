# Mejor ronda Open validada con `real_car:=true`

Registro del 8 de octubre de 2026. Mejor **ronda observada con GUI** en
**square100**, motor limitado al 100 % PWM y dirección simétrica equivalente
±17,6°. Es una selección de evidencia individual; la robustez de un perfil
se evalúa por separado con el set estándar y repeticiones.

## Ronda elegida

- Ejecución: [20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/round.json).
- Puntos: **30/30 estimados**. Puntuación oficial: desconocida.
- Tiempo desde Start: **29.312 s de Gazebo / 29.775 s de pared**.
- Sentido **CW**, detectado automáticamente por cámara y LiDAR.
- Validación estándar: **válida**; sin contactos ni faltas registradas.
- Margen mínimo muestreado: **6.36 cm** (comfortable).
- Parada observada: **34.700 s**; deriva: **1.583 mm**.

## Por qué es la mejor

Primero se compara la puntuación y después el **tiempo total desde Start**,
incluyendo calibración, detección de sentido y frenada. Esta ronda obtuvo el
máximo estimado, pasó todos los controles de validación y es la más rápida de
las rondas GUI válidas revisadas en este contexto. Los intentos que llegan a
DONE más pronto pero omiten secciones completas se descartan.

**Objetivo de menos de 30 s alcanzado en esta ronda.**
Una sola ronda no demuestra repetibilidad con ruido. Los resultados del servo
rápido de octubre 6–7 corresponden a otro motor y sensores y no se mezclan aquí.

**Historial de mejoras, qué funcionó y qué falló:**
[realcar-open-history.md](realcar-open-history.md).
Todos los diagnósticos y la validación del set estándar:
[realcar-open-validation.md](realcar-open-validation.md).

## Reproducir esta configuración

Usar la copia de parámetros de la ejecución, porque el candidato activo puede
seguir cambiando. La copia del código Open está en [20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/source/](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/source/).
Restaurar ese código en una copia de trabajo y compilar antes de ejecutar:
los parámetros solos no reproducen cambios de estrategia posteriores.
La estrategia de tune11 precede a la guardia frontal obligatoria del candidato actual.
Con ruido, el tiempo no será idéntico.

```bash
source /opt/ros/jazzy/setup.zsh
colcon build
source install/setup.zsh
bash src/robotek_evaluation/tools/run_gui_experiment.sh best-realcar-open-replay \
  --params-file docs/open-challenge-runs/20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/source/profile.yaml \
  --world docs/open-challenge-runs/field-size-driver/worlds/square100.sdf \
  --direction cw --controller-direction auto --spawn-y -1.15 \
  --ackermann-velocity-limit 4.0 --ackermann-steer-p-gain 20 \
  --launch-arg real_car:=true
```

Evidencia: [round.json](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/round.json), [juez](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/rule_judge.json),
[manifest](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/manifest.json), [pose de auditoría a 50 Hz](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/audit_pose.csv), [telemetría](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/telemetry.csv),
[contactos](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/contacts.jsonl), [parámetros](20261008T050125Z-realcar-symmetric-tune11-gui-sq100-cw/source/profile.yaml).
El modelo del motor y su calibración se conservan también en `source/` de la
ronda elegida. Scans, cámara y logs crudos se conservan localmente. La pose de Gazebo solo se
usa para auditar. Las vueltas parciales están en `round.json`.

## Límites

Motor `real_car_v1`: batería baja; 0,60 m/s al 100 % es inferido, pendiente de
medir con batería cargada. Tiempo objetivo en el reloj de simulación. Márgenes
muestreados y puntos estimados, no oficiales. Ángulo equivalente ±17,6° del
modelo bicicleta: la rueda interior Ackermann puede llegar a ~19,86°; sigue
bajo el límite de ±25°. El objetivo no se extiende a todas las geometrías del
set: square180 necesita al menos 36 s incluso sin calibración ni carrocería.
