# Mallas de montaje (no van a git)

Exportadas de SolidCraft desde `Assembly3.stp` (abierto con `up: y`, nombres por producto), en mm y en el sistema de
SolidCraft (el render las gira 180° en z y las pone en `(mesh_x, 0, mesh_z)` del URDF). Para regenerarlas, exporta
con la herramienta `export` de SolidCraft los cuerpos:

| Archivo | Cuerpos |
|---|---|
| `rrc_lite.stl` | la segunda «Raspberry Pi 5 v1 (… Raspberry Pi 5 v1:2)» (9 cuerpos), la placa del otro lado de la caja |
| `ld19_head.stl`, `ld19_body.stl` | `LD19_up`; `LD19_bottom`, `LD19_middle`, `LD19_PCB` |
| `screws_lidar.stl` | `PA2X6_1` a `_4` |
| `screws_pi.stl`, `nuts_pi.stl` | los M2×10 (1)…(:4) y las tuercas M2 (1), (:2), (:6), (:7) (lado del Pi) |
| `screws_rrc.stl`, `nuts_rrc.stl` | el M2×14 y los M2×10 (:5)…(:7); las tuercas M2 (:3), (:4), (:5), (:8) |
| `screws_cam.stl`, `nuts_cam.stl` | los dos M1.6×16 y sus tuercas |
| `one_*.stl` | un tornillo o tuerca de cada tipo, para las miniaturas |
