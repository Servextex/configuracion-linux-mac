# Web-apps (WhatsApp, Google Keep, Apple Notes) como aplicaciones — Chrome

Documentado el 2026-07-21. Equipo: Mac Mini con CachyOS (Hyprland + Noctalia). Usuario: `ermesbatista`.

**Objetivo:** convertir tres sitios web en **aplicaciones independientes** (ventana propia, sin
barra de navegador, con su ícono en el dock/lanzador), usando **Google Chrome en modo `--app`**.

- **WhatsApp** → `https://web.whatsapp.com/`
- **Google Keep** → `https://keep.google.com/`
- **Apple Notes (iCloud)** → `https://www.icloud.com/notes`

---

## 1. Iconos (generados localmente, sin descargar nada)

Se crearon con SVG → PNG usando `rsvg-convert`. Viven en `~/.local/share/icons/`:
- `webapp-whatsapp.svg` / `.png`  (verde WhatsApp)
- `webapp-keep.svg` / `.png`      (amarillo Keep)
- `webapp-notes.svg` / `.png`     (nota estilo Apple)

Convertir SVG a PNG:
```bash
cd ~/.local/share/icons
for n in whatsapp keep notes; do rsvg-convert -w 256 -h 256 webapp-$n.svg -o webapp-$n.png; done
```

---

## 2. Lanzadores (`~/.local/share/applications/`)

Clave del modo app: `google-chrome-stable --app=URL --class=<id> --name=<id>` +
`StartupWMClass=<id>` (para que la ventana agrupe con su ícono en el dock de Noctalia).

**`webapp-whatsapp.desktop`**
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=WhatsApp
Comment=WhatsApp Web como aplicación (Chrome)
Exec=/usr/bin/google-chrome-stable --app=https://web.whatsapp.com/ --class=whatsapp-web --name=whatsapp-web
Icon=/home/ermesbatista/.local/share/icons/webapp-whatsapp.png
Terminal=false
StartupWMClass=whatsapp-web
StartupNotify=true
Categories=Network;InstantMessaging;
Keywords=whatsapp;chat;mensajes;wa;
```

**`webapp-keep.desktop`** → igual, cambiando:
```
Name=Google Keep
Exec=/usr/bin/google-chrome-stable --app=https://keep.google.com/ --class=google-keep --name=google-keep
Icon=.../webapp-keep.png
StartupWMClass=google-keep
```

**`webapp-notes.desktop`** → igual, cambiando:
```
Name=Apple Notes
Exec=/usr/bin/google-chrome-stable --app=https://www.icloud.com/notes --class=apple-notes --name=apple-notes
Icon=.../webapp-notes.png
StartupWMClass=apple-notes
```

Registrar tras crearlos:
```bash
update-desktop-database ~/.local/share/applications
```

---

## 3. Uso

- Aparecen en el **lanzador de Noctalia** buscando "WhatsApp", "Keep" o "Notes/Notas".
- La **primera vez** hay que iniciar sesión en cada una (WhatsApp por QR, Keep con cuenta Google,
  Notes con Apple ID).

---

## 4. (Opcional) Fijarlas al dock de Noctalia

El dock de Noctalia fija apps por su id de `.desktop`. En Ajustes de Noctalia → **Dock →
Aplicaciones fijadas**, agregar las entradas: `webapp-whatsapp`, `webapp-keep`, `webapp-notes`
(junto a las que ya estaban: `code`, `firefox`, `google-chrome`, `mongodb-compass`,
`com.anthropic.Claude`).
