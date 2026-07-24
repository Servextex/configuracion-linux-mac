#!/usr/bin/env bash
# Copiar/pegar estilo macOS con Cmd (Super). Manda Ctrl+C/V a las apps normales; en la TERMINAL
# manda Ctrl+Shift+C/V (para que copie/pegue de verdad, dejando Ctrl+C = interrumpir intacto).
# Uso: mac-clip.sh copy | paste   (lo llaman los binds de Hyprland)

cls=$(hyprctl activewindow -j 2>/dev/null | jq -r '.class // ""')

term=0
case "$cls" in
    kitty|Alacritty|alacritty|foot|org.wezfurlong.wezterm|com.mitchellh.ghostty|konsole) term=1 ;;
esac

case "$1" in
    copy)  key=c ;;
    paste) key=v ;;
    *)     exit 0 ;;
esac

if [ "$term" = 1 ]; then
    hyprctl dispatch "hl.dsp.send_shortcut({ mods = \"CTRL SHIFT\", key = \"$key\", window = \"activewindow\" })" >/dev/null 2>&1
else
    hyprctl dispatch "hl.dsp.send_shortcut({ mods = \"CTRL\", key = \"$key\", window = \"activewindow\" })" >/dev/null 2>&1
fi
