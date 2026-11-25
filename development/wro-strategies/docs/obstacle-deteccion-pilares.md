# Detección de pilares: código del equipo frente al nuestro

8 de octubre de 2026. Compara cómo detecta y esquiva los pilares el código del equipo
(`Robotek-WRO2026/src/obstacle/`, submódulo en `96198af`) con nuestra estrategia
(`src/robotek_obstacle/`), y explica qué hace hoy el detector en el coche real.

## Código del equipo: solo cámara, reactivo

| Paso | Detalle |
|---|---|
| Color (`color_vision.py`) | HSV con desenfoque 5×5. Rojo H 0–13 ∪ 169–180, S ≥ 80, V ≥ 50; verde H 53–89, S ≥ 25, V ≥ 25. Apertura y cierre 7×7 |
| Filtro | Área ≥ 650 px, relleno del recuadro ≥ 42 %, proporción ≤ 2,6 |
| Elección | **Un solo bloque**: el de base más baja en la imagen (`base_norm`), tomado como el más cercano |
| Confirmación | 3 frames seguidos del mismo color |
| Esquiva (`control.py`) | El color elige la pared a seguir: **rojo → derecha, verde → izquierda**, a 18 cm. Con la base pasada la mitad de la imagen suma un giro de rumbo de hasta ±12° alejándose del bloque |
| LiDAR | Solo pared (rayos a 30° y 60°) y esquinas; **no participa en los pilares** |
| Velocidad | 35 % fija |

Limitaciones:

- Cualquier mancha del color pasa como pilar. Con el piso de madera del campo real, el
  rojo toma el piso y el zócalo ([robot-real-pi.md](robot-real-pi.md#colores-hsv-en-el-coche-real)).
- La distancia sale de la altura en la imagen, no de una medida.
- Ve un bloque a la vez: no puede planear entre dos pilares seguidos.
- No recuerda los pilares: si el pilar sale de la imagen al acercarse, deja de esquivarlo.

## Nuestra estrategia: cámara + LiDAR, mapa y planificador

| Paso | Archivo | Detalle |
|---|---|---|
| Grupos del LiDAR | `obstacle_perception.scan_clusters` | Grupos cortos y aislados de 1,5–12 cm a menos de 2,5 m; las paredes quedan fuera. Corrige el punto al centro del pilar de 5 cm |
| Manchas de color | `obstacle_perception.color_blocks` | De cada mancha calcula el **ángulo** con el HFOV, la inclinación y el giro de la cámara |
| Asociación | `obstacle_perception.associate` | Una mancha solo es pilar si coincide en ángulo (±0,12 rad, ~7°) con un grupo del LiDAR. Si dos colores apuntan al mismo grupo, se descarta. **Posición del LiDAR, color de la cámara** |
| Mapa | `obstacle_seat_map.SeatMap` | Los pilares solo pueden estar en los 24 lugares del reglamento. Acumula hits del LiDAR y votos de color por lugar; confirma con ≥ 3 hits o ≥ 2 votos y como mucho un pilar por par de filas. **Los recuerda entre vueltas** |
| Localización | `obstacle_localizer.Localizer` | Ajusta los puntos del LiDAR a las paredes conocidas, con giroscopio y odometría por LiDAR (sin encoder) |
| Plan | `obstacle_beam_planner.BeamPlanner` | Busca secuencias de dirección con el modelo bicicleta; comprueba la carrocería contra paredes, isla y pilares, y exige pasar del lado del color, también al retroceder (`wrong_side`) |

Resultados en simulación honesta (solo sensores con ruido), perfil `obstacle_sensors_v1`
([next-steps.md](next-steps.md#obstacle-challenge-sin-aparcar)): 10/10 rondas con 40 puntos
estimados, media 72,4 s, sin contactos, pero solo 5/10 válidas por pasar a menos de 1 cm de
muros o pilares. Con GUI, reg0 CCW y CW válidas (64,3 y 79,9 s).

## En el coche real: `sensors.launch.py detector:=true`

```bash
~/scripts/stop_ros.sh
export ROS_DOMAIN_ID=1
source ~/wro_controller_ws/install/setup.bash
source ~/Projects/WRO-Strategies/install/setup.bash
ros2 launch peripherals sensors.launch.py          # detector:=true es el valor por defecto
```

Comandos de RViz en la Mac y cómo detenerlo:
[robot-real-pi.md](robot-real-pi.md#ver-los-sensores-en-rviz-desde-la-mac-robostack).

### Qué funciona

A los 8 s del arranque se lanzan `scan_adapter` (LD19 → `/robotek/scan`, 0 rad adelante,
solo ±110°) y `obstacle_detector`. El detector usa las mismas funciones que la estrategia
(`color_blocks` + `scan_clusters` + `associate`), con:

- Colores medidos en el coche: rojo H 0–4 ∪ 172–179, S ≥ 170, V ≥ 110; verde H 56–90,
  S ≥ 150, V ≥ 50; área ≥ 150 px. Se pueden cambiar en vivo con
  `ros2 param set /obstacle_detector <nombre> <valor>`.
- Cámara medida tras reapuntarla (`bf155c2`): HFOV 1,164 rad, inclinación 0,17 rad, giro
  0,077 rad, pasados por el launch.

Publica:

| Tópico | Qué se ve |
|---|---|
| `/obstacle/markers` | Cilindro rojo o verde con distancia por pilar asociado; línea por mancha de color; punto gris por grupo del LiDAR del tamaño de un pilar |
| `/obstacle/debug_image/compressed` | Imagen con recuadros (gruesos = asociados con el LiDAR), conteo y decisión DERECHA / IZQUIERDA / CENTRO |
| `/obstacle/steer` | Lado de paso del pilar más cercano (rojo −25°, verde +25°); solo mueve el servo con `servo:=true` |

Comprobación en RViz: la línea de color de la cámara debe pasar por el punto gris del LiDAR
y aparecer el cilindro. Si hay línea y punto pero no cilindro, la cámara está mal
calibrada (giro o HFOV) o la imagen y el scan no están sincronizados (±0,15 s; la imagen
muestra "sin scan sincronizado").

### Qué no hace

- **No maneja.** No lanza el motor ni `acker_node`. Con `servo:=true` solo mueve el servo
  hacia el lado de paso.
- **No es la estrategia completa.** Detecta cuadro a cuadro: no hay mapa de lugares, ni
  localización, ni planificador. Eso solo corre en `obstacle_strategy`.
- **Si no hay asociación, decide solo con la cámara** (el recuadro más alto) para la
  prueba del servo. En esa vía una mancha falsa puede mover el servo.

### Pendiente

- **`obstacle_strategy` todavía usa los rangos HSV de la simulación** (`SIM_COLOR_RANGES`;
  `obstacle_strategy_node.py` llama a `color_blocks` sin `ranges`). La geometría de la
  cámara real sí le llega con `real_car:=true` y `robot.launch.py`. Hay que pasarle los
  colores del coche antes de correrla en el campo real.
- **Rojo en sombra:** el pilar (V 34–61) no se separa del zócalo (V 1–46) por color.
  Opciones: más luz (tira LED con alimentación propia), exposición manual de la cámara, o
  apoyarse en la asociación con el LiDAR.
- Probar la estrategia completa en el campo real. Hasta ahora solo se probaron el
  detector y el servo por color, con el coche quieto.
- Confirmar en el Pi que el launch y el detector instalados son los de la repo (se copia
  con `rsync`, y la instalación de `colcon` es una copia: recompilar tras copiar).

## Explicación simple (método Feynman)

**Antes (código del equipo).** Imagina que manejas mirando solo por una ventanita y sin
memoria. Ves una mancha roja y piensas "hay un pilar rojo; si está abajo en la ventanita,
está cerca, así que me pego a la pared derecha y giro un poco". Pero no sabes si la mancha
es un pilar o el piso de madera, no sabes a cuántos centímetros está, solo miras una mancha
a la vez y, cuando el pilar sale de la ventanita, te olvidas de que estaba ahí.

**Ahora (nuestra estrategia).** Son dos amigos que se ayudan: uno tiene **ojos** (la
cámara) y ve colores pero no distancias; el otro tiene un **bastón** (el LiDAR) y toca
objetos y sabe exactamente dónde están, pero no ve colores. Solo dicen "hay un pilar" cuando
los dos señalan al mismo sitio: así una mancha en el piso no cuenta, porque el bastón no
toca nada ahí. Además llevan un **mapa del campo** con los 24 lugares donde puede haber
pilares y van anotando lo que encuentran, así que en la segunda y tercera vuelta ya saben
dónde está todo aunque no lo vean. Con ese mapa y sabiendo dónde están ellos mismos (por
las paredes), **planean el camino completo** antes de moverse, comprobando que el coche
pase sin tocar nada y por el lado correcto de cada color.

**En una frase:** antes el coche *reaccionaba* a una mancha de color; ahora *confirma* cada
pilar con dos sensores, lo *recuerda* en un mapa y *planea* por dónde pasar.

**Lo que falta, igual de simple:** en el coche real, los "ojos" del detector ya están
ajustados al piso de madera, pero los de la estrategia completa todavía usan los colores de
la simulación; y en sombra el rojo se confunde con el zócalo.
