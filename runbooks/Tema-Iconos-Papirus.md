# Tema de iconos del sistema → Papirus (logos por lenguaje)

Documentado el 2026-07-24. Equipo: Mac Mini con CachyOS. Usuario: `ermesbatista`.

**Problema:** los archivos de código (`.py`, `.js`, etc.) se veían todos con el mismo
ícono genérico de "documento de texto", sin distinción por lenguaje.

**Causa:** el tema de iconos por defecto era **Adwaita**, que es minimalista *a propósito*
y NO trae logos por lenguaje. Las extensiones y tipos MIME del sistema ya estaban bien;
lo que faltaba era un tema de iconos con logos por MIME.

**IMPORTANTE:** este equipo usa **Hyprland** (no GNOME ni KDE como escritorio), pero los
file managers instalados son **Nautilus** (GTK) y **Dolphin** (KDE), así que hay que
configurar el tema de iconos en **ambos** backends.

---

## 1. Instalar Papirus

```bash
sudo pacman -S --needed papirus-icon-theme
```
(~110 MiB instalado, desde repos oficiales `extra/`.)

---

## 2. Aplicar el tema en GTK (Nautilus)

```bash
gsettings set org.gnome.desktop.interface icon-theme 'Papirus'
```
Verificar:
```bash
gsettings get org.gnome.desktop.interface icon-theme    # -> 'Papirus'
```

---

## 3. Aplicar el tema en KDE (Dolphin)

```bash
kwriteconfig6 --file kdeglobals --group Icons --key Theme Papirus
```
Esto crea/edita `~/.config/kdeglobals`:
```ini
[Icons]
Theme=Papirus
```

---

## 4. Refrescar

```bash
nautilus -q      # cierra Nautilus; al reabrirlo toma el tema nuevo
```
Si algún archivo sigue genérico, cerrar y reabrir la ventana del file manager.

---

## Detalle técnico (trampa a recordar)

- `xdg-mime query filetype archivo.py` reporta `text/x-script.python`, pero **Nautilus
  usa `gio`**, que lo resuelve al MIME real `text/x-python`.
- Papirus tiene `text-x-python.svg` (el logo de Python) en
  `/usr/share/icons/Papirus/48x48/mimetypes/`, así que el `.py` muestra el logo correcto.
- Si un tipo raro sale genérico, es que Papirus no mapea ese MIME: se agrega un SVG en
  `~/.local/share/icons/` o se crea un alias en shared-mime-info.

Papirus trae logos para: Python, JS, JSON, HTML, CSS, Rust, Go, C, Java, Markdown, y muchos más.

---

## Resumen rápido

| Backend | Comando |
|---|---|
| GTK / Nautilus | `gsettings set org.gnome.desktop.interface icon-theme 'Papirus'` |
| KDE / Dolphin | `kwriteconfig6 --file kdeglobals --group Icons --key Theme Papirus` |
| Instalar | `sudo pacman -S --needed papirus-icon-theme` |

> Ambos cambios son permanentes (sobreviven reinicio): quedan en `gsettings` (dconf) y en
> `~/.config/kdeglobals`. Opcional: `papirus-folders` para cambiar el color de las carpetas.
