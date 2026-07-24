# 🧰 Instalar mis programas — CachyOS (Arch) · Runbook reutilizable

> **PARA UNA FUTURA SESIÓN / REINSTALACIÓN:** este archivo lista TODO lo que hay que instalar
> y CÓMO, para no repetir la investigación. Léelo y ejecuta los bloques en orden.
> Creado el **2026-07-19** en `MacBookErmes` (CachyOS, kernel 7.1.3, x86_64).
>
> **Regla de oro (del usuario): no improvisar.** Verifica cada paquete antes de asumir que existe,
> y NO toques kernel/arranque. La sección de **MongoDB** tiene una trampa importante: **léela entera.**

---

## 0) Requisitos previos

- **CachyOS / Arch** con `pacman` y el helper de AUR **`paru`** (ya presentes en esta máquina).
- Sin flatpak ni snap (se usa pacman + AUR).
- `sudo` disponible.

```bash
# Sanity check
command -v pacman paru || echo "FALTA pacman/paru"
# El sistema debe estar al día para evitar 'partial upgrades' (NO forzar -Syu de kernel sin querer).
# Si hay 0 updates pendientes, se puede instalar directo. Si hay muchos, evaluar antes.
pacman -Qu | wc -l
```

---

## 1) Apps desde repos oficiales (pacman)

```bash
sudo pacman -S --needed --noconfirm \
  obs-studio \
  vlc \
  signal-desktop \
  telegram-desktop \
  libreoffice-fresh \
  rpi-imager \
  bitwarden \
  rclone \
  nautilus \
  loupe papers \
  file-roller unzip zip unrar 7zip \
  github-cli \
  claude-desktop
#   github-cli    = el CLI "gh"
#   claude-desktop = app oficial de Anthropic (añadido 2026-07-21)
```

| App | Paquete |
|---|---|
| OBS Studio | `obs-studio` |
| VLC | `vlc` |
| Signal | `signal-desktop` |
| Telegram | `telegram-desktop` |
| LibreOffice | `libreoffice-fresh` |
| Raspberry Pi Imager | `rpi-imager` |
| Bitwarden (gestor de contraseñas) | `bitwarden` |
| **Nautilus** (gestor de archivos moderno, reemplaza a Dolphin) | `nautilus` |
| **Loupe** (visor de imágenes moderno, tipo Preview) | `loupe` |
| **Papers** (visor de PDF GTK4) | `papers` |
| **Descompresor** (GUI + zip/rar/7z/tar) | `file-roller` `unzip` `zip` `unrar` `7zip` |
| GitHub CLI (`gh`) | `github-cli` |
| **Claude Desktop** (app oficial de Anthropic) | `claude-desktop` — está en el **repo de CachyOS**, va por `pacman` (binario listo, sin compilar). En AUR hay `claude-desktop` y `claude-desktop-bin`, que reempaquetan el .deb oficial: **innecesarios**, es la misma versión |

`gh` se usa autenticándote una vez: `gh auth login` (GitHub.com → HTTPS → login por navegador).

---

## 2) Apps desde AUR (paru)

```bash
paru -S --needed --noconfirm --skipreview \
  google-chrome \
  spotify \
  postman-bin \
  winbox \
  visual-studio-code-bin \
  termius \
  onlyoffice-bin \
  anydesk-bin \
  arduino-ide-bin \
  mongodb-compass-bin \
  rclone-browser \      # GUI para rclone / Google Drive (ver §7)
  gnome-network-displays \  # presentar pantalla a la TV / Miracast (ver §8)
  zoom                  # videoconferencia (añadido 2026-07-21)
```

| App | Paquete AUR | Nota |
|---|---|---|
| Google Chrome | `google-chrome` | |
| Spotify | `spotify` | |
| Postman | `postman-bin` | |
| Winbox (MikroTik) | `winbox` | v4 **nativo Linux** (no wine) |
| Visual Studio Code | `visual-studio-code-bin` | build oficial de Microsoft |
| Termius | `termius` | |
| ONLYOFFICE | `onlyoffice-bin` | el office open-source parecido a MS Office |
| AnyDesk | `anydesk-bin` | |
| Arduino IDE 2 | `arduino-ide-bin` | IDE 2.x moderno |
| MongoDB Compass | **`mongodb-compass-bin`** | ⚠️ usar el `-bin`. El `mongodb-compass` normal falla por depender de `electron37`; el `-bin` trae su propio Electron |
| **Zoom** | `zoom` | Paquete oficial de Zoom. Para **compartir pantalla en Wayland** hacen falta `xdg-desktop-portal-hyprland` + `xdg-desktop-portal-gtk` (los trae el meta de CachyOS). Si al compartir solo se ve negro: elegir "Compartir pantalla" y aceptar el diálogo del *portal*, no la lista interna de ventanas de Zoom |

> **Office:** se instalaron **ambos** (LibreOffice del repo oficial + ONLYOFFICE de AUR).
> Quédate con el que prefieras; ONLYOFFICE se parece más visualmente a Microsoft Office.

**Arduino / puerto serie:** para subir sketches sin sudo, agrega tu usuario al grupo del puerto:
```bash
sudo usermod -aG uucp,lock $USER   # en Arch el grupo del serial suele ser 'uucp'. Reloguear después.
```

---

## 3) Apps SIN cliente oficial de Linux — se usan por navegador

Estas **no tienen app nativa** de Linux. Decisión tomada (2026-07-19): usarlas vía web en Chrome.

| App | Situación | Alternativa |
|---|---|---|
| **WhatsApp** | No hay app oficial Linux | `web.whatsapp.com` (o AUR no oficial `whatsapp-nativefier`, un envoltorio de WhatsApp Web) |
| **Google Drive** | Google no da cliente Linux | ✅ **RESUELTO con rclone** → ver §7 (carpeta `~/GoogleDrive`, gratis) |
| **CapCut** | **No existe** para Linux | `capcut.com` (web), o editor nativo `kdenlive` |

---

## 4) 🍃 MongoDB con réplica + autenticación (¡SECCIÓN DELICADA!)

> ### ⚠️ TRAMPA DEL KERNEL — LEER PRIMERO
> MongoDB **8.0.21 y superior** (8.2/8.3 incluidas) **se niega a arrancar en kernels ≥ 6.19**
> (mensaje: *"Linux kernel versions 6.19 and newer has a known incompatibility"*, JIRA `SERVER-121912`,
> bug de TCMalloc/RSEQ). Este equipo tiene kernel **7.1.3**, así que la última versión NO arranca.
>
> El bug **real** del kernel ya está corregido desde **kernel 7.0.14**, así que MongoDB corre estable;
> lo único que molesta es un **guard genérico** de MongoDB. La eliminación de ese guard para kernels
> ≥7.0.14 llega en **MongoDB 9.1.0** (JIRA `SERVER-125742`).
>
> **SOLUCIÓN aplicada:** instalar la **última versión que aún arranca = `8.0.20`** (probado: 8.0.20 ✅ / 8.0.21 ❌)
> y **fijarla** en `IgnorePkg` para que no se actualice sola.
>
> 👉 Cuando exista un release estable **≥ 9.1.0** (o backport con `SERVER-125742`), se puede quitar el pin
> y actualizar — **verificando antes que arranca**.

### 4.1) Shell y herramientas (versión actual, no importa el guard)
```bash
paru -S --needed --noconfirm --skipreview mongosh-bin mongodb-tools-bin
```

### 4.2) Instalar el servidor fijado a 8.0.20 (reconstruyendo el paquete AUR)
```bash
cd ~/  # o donde quieras compilar
git clone https://aur.archlinux.org/mongodb-bin.git
cd mongodb-bin
# Fijar versión a 8.0.20:
sed -i 's/^pkgver=.*/pkgver="8.0.20"/'  PKGBUILD
sed -i 's/^_basever=.*/_basever="8.0"/' PKGBUILD
# Los .deb vienen de repo.mongodb.org (https oficial): checksums a SKIP
sed -i "/^sha256sums_x86_64=/,/)/ s/'[0-9a-f]\{64\}'/'SKIP'/g" PKGBUILD
makepkg -si --noconfirm --needed
mongod --version   # -> db version v8.0.20
```

### 4.3) Evitar que se actualice (pin)
```bash
sudo sed -i 's/^#\?IgnorePkg.*/IgnorePkg   = mongodb-bin/' /etc/pacman.conf
grep '^IgnorePkg' /etc/pacman.conf   # -> IgnorePkg   = mongodb-bin
```

### 4.4) Servicio como root + réplica (rutas de Arch, NO las de Ubuntu)
> En **Arch/CachyOS** el servicio es **`mongodb.service`** (no `mongod.service`) y la config es
> **`/etc/mongodb.conf`** (no `/etc/mongod.conf`). El servicio ya corre como usuario `mongodb`.

```bash
# Backup config
sudo cp -a /etc/mongodb.conf /etc/mongodb.conf.bak-$(date +%F)

# (Opcional) correr como root vía drop-in (sobrevive updates; mejor que editar el .service):
sudo mkdir -p /etc/systemd/system/mongodb.service.d
printf '[Service]\nUser=root\nGroup=root\n' | sudo tee /etc/systemd/system/mongodb.service.d/override.conf

# Añadir la réplica a la config:
printf '\nreplication:\n  oplogSizeMB: 2000\n  replSetName: rs0\n' | sudo tee -a /etc/mongodb.conf

sudo systemctl daemon-reload
sudo systemctl enable --now mongodb
systemctl is-active mongodb        # -> active
```

### 4.5) Iniciar la réplica (single-node, solo local)
```bash
mongosh --quiet --host 127.0.0.1 --port 27017 --eval \
  'rs.initiate({_id:"rs0", members:[{_id:0, host:"127.0.0.1:27017"}]})'
# esperar unos segundos a que sea PRIMARY
mongosh --quiet --host 127.0.0.1 --port 27017 --eval 'rs.status().members[0].stateStr'  # -> PRIMARY
```

### 4.6) Crear usuario root (ANTES de activar la seguridad)
```bash
# ⚠️ CONTRASEÑA EN TEXTO PLANO — cámbiala si copias este USB a otro lado.
#    Password usado el 2026-07-19: Servextex5252-
mongosh --quiet --host 127.0.0.1 --port 27017 --eval '
db.getSiblingDB("admin").createUser({
  user: "root",
  pwd: "Servextex5252-",
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "root", db: "admin" },
    "readWriteAnyDatabase"
  ]
});'
```

### 4.7) Activar la seguridad (keyFile → habilita auth)
```bash
# Keyfile (propietario root porque el servicio corre como root; permisos 400)
sudo bash -c 'umask 077; openssl rand -base64 756 > /etc/mongodb.keyfile'
sudo chown root:root /etc/mongodb.keyfile
sudo chmod 400 /etc/mongodb.keyfile

printf '\nsecurity:\n  keyFile: /etc/mongodb.keyfile\n' | sudo tee -a /etc/mongodb.conf
sudo systemctl restart mongodb
```

### 4.8) Verificar
```bash
# Sin credenciales -> debe FALLAR ("requires authentication")
mongosh --quiet --eval 'db.adminCommand({listDatabases:1})'
# Con root -> debe FUNCIONAR
mongosh --quiet "mongodb://root:Servextex5252-@127.0.0.1:27017/admin?replicaSet=rs0" \
  --eval 'print(rs.status().set + " / " + rs.status().members[0].stateStr)'
```

**Cadena de conexión** (Compass / apps):
```
mongodb://root:Servextex5252-@127.0.0.1:27017/?replicaSet=rs0&authSource=admin
```

---

## 4.9) 🟥 Redis / Valkey (caché y sesiones) — añadido 2026-07-21

> ⚠️ En **Arch/CachyOS el paquete `redis` ahora ES `valkey`** (fork libre y *drop-in* de Redis,
> mantenido por la Linux Foundation): mismo protocolo, mismo puerto **6379**, mismos binarios
> `redis-server` / `redis-cli`. Tu `app.py` usa `redis://localhost:6379/1` → **funciona sin
> cambiar una sola línea**.

```bash
sudo pacman -S --needed --noconfirm redis      # instala 'valkey' (provee redis)
sudo systemctl enable --now valkey.service      # arranca + activa al boot
#   redis.service queda como alias de valkey.service

# Verificar:
redis-cli ping                                  # -> PONG
redis-cli -n 1 set x ok && redis-cli -n 1 get x && redis-cli -n 1 del x   # DB 1 (la de la app) OK
ss -tlnp | grep 6379                            # -> escuchando en 127.0.0.1:6379
```

No necesita usuario/replica/auth como MongoDB: por defecto queda en `localhost:6379`, 16 DBs
(la app usa la `1`), sin contraseña. Suficiente para caché/sesiones locales.

---

## 5) Verificación final de todo

```bash
for p in google-chrome obs-studio vlc postman-bin winbox visual-studio-code-bin \
         signal-desktop telegram-desktop termius mongodb-compass-bin libreoffice-fresh \
         onlyoffice-bin rpi-imager anydesk-bin arduino-ide-bin spotify bitwarden github-cli \
         rclone rclone-browser gnome-network-displays nautilus loupe papers file-roller unzip zip unrar 7zip \
         mongodb-bin mongosh-bin mongodb-tools-bin valkey; do
  pacman -Qq "$p" >/dev/null 2>&1 && printf "  OK  %-24s %s\n" "$p" "$(pacman -Q $p|awk '{print $2}')" \
    || printf "  --  %-24s FALTA\n" "$p"
done
```

---

## 6) 🔍 Apps Electron se ven DIMINUTAS (HiDPI / escala 1.67)

En este MacBook (Hyprland/Wayland, panel 2880×1800 a escala **1.666667**) las apps **Electron**
salen chiquitas porque corren como XWayland (Hyprland tiene `xwayland.force_zero_scaling=true`).

**Fix GLOBAL (arregla las Electron MODERNAS: Chrome, VS Code, Signal, Bitwarden, Compass, Postman…):**
forzar Wayland nativo en `~/.config/uwsm/env`:
```bash
# cambiar auto -> wayland
export ELECTRON_OZONE_PLATFORM_HINT=wayland
```
Requiere **cerrar sesión y volver a entrar**.

**EXCEPCIÓN — Electron viejo (ignora Wayland fraccional).** Ej: **Termius = Electron 21/Chrome 106**.
Esas se quedan XWayland y diminutas → necesitan parche por-app. Copia su `.desktop` a
`~/.local/share/applications/` y agrega la bandera al Exec:
```bash
# ejemplo Termius
sed 's|^Exec=termius|Exec=termius --force-device-scale-factor=1.67|' \
  /usr/share/applications/termius.desktop > ~/.local/share/applications/termius.desktop
update-desktop-database ~/.local/share/applications
# cerrar la app POR COMPLETO antes de reabrir (son single-instance)
```
Ver la versión de Electron de una app: `strings /opt/<app>/<bin> | grep -i Electron/`.

**Nota del monitor:** el scale debe ser un valor válido para la resolución. `1.7` es inválido para
2880×1800 y tira warnings al login; el correcto es **`1.666667`** (=5/3 → 1728×1080 exacto) en
`~/.config/hypr/config/monitors.lua`. Este Hyprland usa parser Lua → aplicar con `hyprctl reload`.

---

## 7) ☁️ Google Drive (gratis, con rclone) — montado como carpeta

Google no tiene cliente Linux. Solución **gratis** (se descartó Insync por ser de pago, y Celeste
porque no compila — dep Rust vieja). Queda tu Drive en `~/GoogleDrive`, montado al iniciar sesión.

```bash
sudo pacman -S --needed --noconfirm rclone      # motor (oficial)
paru -S --needed --noconfirm --skipreview rclone-browser   # GUI opcional (Qt)
```

**Client_id propio (IMPORTANTE):** el client_id compartido de rclone se retira en 2026. Crea el tuyo
(una vez) para que no se corte:
1. https://console.cloud.google.com/ → proyecto nuevo → habilita **Google Drive API**.
2. **Pantalla de consentimiento OAuth** → Externo → rellena lo mínimo → **PUBLICAR APP a Producción**
   (si la dejas en "Prueba" da `Error 403 access_denied` y el token caduca a 7 días).
3. **Credenciales → Crear → ID de cliente OAuth → App de escritorio** → descarga el JSON.

**Conectar la cuenta (el login va en el navegador, sin terminal para el usuario):**
```bash
# usa el client_id y secret del JSON descargado:
CID=...    # termina en .apps.googleusercontent.com
CSEC=...   # empieza por GOCSPX-
rclone config create gdrive drive scope drive client_id "$CID" client_secret "$CSEC"
rclone authorize "drive" "$CID" "$CSEC"        # abre el navegador -> autorizar
# copia el token que imprime y:
rclone config update gdrive token '<PEGAR_JSON_DEL_TOKEN>'
#   (ese 'config update' a veces se cuelga levantando :53682; el token ya se escribió, se puede matar)
rclone lsd gdrive:     # prueba: lista tus carpetas
```

**Montaje automático (servicio de usuario systemd):** `~/.config/systemd/user/rclone-gdrive.service`
```ini
[Unit]
Description=Montaje Google Drive (rclone)
After=network-online.target
Wants=network-online.target
[Service]
Type=notify
TimeoutStartSec=120
ExecStartPre=/usr/bin/mkdir -p %h/GoogleDrive
ExecStart=/usr/bin/rclone mount gdrive: %h/GoogleDrive --vfs-cache-mode full --vfs-cache-max-size 10G --dir-cache-time 1000h --poll-interval 15s --umask 022
ExecStop=/usr/bin/fusermount3 -u %h/GoogleDrive
Restart=on-failure
RestartSec=10
[Install]
WantedBy=default.target
```
```bash
systemctl --user daemon-reload
systemctl --user enable --now rclone-gdrive.service
ls ~/GoogleDrive     # tus archivos
```

---

## 8) 🖥️ Extras de escritorio (post-instalación)

### 8.1 Nautilus por defecto (en vez de Dolphin) + visores de imagen/PDF
```bash
xdg-mime default org.gnome.Nautilus.desktop inode/directory
# atajo de Hyprland: en ~/.config/hypr/config/variables.lua
#   FILE_MANAGER = "nautilus"      (estaba "dolphin")   -> Super+E lo abre

# Visores por defecto:
xdg-mime default org.gnome.Papers.desktop application/pdf
for m in image/png image/jpeg image/gif image/webp image/bmp image/tiff image/x-icon image/heif image/avif image/svg+xml; do
  xdg-mime default org.gnome.Loupe.desktop "$m"
done

# Quitar Dolphin: OJO, es dependencia del meta 'cachyos-hypr-noctalia', así que -Rns normal no lo deja.
# Remoción quirúrgica (solo Dolphin, no toca nada más):
sudo pacman -Rdd dolphin
#   Nota: un futuro update del meta podría reinstalarlo; si vuelve, repetir el -Rdd.
```
**IMPORTANTE tras quitar Dolphin:** algunas apps (p.ej. el navegador al "mostrar en carpeta") llaman a
`dolphin` por su nombre y dan error "No se ha podido encontrar el programa «dolphin»". Nautilus vía
`xdg-open`/mimeapps SÍ es el default, pero esos llamados hardcodeados fallan. Fix = **puente** en el PATH:
```bash
cat > ~/.local/bin/dolphin <<'SH'
#!/bin/sh
# Puente: Dolphin -> Nautilus. (Borrar este archivo para revertir.)
target=""
for arg in "$@"; do case "$arg" in -*) ;; file://*) target="${arg#file://}";; *) target="$arg";; esac; done
if [ -n "$target" ]; then [ -f "$target" ] && target=$(dirname "$target"); exec nautilus -- "$target"; fi
exec nautilus
SH
chmod +x ~/.local/bin/dolphin   # ~/.local/bin va primero en el PATH gráfico
```

### 8.2 Descompresor: predeterminar file-roller para los formatos comunes
```bash
for m in application/zip application/vnd.rar application/x-rar application/x-7z-compressed \
         application/x-tar application/gzip application/x-bzip2 application/x-xz \
         application/x-compressed-tar application/x-zip-compressed; do
  xdg-mime default org.gnome.FileRoller.desktop "$m"
done
# Nautilus: clic derecho -> "Extraer aquí". RAR solo se extrae (no se crea) en Linux.
```

### 8.3 Presentar pantalla a la TV (Miracast) con atajo de teclado
Requisitos ya presentes en el MacBook: WiFi con P2P/Wi-Fi Direct + `xdg-desktop-portal-hyprland`.
```bash
# app: gnome-network-displays (instalada en §2). Uso: TV en modo "Screen Mirroring" -> abrir app -> elegir TV.
```
**Atajo Hyprland** (en `~/.config/hypr/config/binds.lua`), tecla libre `Super+M` (Mirror):
```lua
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd(launchPrefix .. "gnome-network-displays")) -- Presentar en TV
```
**Lanzador con muchas keywords** (para encontrarlo buscando "tv/presentar/espejo/airplay") en
`~/.local/share/applications/presentar-tv.desktop`:
```ini
[Desktop Entry]
Name=Presentar en TV (Screen Mirroring)
Exec=gnome-network-displays
Icon=org.gnome.NetworkDisplays
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
Keywords=tv;televisor;presentar;espejo;mirror;mirroring;airplay;cast;proyectar;pantalla;screen;display;miracast;chromecast;
```
```bash
update-desktop-database ~/.local/share/applications
```

**⚠️ FIREWALL (imprescindible si usas ufw) — el motivo de "se queda conectando / raya en la TV":**
Muchas Smart-TV son **Chromecast** (no Miracast): la laptop monta un servidor HTTP en un **puerto alto
aleatorio** (32768-60999) y la TV lo descarga. Con `ufw deny incoming`, la TV queda bloqueada → LOADING.
Diagnóstico: `sudo journalctl -k | grep 'UFW BLOCK'` (verás la IP de la TV). Fix (funciona en cualquier red):
```bash
for net in 192.168.0.0/16 10.0.0.0/8 172.16.0.0/12; do
  sudo ufw allow proto tcp from $net to any port 32768:60999 comment 'Chromecast/cast media (GND)'
done
# (opcional, para TVs Miracast reales:)
sudo ufw allow 7236/tcp comment 'Miracast RTSP'
sudo ufw allow from 192.168.49.0/24 comment 'Miracast Wi-Fi Direct'
```
**Soporta AMBOS (global, no solo Chromecast):** la app detecta el tipo de TV sola.
- Chromecast/Cast → reglas de puertos altos de arriba.
- **Miracast** (TV con "Screen Mirroring") → requiere NetworkManager con **wpa_supplicant** (NO iwd),
  dispositivo `p2p-dev-wlan0` gestionado por NM, y las reglas `192.168.49.0/24` + `7236/tcp` de arriba.
  Verificar: `NetworkManager --print-config | grep wifi.backend` y `nmcli device | grep p2p`.

Notas: codifica por HW (`vah264enc`, GPU AMD). El **lag ~1-2 s es inherente al Chromecast** (bien para
presentaciones, no para video; para video, castear la pestaña/archivo desde Chrome, no espejar).
Diagnóstico avanzado: `systemd-run --user --unit=gnd-debug --setenv=G_MESSAGES_DEBUG=all --setenv=GST_DEBUG=2 gnome-network-displays` + `journalctl --user -u gnd-debug`. (NUNCA `pkill -f gnome-network-displays`: la línea se auto-mata.)

### 8.4 Fondo de pantalla (wallpaper) — carpeta con rotación aleatoria (tipo Mac)
El wallpaper lo gestiona **Noctalia** (además genera los colores del sistema a partir de él). NO se
cambia con herramientas sueltas (swww/hyprpaper a mano) — hay que usar Noctalia, o "no cambia".

**Comandos CLI de Noctalia:**
```bash
noctalia msg wallpaper-get                 # ver el actual
noctalia msg wallpaper-set <ruta/imagen>   # fijar uno (persistente)
noctalia msg wallpaper-random              # saltar a uno aleatorio ya
noctalia msg wallpaper-next / -previous    # siguiente / anterior
noctalia msg settings-open wallpaper       # abrir Ajustes en la sección Wallpaper
```
**Rotación aleatoria desde carpeta (como en Mac) — por la GUI** (`settings-open wallpaper`):
1. Carpeta de wallpapers → `~/Pictures/Wallpapers` (crear la carpeta y meter ahí tus imágenes).
2. "Cycle automatically / on a timer" → activar.
3. "Order" → **Random**.
4. "Seconds between changes" → intervalo (ej. 300 = 5 min).
5. (Opcional) "Search nested folders", transición, fill (Crop).
```bash
mkdir -p ~/Pictures/Wallpapers   # poner aquí los fondos; toda la carpeta entra en la rotación
```

---

## Apéndice — decisiones tomadas el 2026-07-19
- WhatsApp / CapCut → **por navegador** (no hay cliente Linux decente/gratuito).
- Google Drive → **RESUELTO con rclone** (gratis, carpeta `~/GoogleDrive`, client_id propio) — ver §7. Se descartó Insync (de pago) y Celeste (no compila).
- Office → **LibreOffice + ONLYOFFICE** (ambos).
- MongoDB → **fijado en 8.0.20** por el guard de kernel; réplica `rs0` **solo local** (127.0.0.1); servicio como **root**.
- No se tocó kernel ni arranque. El sistema estaba al día (0 updates pendientes) → sin riesgo de partial-upgrade.

**Extras añadidos el 2026-07-20:**
- **Nautilus** como gestor por defecto (reemplaza Dolphin, que se ve fuera de lugar en Hyprland). Dolphin quedó instalado.
- **Descompresor**: file-roller + zip/rar/7z/tar (faltaba todo; por eso no abrían los .zip/.rar).
- **Casting a TV** (Miracast) con `gnome-network-displays`, atajo **Super+M** y lanzador buscable "Presentar en TV". Barra Noctalia soporta widget "custom" pero se dejó por GUI para no editar la config a ciegas.
- Google Drive quedó con **client_id propio publicado** (ya no el compartido de rclone).
