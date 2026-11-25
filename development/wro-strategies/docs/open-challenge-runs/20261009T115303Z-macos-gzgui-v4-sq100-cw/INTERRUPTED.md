# Ronda que no llegó a arrancar (Gazebo con ventana en macOS)

Intento con la ventana de Gazebo (`run_gui_experiment.sh` sin `--no-gui`), macOS RoboStack,
9 oct 2026. `gz sim` sin `-s` ni `-g` se cierra en macOS: "On macOS `gz sim` currently only
works with either the -s argument or the -g argument"
([gz-sim#44](https://github.com/gazebosim/gz-sim/issues/44)). Sin simulador no hubo scans ni
Start; se detuvo a mano. Sin puntos ni línea en `rounds.jsonl`.
