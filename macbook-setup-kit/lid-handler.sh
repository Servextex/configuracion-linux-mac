#!/usr/bin/env bash
# Handler de tapa (lo lanza Hyprland autostart). El sistema NUNCA suspende (cuelga el GPU AMD).
#   Cerrar tapa → pantalla off + teclado off + GPU AMD 'low' + WiFi off + Bluetooth off.
#   Abrir tapa  → restaura todo al instante.
#   Cerrada 5 min → apagar limpio (bag-safe).
# La Touch Bar NO se toca (se apaga sola por inactividad; forzarla es riesgoso, §8/§15).

KBD="spi::kbd_backlight"
GPU=/sys/class/drm/card1/device/power_dpm_force_performance_level
TIMEOUT=300          # 5 minutos
POLL=3

lid_state() { cat /proc/acpi/button/lid/*/state 2>/dev/null | awk '{print $2}' | head -1; }
dpms()      { hyprctl dispatch "hl.dsp.dpms(\"$1\")" >/dev/null 2>&1; }

prev="open"
closed_at=0
kbd_save=0

while true; do
    st="$(lid_state)"
    now="$(date +%s)"

    if [ "$st" = "closed" ] && [ "$prev" = "open" ]; then
        kbd_save="$(brightnessctl -d "$KBD" get 2>/dev/null)"
        dpms off
        brightnessctl -d "$KBD" set 0 >/dev/null 2>&1
        echo low > "$GPU" 2>/dev/null
        nmcli radio wifi off 2>/dev/null
        rfkill block bluetooth 2>/dev/null
        closed_at="$now"
    elif [ "$st" = "open" ] && [ "$prev" = "closed" ]; then
        dpms on
        brightnessctl -d "$KBD" set "${kbd_save:-0}" >/dev/null 2>&1
        echo auto > "$GPU" 2>/dev/null
        nmcli radio wifi on 2>/dev/null
        rfkill unblock bluetooth 2>/dev/null
        closed_at=0
    fi

    if [ "$st" = "closed" ] && [ "$closed_at" -gt 0 ] && [ $((now - closed_at)) -ge "$TIMEOUT" ]; then
        # antes de apagar: dejar todo en estado "normal" para que lo que systemd guarda al
        # apagar (y restaura al encender) sea el estado ON, no el apagado de la tapa cerrada.
        #   - WiFi/BT: si no, NetworkManager/systemd-rfkill guardan "apagado" → arrancan apagados.
        #   - Teclado: systemd-backlight guarda el brillo del kbd; si queda en 0 → arranca sin luz
        #     y hay que subirlo a mano tras loguearse. Se restaura a su valor previo (kbd_save).
        nmcli radio wifi on 2>/dev/null
        rfkill unblock bluetooth 2>/dev/null
        brightnessctl -d "$KBD" set "${kbd_save:-0}" >/dev/null 2>&1
        sleep 2                     # dejar que los estados "on" se persistan antes del apagado
        systemctl poweroff
    fi

    [ -n "$st" ] && prev="$st"
    sleep "$POLL"
done
