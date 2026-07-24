# Redirección de almacenamiento de apps de mensajería al disco externo (P3-512)

**Equipo:** Mac Mini / CachyOS · **Fecha:** 2026-07-22
**Objetivo:** Que Signal, Telegram y WhatsApp guarden TODOS sus datos en el disco
externo (P3-512, `/mnt/disco1`) y NO en el NVMe interno (109 GB), con un **tope
duro de 80 GB** para que nunca se coman el disco (en el Mac, WhatsApp llegó a 238 GB
por caché de media autodescargada).

---

## Resultado final

| App       | Instalación         | Enlace en el home                     | Datos reales (dentro del contenedor)        |
|-----------|---------------------|---------------------------------------|---------------------------------------------|
| Signal    | pacman `signal-desktop`   | `~/.config/Signal`              | `/mnt/disco1/AppData/Signal`                |
| Telegram  | pacman `telegram-desktop` | `~/.local/share/TelegramDesktop`| `/mnt/disco1/AppData/TelegramDesktop`       |
| WhatsApp  | AUR `zapzap` (cliente)    | `~/.config/ZapZap`              | `/mnt/disco1/AppData/ZapZap-config`         |
|           |                           | `~/.local/share/ZapZap`         | `/mnt/disco1/AppData/ZapZap-share`          |
|           |                           | `~/.cache/ZapZap`               | `/mnt/disco1/AppData/ZapZap-cache`          |

Cada ruta del home es un **symlink** que apunta dentro del contenedor. La app
"cree" que escribe en su ruta de siempre; físicamente todo cae en el contenedor.

> **Nota (2026-07-22):** se eliminó el antiguo lanzador de WhatsApp como web-app
> de Chrome. Era `~/.local/share/applications/webapp-whatsapp.desktop`
> (`google-chrome-stable --app=https://web.whatsapp.com/`) + ícono
> `~/.local/share/icons/webapp-whatsapp.png`. Ahora WhatsApp se usa vía **ZapZap**.
> Para quitarlo: `rm` de esos dos archivos + `update-desktop-database ~/.local/share/applications`.

---

## El contenedor (tope duro de 80 GB)

Es una **imagen ext4 dispersa** montada como loopback. Al ser un sistema de
archivos de tamaño fijo, las apps **físicamente no pueden pasar de 80 GB**.
Es dispersa (`truncate`): solo ocupa espacio real a medida que se llena.

- Imagen: `/mnt/disco1/AppData.img`  (80 GB)
- Montaje: `/mnt/disco1/AppData`  (loop, ext4, `-m 0` sin bloques reservados)
- Montaje automático al arrancar vía `/etc/fstab`.

### Línea agregada a `/etc/fstab`
```
/mnt/disco1/AppData.img  /mnt/disco1/AppData  ext4  loop,nofail,x-systemd.requires-mounts-for=/mnt/disco1  0 0
```
(`x-systemd.requires-mounts-for` garantiza que `/mnt/disco1` monte primero.)
Respaldo del fstab original en `/etc/fstab.bak-*`.

---

## Comandos exactos usados (reproducible desde cero)

```bash
# 0) Cerrar apps ANTES de mover datos (evita corromper la DB).
#    OJO: NO usar `pkill -f signal-desktop/zapzap` -> el propio comando contiene
#    esa cadena y pkill se auto-mata (exit 144). Usar coincidencia exacta -x:
pkill -TERM -x signal-desktop
pkill -TERM -x Telegram
pkill -TERM -x zapzap

# 1) Instalar cliente de WhatsApp.
#    NO usar `whatsapp-for-linux` (AUR): depende de `webkit2gtk` (ya no está en
#    repos oficiales) y se pone a compilar WebKit entero -> falla.
#    Usar ZapZap: usa qt6-webengine precompilado de repos oficiales.
paru -S --noconfirm --needed zapzap

# 2) Crear el contenedor de 80 GB y montarlo.
EXT=/mnt/disco1; IMG=$EXT/AppData.img; MNT=$EXT/AppData
mv "$MNT" "$MNT.staging"          # apartar datos que ya estaban ahí (si aplica)
mkdir "$MNT"
truncate -s 80G "$IMG"            # imagen dispersa
mkfs.ext4 -q -m 0 -L AppData "$IMG"
sudo mount -o loop "$IMG" "$MNT"
sudo chown ermesbatista:ermesbatista "$MNT"

# 3) Mover datos de cada app al contenedor y dejar symlink en su ruta original.
#    Patrón: cp -a origen destino; verificar bytes iguales; rm origen; ln -s.
#    Signal      : ~/.config/Signal            -> $MNT/Signal
#    Telegram    : ~/.local/share/TelegramDesktop -> $MNT/TelegramDesktop
#    ZapZap conf : ~/.config/ZapZap            -> $MNT/ZapZap-config
#    ZapZap share: ~/.local/share/ZapZap       -> $MNT/ZapZap-share
#    ZapZap cache: ~/.cache/ZapZap             -> $MNT/ZapZap-cache

# 4) Persistir en fstab (ver línea arriba) y probar:
sudo umount /mnt/disco1/AppData
sudo mount /mnt/disco1/AppData    # lee la línea de fstab -> debe montar bien
```

---

## Cómo cambiar el tope (ej. subir de 80 GB a 120 GB)
```bash
# apps cerradas + contenedor desmontado
sudo umount /mnt/disco1/AppData
e2fsck -f /mnt/disco1/AppData.img
truncate -s 120G /mnt/disco1/AppData.img
resize2fs /mnt/disco1/AppData.img
sudo mount /mnt/disco1/AppData
```
Para REDUCIR: `resize2fs` a un tamaño menor primero, luego `truncate`. (Riesgoso;
respaldar antes.)

## Cómo revertir todo (volver a disco interno)
```bash
# cerrar apps
# por cada symlink: borrar el symlink y copiar la carpeta de vuelta al home
rm ~/.config/Signal && cp -a /mnt/disco1/AppData/Signal ~/.config/Signal
# ...idem Telegram y ZapZap...
sudo umount /mnt/disco1/AppData
# quitar la línea de /etc/fstab (o restaurar /etc/fstab.bak-*)
rm /mnt/disco1/AppData.img
```

---

## Recomendación anti-238GB (además del tope duro)
Apagar autodescarga de media en cada app para que no acumulen:
- **Telegram:** Ajustes → Avanzado → Descarga automática de media → desactivar.
- **WhatsApp/ZapZap:** Ajustes de WhatsApp → Almacenamiento y datos → autodescarga.
- **Signal:** guarda menos por defecto; revisar Ajustes → Datos y almacenamiento.

## Trampas encontradas (gotchas)
- `pkill -f <patrón>` se auto-mata si el patrón está en su propia línea de comando
  (exit 144). Usar `pkill -x <comm>`.
- `whatsapp-for-linux` (AUR) arrastra `webkit2gtk` de AUR y compila WebKit → falla.
  Alternativa buena y liviana: `zapzap` (Qt6 + qt6-webengine de repos oficiales).
- Cerrar SIEMPRE las apps antes de mover sus carpetas (locks de SQLite).
- `sudo` en este equipo es passwordless.
- El contenedor loop necesita `/mnt/disco1` montado primero: por eso
  `x-systemd.requires-mounts-for=/mnt/disco1` en fstab.
