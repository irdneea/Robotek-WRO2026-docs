> Registro histórico del juez v1 a 10 Hz. Consultar la [revisión actual](realcar-open-history.md) para los puntos corregidos.

# Historial de mejores rondas Open con el coche real

8 de octubre de 2026. Este historial conserva las mejoras sucesivas; no se borra
una ronda al reemplazarla. Se mantienen contextos separados por **campo, modelo,
sentido y GUI**. Aquí todos son square100 y `real_car_v1`, motor limitado al 100 %
PWM y dirección equivalente ±17,6°. Primero puntos; con igual puntuación, tiempo
**total desde Start**. Solo se promocionan rondas que pasan la validación.

[Mejor ronda GUI actual y motivo de elección](best-realcar-open-round-judge-v1.md).
[Todos los intentos y comparación estándar](realcar-open-validation.md).
[Cómo correr las pruebas](../guia-correr-open-v4.md#coche-real-y-registro-de-mejoras).
Los parámetros exactos y el código se conservan en `source/` de cada ejecución.
Las promociones de una ronda no acreditan robustez general del perfil.

## Mejoras sucesivas observadas

| Ejecución y evidencia | Contexto | Puntos estimados | Start → fin sim (s) | Mejor anterior | Hallazgo |
|---|---|---:|---:|---|---|
| [realcar-symmetric-tune2-sq100-ccw](20261008T044430Z-realcar-symmetric-tune2-sq100-ccw/round-judge-v1.json) | CCW / sin GUI | 30 | 34.676 | primera válida del contexto | Carril más corto, frenada de la última curva y espera antes de DONE: primera parada válida. |
| [realcar-symmetric-tune6-sq100-ccw](20261008T045035Z-realcar-symmetric-tune6-sq100-ccw/round-judge-v1.json) | CCW / sin GUI | 30 | 33.716 | 34.676 s | Extremo LiDAR conectado, nueva habilitación de curva y arco calculado con velocidad real. |
| [realcar-symmetric-tune8-sq100-ccw](20261008T045413Z-realcar-symmetric-tune8-sq100-ccw/round-judge-v1.json) | CCW / sin GUI | 30 | 30.516 | 33.716 s | Anticipación moderada y escala propia de la última curva: conserva todas las secciones. |
| [realcar-symmetric-tune10-gui-sq100-ccw](20261008T045825Z-realcar-symmetric-tune10-gui-sq100-ccw/round-judge-v1.json) | CCW / GUI | 30 | 30.016 | primera válida del contexto | Iniciar la frenada antes de terminar el arco ahorra tiempo; margen final justo por mantener dirección al frenar. |
| [realcar-symmetric-tune12-sq100-cw](20261008T050440Z-realcar-symmetric-tune12-sq100-cw/round-judge-v1.json) | CW / sin GUI | 30 | 34.017 | primera válida del contexto | Margen frontal obligatorio elimina atajos de esquina; primera CW válida de esta serie. |
| [realcar-symmetric-tune13-sq100-cw](20261008T050707Z-realcar-symmetric-tune13-sq100-cw/round-judge-v1.json) | CW / sin GUI | 30 | 30.217 | 34.017 s | Menor amortiguación y salida de arco más rápida, con anticipación protegida: reduce tiempo conservando margen. |
| [realcar-symmetric-tune14-gui-sq100-cw](20261008T050840Z-realcar-symmetric-tune14-gui-sq100-cw/round-judge-v1.json) | CW / GUI | 30 | 30.080 | primera válida del contexto | Margen frontal obligatorio y servo controlado durante la frenada; más margen que tune10. |
| [realcar-symmetric-tune15-gui-sq100-cw](20261008T051135Z-realcar-symmetric-tune15-gui-sq100-cw/round-judge-v1.json) | CW / GUI | 30 | 29.714 | 30.080 s | Tres imágenes independientes a 6 fps y frenada con servo activo; comprobar repetibilidad en ambos sentidos. |

## Lo que funcionó

- **Motor saturado al 100 % PWM**: evita atribuir al coche velocidades obtenidas
  por extrapolar más allá del máximo de motor. Se aplica después de la rampa,
  como en el hardware; no subir ese límite para lograr el tiempo objetivo.
- **Plugin con ganancia 20**: sigue el servo medido. Ganancia 1 añade lentitud
  artificial. El ángulo equivalente sigue limitado a ±17,6° en los dos lados.
- **Arco a velocidad real**: 1,28 m/s de comando equivale a 0,60 m/s del modelo;
  la última curva usa 0,60 → 0,42. El tiempo del arco no debe usar el comando
  como si fuera velocidad real.
- **Extremo de muro observable y conectado**: separar el tramo de isla de rayos
  del muro exterior; devolver desconocido si sigue fuera de la ventana.
- **Habilitar curvas en rectas cortas**, conservando la evidencia del extremo
  interior y el margen frontal. Las curvas deben cruzar las ocho secciones con
  toda la carrocería, no simplemente acumular giros.
- **Frenada con dirección activa**: un Twist dentro de la banda muerta del
  motor permite comandar el servo mientras el motor baja a cero; la banda
  muerta se modela igual que en `base_adapter`.
- **Cámara a 6 fps**: tres imágenes independientes coherentes reducen la espera
  respecto a cinco. Mantener detección automática, rechazo de conflicto con
  LiDAR y rechazo de imágenes antiguas; nunca fijar el sentido para ganar tiempo.

## Lo que no funcionó y por qué

- **Perfil del servo rápido sin adaptar**: recorrido exterior largo, frenada
  insuficiente y vueltas lentas con el motor real. Primer diagnóstico nuevo
  además usó ganancia 1. La ronda anterior de 43,831 s tenía 27 puntos, no era válida.
- **Anticipación 0,38 m sin arreglar la percepción (tune3)**: se confundía el
  borde de la ventana de rayos con el extremo de la isla; giró contra ella.
- **Ampliar la ventana sin separar tramos (tune4)**: rayos del muro exterior
  casi sobre la recta de la isla alargaban falsamente el muro.
- **Acortar demasiado el carril/las curvas (tune5, tune7, tune9, tune11)**:
  puede completar tres vueltas aparentes y llegar a DONE pronto, pero la huella
  no entra completa en varias secciones de esquina; el juez descarta el máximo.
  Tune9 GUI hizo DONE a 29,496 s, pero solo obtuvo 15 puntos. Tune11 CW, 9 puntos.
- **Parar el comando sin esperar la frenada**: el motor sigue avanzando y el
  juez no valida la deriva/parada; puede salirse de la sección de llegada.
- **Primera repetición GUI CCW del perfil final**: obtuvo 18 puntos y solo dos
  vueltas puntuables; DONE con doce giros no aseguró cruzar todas las secciones.
  Su evidencia está en la tabla de validación.
- **Dejar la dirección fija al frenar (tune10)**: dio una ronda válida pero con
  solo 1,99 cm de margen final; no es la opción preferida para repetibilidad.

Cada fallo conserva su `round.json` y ledger. El intento bloqueado por sockets
UDP del sandbox no arrancó y no proporciona puntos ni tiempos medibles.
