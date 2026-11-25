# Identificación de la dirección de Gazebo para el Open lab

Pasos (todo en `/tmp/v5/id`, ver `docs/open-lab.md`):

```bash
source tools/macos_env.sh; source install/setup.sh
python3 - <<'PY'      # campo vacío (solo suelo)
import xml.etree.ElementTree as ET
t = ET.parse('docs/open-challenge-runs/field-size-driver/worlds/square100.sdf'); w = t.getroot().find('world')
[w.remove(m) for m in w.findall('model') if m.get('name') == 'game_field']
t.write('/tmp/v5/id/empty.sdf')
PY
mkdir -p /tmp/v5/id/out
ros2 launch tools/open_lab/steer_id.launch.py &        # Gazebo sin GUI + modelo de actuadores + audit_pose_recorder
sleep 25; python3 tools/open_lab/steer_id_drive.py     # escalones de dirección a 50 Hz; escribe /tmp/v5/id/cmd.csv
python3 tools/open_lab/steer_id_fit.py                 # ajusta retardo, velocidad y filtro del servo
```
