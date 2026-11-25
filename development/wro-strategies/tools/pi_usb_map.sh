#!/usr/bin/env bash
# Mapa de USB del Pi 5: qué dispositivo cuelga de qué controlador xHCI, a qué velocidad y con
# qué nombre estable. Solo lectura. Se corre en el Pi, o desde el Mac:
#   ssh user@192.168.0.10 'bash -s' < tools/pi_usb_map.sh
# Para saber qué puerto físico es cada controlador: enchufar UN dispositivo en un puerto, correrlo,
# y anotar el controlador (xhci-hcd.0 o .1) y la fila (bus/puerto); repetir en los 4 puertos.
printf '%-6s %-10s %-6s %-11s %s\n' PUERTO USB_ID MB/s CONTROLADOR PRODUCTO
for d in /sys/bus/usb/devices/[0-9]*-[0-9]*; do
  name=$(basename "$d"); case "$name" in *:*|*.*) continue ;; esac
  [ -f "$d/idVendor" ] || continue
  ctrl=$(readlink -f "$d" | grep -o 'xhci-hcd\.[0-9]' | head -1)
  printf '%-6s %-10s %-6s %-11s %s\n' "$name" "$(cat "$d/idVendor"):$(cat "$d/idProduct")" \
    "$(cat "$d/speed")" "${ctrl:-?}" "$(cat "$d/product" 2>/dev/null)"
done
echo
echo "Nombres estables (no cambian con el puerto):"
ls -l /dev/serial/by-id /dev/v4l/by-id 2>/dev/null | grep -- '->' | awk '{print "  " $9 " -> " $11}'
echo
echo "Corriente: fuente $(( $(xxd -p /proc/device-tree/chosen/power/max_current 2>/dev/null | head -c 8 | sed 's/^/0x/') )) mA, $(vcgencmd get_config usb_max_current_enable 2>/dev/null)"
