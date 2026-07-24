# Configuración: disco externo P3-512 (ext4) para trabajo + descargas

Documentado el 2026-07-21. Equipo: Mac Mini corriendo CachyOS (Linux). Usuario: `ermesbatista` (uid/gid 1000).

**Objetivo:** el SSD externo USB de 512 GB (etiqueta `P3-512`, formato **ext4**) se monta
solo siempre en la misma ruta, se puede **trabajar directamente sobre él** (proyectos,
venvs, node_modules, permisos y symlinks reales), y **Chrome y Firefox descargan ahí**
para no llenar el disco interno (nvme).

> **Formato = ext4** (a propósito). Es lo correcto para DESARROLLAR en Linux.
> Contra: un **Mac NO lee ext4** de fábrica. Este disco es para usarse en **Linux**.

---

## Datos del disco

| Dato | Valor |
|------|-------|
| Etiqueta | `P3-512` |
| Formato | **ext4** (nativo Linux; symlinks, permisos, rápido con archivos pequeños) |
| UUID (al documentar) | `0191a9b3-2c51-4cb1-a130-4c7c901f434f` |
| Punto de montaje fijo | `/mnt/disco1` |
| Carpeta de descargas | `/mnt/disco1/Descargas` |

⚠️ **El UUID cambia si vuelves a formatear el disco.** Para obtener el nuevo:
```bash
sudo blkid -L P3-512      # muestra el device, p.ej. /dev/sda1
sudo blkid /dev/sda1      # muestra UUID="..."
```
El script `reconfigurar-disco.sh` (misma carpeta) detecta el disco por su **etiqueta**
`P3-512`, así que funciona aunque cambie el UUID.

---

## 1. Herramientas necesarias

```bash
# ext4 ya viene en Linux (e2fsprogs). Nada que instalar normalmente.
# Solo si necesitas RESCATAR un disco APFS de Mac (lectura):
paru -S --noconfirm apfs-fuse
```

---

## 2. Montaje permanente (fstab)

```bash
sudo mkdir -p /mnt/disco1
```
Línea al final de `/etc/fstab`:
```
UUID=0191a9b3-2c51-4cb1-a130-4c7c901f434f /mnt/disco1 ext4 defaults,nofail,x-gvfs-show,x-gvfs-name=Disco%20P3-512 0 2
```
- `nofail` = si el disco no está conectado, el arranque NO se cuelga.
- `x-gvfs-show` = hace que **aparezca solo** en la barra lateral de Dolphin (como un disco normal), sin marcador manual.
- `x-gvfs-name=...` = el nombre que muestra en la barra ("Disco P3-512").

Como ext4 tiene dueños reales, tras el primer montaje se pone el disco a tu nombre:
```bash
sudo systemctl daemon-reload
sudo mount /mnt/disco1
sudo chown ermesbatista:ermesbatista /mnt/disco1
```

---

## 3. Carpeta de descargas

```bash
mkdir -p /mnt/disco1/Descargas
```

---

## 4. Google Chrome → descargar al disco

Archivo: `/etc/opt/chrome/policies/managed/descargas.json`
```json
{
  "DownloadDirectory": "/mnt/disco1/Descargas",
  "PromptForDownloadLocation": false
}
```
```bash
sudo mkdir -p /etc/opt/chrome/policies/managed
# (crear el archivo de arriba)
```
Cierra y abre Chrome. Verifica en `chrome://policy` que aparece `DownloadDirectory`.

---

## 5. Firefox → descargar al disco (autoconfig, nivel sistema)

Archivo 1: `/usr/lib/firefox/defaults/pref/autoconfig.js`
```js
pref("general.config.filename", "firefox.cfg");
pref("general.config.obscure_value", 0);
```
Archivo 2: `/usr/lib/firefox/firefox.cfg`  (la **primera línea DEBE ser un comentario**)
```js
// Config Servex: descargas al disco externo
defaultPref("browser.download.folderList", 2);
defaultPref("browser.download.dir", "/mnt/disco1/Descargas");
defaultPref("browser.download.useDownloadDir", true);
```
Cierra y abre Firefox.

> Si actualizas Firefox, estos archivos (en `/usr/lib/firefox/`) pueden borrarse.
> Vuelve a correr el script si dejan de funcionar las descargas.

---

## 6. Notas

- **ext4 sí soporta symlinks y permisos**, así que puedes crear venvs normales
  (`python -m venv .venv`) y `npm install` directamente en el disco, sin trucos.
- Para desmontar seguro: `sudo umount /mnt/disco1`
- Si el `umount` dice "ocupado" y `lsof/fuser` no muestran nada, casi seguro es
  **`gvfsd-trash`** (monitor de papelera) con un inotify watch. Solución:
  ```bash
  sudo umount -l /mnt/disco1      # desmontaje lazy
  sudo kill $(pgrep -x gvfsd-trash)   # libera el watch
  ```

---

## Reconfigurar rápido

En esta carpeta está **`reconfigurar-disco.sh`**. Tras un reinstalado o problema:
```bash
sudo bash reconfigurar-disco.sh
```
Detecta el disco por su etiqueta `P3-512`, rehace fstab (ext4), lo pone a tu nombre,
crea la carpeta Descargas y configura Chrome y Firefox. Luego reinicia los navegadores.

---

## Apéndice: si hay que RE-FORMATEAR el disco a ext4

(Solo si el disco se corrompe o quieres empezar de cero. **Borra todo.**)
```bash
sudo umount /mnt/disco1 2>/dev/null
sudo wipefs -a /dev/sda
sudo parted -s /dev/sda mklabel gpt
sudo parted -s /dev/sda mkpart "P3-512" ext4 0% 100%
sudo partprobe /dev/sda
sudo mkfs.ext4 -F -L "P3-512" -m 0 /dev/sda1
```
Luego corre `reconfigurar-disco.sh` (el UUID nuevo lo detecta solo por la etiqueta).
