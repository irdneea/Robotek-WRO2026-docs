# Arranque automático del stack (desactivado el 9 oct 2026)

Copia de lo que había en el Pi (`user@192.168.0.10`). **Desde el 9 oct 2026 el stack ya no
arranca solo al encender**: se desactivó el servicio de usuario y se dejaron todos los archivos
en su sitio, para volver a activarlo más adelante con un modo (`open` u `obstacle`).

| Archivo (en el Pi) | Copia aquí | Qué es |
|---|---|---|
| `~/.config/systemd/user/ros_autostart.service` | [ros_autostart.service](ros_autostart.service) | servicio de usuario (`WantedBy=default.target`, `Restart=on-failure`); con *linger* activado arrancaba al encender, sin iniciar sesión |
| `~/scripts/ros_autostart.sh` | [ros_autostart.sh](ros_autostart.sh) | lee `~/.config/wro_mode` y lanza el stack del modo |
| `~/.config/wro_mode` | — (contenía `obstacle`) | modo: `open` (`~/Documents/Testv1/open/run_open.sh`) u `obstacle` (`ros2 launch rrc_lite_driver wro.launch.py`) |
| `~/scripts/stop_ros.sh` | [stop_ros.sh](stop_ros.sh) | detiene el servicio y mata el stack; sigue sirviendo para parar nodos lanzados a mano |

## Qué se hizo

```bash
systemctl --user disable --now ros_autostart.service
```

Solo eso: quitó el enlace en `~/.config/systemd/user/default.target.wants/` y detuvo el servicio.
La unidad, el script, `wro_mode` y `stop_ros.sh` **no se tocaron**. *Linger* sigue activado (no
hace nada sin servicios habilitados).

Otros mecanismos revisados que **no** lanzan el stack ahora: `/etc/rc.local` (ejecutable, pero
`rc-local.service` aparece *failed*; en teoría arrancaría `rrc_driver`, el LiDAR y
`acker_lidar_controller`), `my_ros_service.service` (del sistema, habilitado pero inactivo) y
`ros_wro.service` (del sistema, deshabilitado). Los de sistema necesitan `sudo` y no se tocaron.

## Volver a activarlo (cuando se decida)

1. Elegir el modo: `echo open > ~/.config/wro_mode` o `echo obstacle > ~/.config/wro_mode`.
2. Habilitarlo para el siguiente encendido y arrancarlo ahora:

```bash
systemctl --user enable --now ros_autostart.service
```

3. Para pararlo de nuevo sin quitar el arranque: `~/scripts/stop_ros.sh` (o
   `systemctl --user stop ros_autostart.service`); para quitarlo otra vez:
   `systemctl --user disable --now ros_autostart.service`.

**Ojo:** el modo `obstacle` lanza `wro.launch.py`, que incluye `acker_node` y `motor`: el coche
puede moverse nada más arrancar. Y no se puede correr a la vez que nuestros launch
(`robot.launch.py`, `sensors.launch.py`): comparten LiDAR, cámara y placa.
