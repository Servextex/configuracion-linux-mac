# MacBook Pro 2016 15" (MacBookPro13,3) en CachyOS — Puesta a punto de periféricos

> **FUENTE DE VERDAD.** Sigue el **RUNBOOK DEFINITIVO** de abajo: es lo ÚNICO probado y funcionando
> en la máquina NUEVA (MacBookPro13,3 · CachyOS con **Limine + Hyprland + Noctalia** · 2026-07-18).
> Detalles/porqués en §11–§16.
> ⚠️ **NO sigas** el "RUNBOOK LEGACY" ni §1–§10 ni el Apéndice A: son de la máquina ORIGINAL (GRUB,
> brillo por AUX) y **varias cosas NO aplican aquí** (lo aclara §12). Se conservan solo como historia.
>
> 📦 **Instalar apps/programas** (Chrome, VS Code, Spotify, MongoDB con réplica, etc.): ver el runbook
> aparte **[`instalar-programas-cachyos.md`](instalar-programas-cachyos.md)** en esta misma USB (2026-07-19).

## ⚡ RUNBOOK DEFINITIVO — MacBookPro13,3 en CachyOS/Limine (2026-07-18)

> Hardware IDÉNTICO. Verifica: `cat /sys/class/dmi/id/product_name` → `MacBookPro13,3`.
> **Kit:** copia `~/macbook-setup-kit/` (USB) → NVRAM WiFi, daemon auto-brillo, servicios, udev, configs.
> **REGLA DE ORO 1:** kernel CachyOS = clang → todo DKMS con **`LLVM=1`** (NO GCC/KCFLAGS).
> **REGLA DE ORO 2:** el brillo va **NATIVO** por `gmux_backlight`. **NUNCA** metas `acpi_backlight=native`
> ni `amdgpu.backlight=1` en el cmdline → rompen la fluidez del compositor y estorban la Touch Bar (§12).
> **REGLA DE ORO 3:** aquí el bootloader es **Limine** (NO GRUB): params de kernel en `/etc/default/limine`
> (`KERNEL_CMDLINE[default]`) + `sudo limine-update`. `mkinitcpio -P` SOLO en terminal normal (§15).

### 0) Base
```bash
cat /sys/class/dmi/id/product_name          # MacBookPro13,3
echo 'ermesbatista ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/99-ermesbatista-nopasswd
sudo chmod 440 /etc/sudoers.d/99-ermesbatista-nopasswd     # (revertir al final: rm de ese archivo)
KIT=~/macbook-setup-kit
sudo pacman -S --needed --noconfirm base-devel dkms git linux-cachyos-headers brightnessctl ethtool paru
paru -S --needed --noconfirm mbpfan swayosd
mkdir -p ~/src
```

### 1) WiFi 2.4+5 GHz (da internet; en vivo). Detalle §6.
```bash
sudo cp $KIT/firmware/brcmfmac43602-pcie.txt /lib/firmware/brcm/
sudo cp $KIT/firmware/brcmfmac43602-pcie.txt "/lib/firmware/brcm/brcmfmac43602-pcie.Apple Inc.-MacBookPro13,3.txt"
sudo cp $KIT/modprobe/brcmfmac.conf /etc/modprobe.d/
# si  ethtool -P wlan0  != 00:90:4c:0d:f4:3e → edita macaddr= en AMBOS .txt
nmcli radio wifi off; sudo modprobe -r brcmfmac_wcc brcmfmac 2>/dev/null; sudo modprobe brcmfmac; nmcli radio wifi on
sudo iw phy $(iw dev wlan0 info|awk '/wiphy/{print "phy"$2}') info | grep 'Band 2'   # 5 GHz OK
```

### 2) AUDIO (CS8409) — DKMS+LLVM=1 (suena tras reboot). Detalle §4.
```bash
cd ~/src && git clone --depth 1 https://github.com/davidjo/snd_hda_macbookpro && cd snd_hda_macbookpro
sed -i 's/MAKE="make"/MAKE="make LLVM=1"/' dkms.conf
sudo -E env LLVM=1 ./install.cirrus.driver.sh -i -d
```

### 3) TOUCH BAR (iBridge/T1) — DKMS + 3 parches + **BLACKLIST**. Detalle §5 y §15.
```bash
cd ~/src && git clone --depth 1 -b touchbar-driver-hid-driver https://github.com/marc-git/macbook12-spi-driver.git touchbar-t1
```
- Aplica los **3 parches** kernel 7.1 (texto exacto en §5): `.remove`→`void` en `apple-ib-als.c`/`apple-ib-tb.c`;
  `.report_fixup`→`const __u8 *`; quitar `.owner = THIS_MODULE` del `acpi_driver`.
- Copia SOLO los 3 módulos (SIN `applespi`) a `/usr/src/apple-ibridge-0.1/` con Makefile+`dkms.conf`
  (`MAKE[0]="make LLVM=1 KDIR=/usr/lib/modules/$kernelver/build"`), luego:
```bash
sudo dkms add -m apple-ibridge -v 0.1 && sudo dkms build -m apple-ibridge -v 0.1 && sudo dkms install -m apple-ibridge -v 0.1
echo apple-ibridge | sudo tee /etc/modules-load.d/apple-ibridge.conf                 # autoload
# ⭐ CRÍTICO (§15): sin esto la barra enciende SOLO A VECES (carrera hid_sensor_hub por la interfaz .0002)
sudo cp $KIT/modprobe/blacklist-hid-sensor-hub.conf /etc/modprobe.d/
sudo modprobe -r hid_sensor_hub 2>/dev/null
```

### 4) VENTILADORES (mbpfan) — en vivo. Detalle §10.
```bash
sudo tee /etc/mbpfan.conf >/dev/null <<'CONF'
[general]
low_temp = 50
high_temp = 55
max_temp = 68
polling_interval = 1
CONF
sudo systemctl enable --now mbpfan
```

### 5) BRILLO pantalla = NATIVO (NO cmdline, NO daemon AUX). §12.
```bash
brightnessctl -d gmux_backlight set 50%     # debe mover el panel → si sí, LISTO (no hace falta nada más)
```

### 6) OSD estilo macOS (swayosd) + luz teclado + auto-brillo. §12, §13, §14.
- `autostart.lua` → `hl.exec_cmd("swayosd-server")`
- `binds.lua`: volumen y brillo → `swayosd-client` (§13); luz teclado → `brightnessctl -d 'spi::kbd_backlight'` (§12)
- `~/.config/noctalia/config.toml` → `[osd.kinds]` `volume=false` + `brightness=false`; `noctalia msg config-reload`
```bash
# auto-brillo por sensor (silencioso, gmux directo, rampa suave):
sudo cp $KIT/udev/90-backlight-gmux.rules /etc/udev/rules.d/
sudo chgrp video /sys/class/backlight/gmux_backlight/brightness && sudo chmod g+w /sys/class/backlight/gmux_backlight/brightness
sudo udevadm control --reload
install -Dm755 $KIT/scripts/als-backlight.py ~/.local/bin/als-backlight.py
install -Dm644 $KIT/systemd-user/als-backlight.service ~/.config/systemd/user/als-backlight.service
systemctl --user enable --now als-backlight
```

### 7) Toques macOS (opcional). §5.c / §5.d.
- Scale `1.6`, trackpad (natural_scroll/tap/clickfinger/…), teclado `us altgr-intl` (acentos con AltDcha), gestos 3/4 dedos.

### 8) HIBERNACIÓN (reemplaza suspensión — la suspensión cuelga el GPU AMD). §16.
- ⏳ **EN CONFIGURACIÓN.** Ver §16 (swapfile + `resume=` en Limine + logind). Adaptado de §8 (que es GRUB).

### Orden y reinicios
- 0→1→2→3→4→5→6. **1 reinicio** activa audio + Touch Bar (lo demás es en vivo). WiFi sin reinicio.
- ⚠️ `mkinitcpio -P` SOLO en terminal normal (en background se cuelga, §15). Params de kernel → Limine, NO GRUB.
- **NUNCA** `acpi_backlight=native` / `amdgpu.backlight=1`.

---

## ⚡ RUNBOOK LEGACY (máquina ORIGINAL, GRUB) — ⚠️ NO SEGUIR, solo historia

> Lo de abajo (§0-legacy y pasos 0–5) es de la MÁQUINA ORIGINAL con **GRUB** y **brillo por AUX**.
> **NO lo apliques en la máquina nueva** — usa el RUNBOOK DEFINITIVO de arriba. Se conserva como
> referencia de cómo se hizo la primera vez. Las contradicciones (brillo, bootloader) están explicadas
> en §11 y §12.

## ⚡ RUNBOOK (LEGACY) — configurar OTRO MacBookPro13,3 desde cero

> Para hardware **IDÉNTICO**: MacBookPro13,3 (2016 15", chip T1, WiFi BCM43602, audio CS8409,
> GPU Intel HD530 + AMD Baffin). Verifica: `cat /sys/class/dmi/id/product_name` → `MacBookPro13,3`.
> **Kit de archivos:** copia `~/macbook-setup-kit/` de esta máquina a la nueva (USB).
> **REGLA DE ORO:** el kernel de CachyOS se compila con **clang** → todo módulo DKMS con `LLVM=1`
> (NO GCC, NO KCFLAGS).

### 0) Prerrequisitos
```bash
sudo pacman -S --needed base-devel dkms git linux-cachyos-headers brightnessctl ethtool
KIT=~/macbook-setup-kit          # ajusta si lo copiaste a otra ruta
mkdir -p ~/src
```

### 1) WiFi 2.4 + 5 GHz  ← hazlo primero (independiente, te da internet). Detalle en §6.
```bash
ethtool -P wlan0                 # MAC real (normalmente 00:90:4c:0d:f4:3e en estas tarjetas)
sudo cp $KIT/firmware/brcmfmac43602-pcie.txt /lib/firmware/brcm/
sudo cp $KIT/firmware/brcmfmac43602-pcie.txt "/lib/firmware/brcm/brcmfmac43602-pcie.Apple Inc.-MacBookPro13,3.txt"
# Si la MAC de arriba NO es 00:90:4c:0d:f4:3e, ponla en AMBOS archivos:
#   sudo sed -i 's/^macaddr=.*/macaddr=AA:BB:CC:DD:EE:FF/' /lib/firmware/brcm/brcmfmac43602-pcie*.txt*
sudo cp $KIT/modprobe/brcmfmac.conf /etc/modprobe.d/        # feature_disable=0x82000
nmcli radio wifi off; sudo modprobe -r brcmfmac_wcc brcmfmac 2>/dev/null; sudo modprobe brcmfmac; nmcli radio wifi on
# Verificar 5 GHz (debe aparecer "Band 2"):
sudo iw phy $(iw dev wlan0 info | awk '/wiphy/{print "phy"$2}') info | grep 'Band 2'
```
> Si `wlan0` NO sube (`dmesg` → `Dongle setup failed`): la NVRAM no corresponde. Confirma modelo
> 13,3 y `boardtype=0x073e` en el .txt. Para revertir a 2.4: borra los .txt y recarga el módulo.
> La NVRAM también se baja de `https://bugzilla.kernel.org/attachment.cgi?id=285753` (bug 193121).

### 2) AUDIO (altavoces internos CS8409) — DKMS + LLVM=1. Detalle en §4.
```bash
cd ~/src && git clone https://github.com/davidjo/snd_hda_macbookpro && cd snd_hda_macbookpro
sed -i 's/MAKE="make"/MAKE="make LLVM=1"/' dkms.conf         # permanencia con clang
export LLVM=1
sudo -E env LLVM=1 ./install.cirrus.driver.sh -i -d
# tras REINICIAR: speaker-test -t sine -f 440 -l1 -c2  (debe sonar)
```

### 3) TOUCH BAR (iBridge/T1) — DKMS + parches kernel 7.1 + LLVM=1. Detalle y parches en §5.
```bash
cd ~/src && git clone -b touchbar-driver-hid-driver https://github.com/marc-git/macbook12-spi-driver.git touchbar-t1
```
Aplicar los **3 parches** kernel 6.11+/7.1 (ver §5, texto exacto): (a) `.remove` de los
`platform_driver` en `apple-ib-als.c`/`apple-ib-tb.c` → `void`; (b) `.report_fixup` en
`apple-ibridge.c` → `const __u8 *`; (c) quitar `.owner = THIS_MODULE` del `acpi_driver`.
Copiar fuentes a `/usr/src/apple-ibridge-0.1/` con `dkms.conf` (`MAKE[0]="make LLVM=1 KDIR=..."`) y:
```bash
sudo dkms add -m apple-ibridge -v 0.1 && sudo dkms build -m apple-ibridge -v 0.1 && sudo dkms install -m apple-ibridge -v 0.1
echo apple-ibridge | sudo tee /etc/modules-load.d/apple-ibridge.conf   # autoload
```

### 4) BRILLO de pantalla
> 🛑🛑 **STOP — LEER §12 ANTES.** En la MacBook NUEVA (2026-07-18, Limine) el brillo funciona
> **NATIVO** por `gmux_backlight`, y meter `acpi_backlight=native amdgpu.backlight=1` + el daemon AUX
> **ROMPE la fluidez del compositor** (mouse/animaciones a saltos) y estorba la Touch Bar. En esa
> máquina: **NO hacer NADA de este paso 4** — el brillo ya va con las teclas del Touch Bar.
> El bloque de abajo es SOLO para la máquina ORIGINAL (donde gmux NO movía el panel). Además usa
> GRUB; en Limine sería `/etc/default/limine` + `limine-update` (ver §11). Verificar SIEMPRE primero
> si `brightnessctl -d gmux_backlight set 50%` ya mueve el panel — si sí, saltarse este paso entero.

<details><summary>(solo máquina original — gmux no funcionaba) daemon AUX</summary>

```bash
# a) GRUB: forzar backlight nativo por AUX (revisar que no quede duplicado)
sudo cp /etc/default/grub /etc/default/grub.bak
sudo sed -i "s/\(GRUB_CMDLINE_LINUX_DEFAULT='\)/\1acpi_backlight=native amdgpu.backlight=1 /" /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg
# b) daemon único (auto-brillo curva + puente AUX/DPCD) — fuente en Apéndice A
sudo install -m755 $KIT/scripts/amdgpu-backlight.py /usr/local/bin/
sudo install -m644 $KIT/systemd/amdgpu-backlight.service /etc/systemd/system/
sudo install -m644 $KIT/udev/90-backlight-amdgpu.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo systemctl daemon-reload && sudo systemctl enable --now amdgpu-backlight
# c) REINICIAR (para que aparezca /sys/class/backlight/amdgpu_bl1 por los params de GRUB)
```
Teclas físicas de brillo/teclado en Hyprland: binds en `~/.config/hypr/config/binds.lua` (ver §5.b).
Ajustar curva de auto-brillo: editar `CURVE` en el script y `sudo systemctl restart amdgpu-backlight`.
</details>

### 5) VENTILADORES / control térmico (mbpfan) — evita throttling y tirones. Detalle en §10.
```bash
paru -S --noconfirm mbpfan            # AUR (no está en repos oficiales)
sudo tee /etc/mbpfan.conf >/dev/null <<'CONF'
[general]
low_temp = 50     # <50C: ventiladores al mínimo
high_temp = 55    # a partir de 55C suben con fuerza
max_temp = 68     # a 68C ya están al máximo (a ~60C ya soplan duro)
polling_interval = 1
CONF
sudo systemctl enable --now mbpfan    # permanente (sysinit.target)
```
> Independiente, **sin reinicio**. El i7-6920HQ corre caliente; sin esto la CPU llega a 100°C y
> hace *throttling* → las transiciones de Hyprland se sienten "toscas". No es la GPU.

### Orden y reinicios
1→2→3→4. Hay **dos reinicios** convenientes: uno tras audio+touchbar+GRUB, y listo. WiFi no
requiere reinicio. Al terminar: audio ✅, Touch Bar ✅, brillo+auto-brillo ✅, WiFi 2.4/5 GHz ✅.

---

## 0. Cómo continuar en otra sesión (control total, sin confirmaciones)

- **sudo sin contraseña YA está configurado** en `/etc/sudoers.d/99-ermesbatista-nopasswd`
  (`ermesbatista ALL=(ALL) NOPASSWD: ALL`). Por eso cualquier `sudo`, `paru`, `dkms` o
  `makepkg` funciona sin pedir clave.
- Para que **Claude Code tampoco pida confirmación** de cada comando, inicia la sesión con:
  ```
  claude --dangerously-skip-permissions
  ```
- Carpeta de trabajo de los drivers: `/home/ermesbatista/src/`
- **Para revertir el sudo sin contraseña al terminar** (recomendado por seguridad):
  ```
  sudo rm /etc/sudoers.d/99-ermesbatista-nopasswd
  ```

## 1. Hardware detectado

| Componente | Detalle |
|---|---|
| Modelo | **MacBookPro13,3** (15", 2016, chip **T1**) |
| CPU | Intel Core i7-6920HQ (Skylake) |
| GPU | Intel HD 530 + AMD Radeon Pro 460 (Baffin) |
| WiFi/BT | Broadcom **BCM43602** `[14e4:43ba]` → driver `brcmfmac` |
| Audio | Intel HDA + códec **Cirrus Logic CS8409** (+ CS42L83 + amplificador) |
| Touch Bar | USB `05ac:8600 Apple iBridge` (chip T1) |
| Kernel | `linux-cachyos` 7.1.3-2 (headers instalados) · GCC **16.1.1** |

## 2. Diagnóstico inicial (estado de cada cosa)

- **WiFi** ✅ El driver `brcmfmac` + firmware `brcmfmac43602-pcie.bin` están OK. `wlan0`
  existe y **escanea redes** (ERJEN, El Punto Del Marisco, ZTE-M8h8). No estaba roto,
  solo **desconectado**. → Solo falta conectarlo a la red del usuario.
- **Bluetooth** ✅ Funciona (controlador activo, `Powered: yes`).
- **Audio** ❌→🔧 El códec CS8409 carga y crea `card 0: CS8409 Analog`, PCM al máximo, sin
  mute… **pero no suena**. Es el problema clásico: el driver *mainline* no inicializa el
  **amplificador de los altavoces internos**. Solución: driver DKMS
  **`davidjo/snd_hda_macbookpro`**.
- **Touch Bar** ❌ `applespi` cargado pero **falta el módulo del Touch Bar**. Necesita driver
  DKMS del iBridge/T1. Nota clave: en este modelo **volumen y brillo están EN la Touch Bar**
  (no hay teclas físicas F), por eso "el volumen no funciona" es en parte consecuencia de esto.

## 3. Requisitos (ya cubiertos)

- `dkms` ✅ instalado · `git`, `base-devel` ✅ · `linux-cachyos-headers` 7.1.3-2 ✅
- ⚠️ **CLAVE — el kernel de CachyOS se compila con CLANG/LLVM, no con GCC.** El intento con
  GCC 16 falla con `gcc: error: unrecognized command-line option '-mstack-alignment=8'`,
  `-mllvm`, `-mretpoline-external-thunk`, etc. (flags exclusivos de clang). **La solución NO
  es `KCFLAGS`**, sino compilar los módulos out-of-tree con **`LLVM=1`** (clang 22.x, ya
  instalado en `/usr/bin/clang`). Comprobar el compilador del kernel:
  `cat /proc/version` o el warning "The kernel was built by: clang version 22.1.6".

## 4. AUDIO — driver CS8409 (davidjo/snd_hda_macbookpro) ✅ INSTALADO (falta reiniciar)

Instalado vía **DKMS + LLVM=1** para que sea **permanente** (se recompila solo en cada
actualización de kernel gracias al hook de pacman y `AUTOINSTALL="yes"`).

Pasos que se ejecutaron:
```bash
cd /home/ermesbatista/src/snd_hda_macbookpro   # (ya clonado, branch cb27cc4)
# 1) PERMANENCIA CON CLANG: editar dkms.conf para que DKMS siempre use clang:
#    MAKE="make"  →  MAKE="make LLVM=1"
# 2) Instalar como módulo DKMS (NO como make install suelto, que no sobrevive updates):
export LLVM=1
sudo -E env LLVM=1 ./install.cirrus.driver.sh -i -d
```
Resultado: `dkms status` → `snd_hda_macbookpro/0.1, 7.1.3-2-cachyos: installed (Original
modules exist)`. El módulo activo queda en `/lib/modules/<kernel>/updates/dkms/`.

Verificar **tras reiniciar** (la recarga en caliente no es posible, el códec está enlazado
a la tarjeta desde el arranque):
```bash
dkms status
modinfo -n snd_hda_codec_cs8409          # debe apuntar a updates/dkms/
speaker-test -t sine -f 440 -l1 -c2      # debe sonar por los altavoces internos
```
**Estado:** ✅ **FUNCIONANDO — probado tras reinicio (2026-07-17), suena por altavoces
internos. Sink `alsa_output.pci-0000_00_1f.3.analog-stereo`. Permanente vía DKMS+clang.**

> Notas: el error `SSL error ... signing_key.pem` durante `make install` es inofensivo.
> DKMS generó su propia MOK (`/var/lib/dkms/mok.key`). Si algún día se activa Secure Boot,
> habrá que enrolar esa MOK con `mokutil`.

## 5. TOUCH BAR — driver iBridge/T1 (2016/2017) ✅ FUNCIONANDO

Fuente que SÍ compila: fork **`marc-git/macbook12-spi-driver`**, rama
`touchbar-driver-hid-driver` (base del AUR `macbook12-spi-driver-dkms`). El repo original
`roadrunner2` ya no tiene la rama `touchbar`. El `apple-ib-drv` de t2linux es solo para T2.

Repo clonado en `/home/ermesbatista/src/touchbar-t1`. Módulos que necesita el T1:
`apple-ibridge` (núcleo), `apple-ib-tb` (touchbar), `apple-ib-als` (sensor de luz).
**`applespi` se OMITE** (el teclado/trackpad SPI ya está en el kernel mainline; compilar la
copia vieja causaría conflicto y además usa `<asm/unaligned.h>`, movido en 6.12+).

### Parches necesarios para kernel 7.1 (API cambiada)
Editados en las fuentes (y por tanto en `/usr/src/apple-ibridge-0.1/` que usa DKMS):
1. `apple-ib-als.c` y `apple-ib-tb.c`: `.remove` de `platform_driver` pasó a devolver
   `void` (kernel 6.11+). Cambiar `static int ..._platform_remove(...)` → `static void ...`
   y sustituir `return rc/return 0` por `dev_warn(...) + return;` / nada.
2. `apple-ibridge.c` línea ~425: `.report_fixup` ahora devuelve `const __u8 *`
   (`static const __u8 *appleib_report_fixup(...)`).
3. `apple-ibridge.c` `struct acpi_driver`: eliminar la línea `.owner = THIS_MODULE,`
   (el campo ya no existe).

### Instalación permanente (DKMS + LLVM=1)
`dkms.conf` propio en `/usr/src/apple-ibridge-0.1/`:
```
MAKE[0]="make LLVM=1 KDIR=/usr/lib/modules/$kernelver/build"
BUILT_MODULE_NAME[0..2]="apple-ibridge" / "apple-ib-tb" / "apple-ib-als"
AUTOINSTALL="yes"
```
```bash
sudo dkms add -m apple-ibridge -v 0.1
sudo dkms build -m apple-ibridge -v 0.1
sudo dkms install -m apple-ibridge -v 0.1
# Autoload al arranque (si no, hid-generic acapara el iBridge primero):
echo apple-ibridge | sudo tee /etc/modules-load.d/apple-ibridge.conf
```
Verificado: al `modprobe apple-ibridge` el driver arrebata el HID a `hid-generic`
(`apple-ibridge-hid 0003:05AC:8600.0001`) y crea los input devices de la Touch Bar.
Parámetros de `apple-ib-tb`: `fnmode` (1=multimedia por defecto), `idle_timeout=300`,
`dim_timeout`. Se pueden fijar en `/etc/modprobe.d/` si se quiere otro comportamiento.

**Estado:** ✅ **funcionando y permanente (DKMS+clang, autoload configurado).**

## 5.b Brillo de pantalla, retroiluminación del teclado y sensor de luz ✅

**Diagnóstico clave: el HARDWARE de los tres funciona; faltaban los ATAJOS en Hyprland.**
El escritorio es **Hyprland (Wayland)** con el shell **Noctalia** (`noctalia msg …`). En Wayland
nada controla brillo/teclado solo: hay que enlazar las teclas explícitamente.

Interfaces presentes y funcionales (probadas escribiendo directo):
- **Brillo pantalla:** `/sys/class/backlight/gmux_backlight` (max 1023). Lo maneja `apple_gmux`.
- **Teclado:** LED `/sys/class/leds/spi::kbd_backlight` (max 255), vía el driver SPI del teclado.
- **Sensor de luz:** `iio:device0` (name=`als`, driver `apple_ib_als`), lee `in_illuminance_input`.
- `brightnessctl` ya instalado y **funciona sin sudo** (no hicieron falta reglas udev).
- La Touch Bar **sí emite** todas las teclas (verificado por bitmap en /proc/bus/input/devices):
  `KEY_BRIGHTNESSUP/DOWN` (225/224), `KEY_KBDILLUMUP/DOWN` (230/229), volumen, multimedia.

Lo que se hizo (permanente, en la config del usuario):
- **Brillo de pantalla:** ya existían binds `XF86MonBrightnessUp/Down → noctalia msg brightness-up/down`
  en `~/.config/hypr/config/binds.lua`. Verificado: el comando cambia el brillo (688→460→688). OK.
- **Retroiluminación del teclado (NUEVO):** no existía ningún bind. Añadidos en `binds.lua`:
  ```lua
  hl.bind("XF86KbdBrightnessUp",   hl.dsp.exec_cmd("brightnessctl -d 'spi::kbd_backlight' set 15%+"), { locked=true, repeating=true })
  hl.bind("XF86KbdBrightnessDown", hl.dsp.exec_cmd("brightnessctl -d 'spi::kbd_backlight' set 15%-"), { locked=true, repeating=true })
  hl.bind("XF86KbdLightOnOff",     hl.dsp.exec_cmd("brightnessctl -d 'spi::kbd_backlight' set 50%"),  { locked=true })
  hl.bind("SUPER + F5", ... "15%-")   -- fallback teclado fisico
  hl.bind("SUPER + F6", ... "15%+")
  ```
  Noctalia NO tiene comando de teclado → se usa `brightnessctl` directo. Recargado con `hyprctl reload`.
- **Sensor de luz / brillo automático ✅ ACTIVADO (2026-07-17) — daemon propio por CURVA:**
  - **Se descartó `wluma`**: es de tipo "aprende con el tiempo" → lento en reaccionar y el
    usuario lo notó pesado. Desinstalado (`paru -Rns wluma`, borrado `~/.config/wluma` y
    `~/.local/share/wluma`).
  - En su lugar, la lógica de auto-brillo por **curva fija** vive ahora dentro del daemon
    ÚNICO **`/usr/local/bin/amdgpu-backlight.py`** (ver §5.b root cause). Lee el ALS
    (`iio` name=als → `in_illuminance_input`), aplica curva luz→brillo con suavizado EMA y
    rampa suave, y escribe el brillo **directo al panel por AUX** (NO a `amdgpu_bl1`), por lo
    que **no dispara el OSD de Noctalia** en los cambios automáticos. Respuesta inmediata.
  - **Respeta ajustes manuales:** si mueves el brillo con las teclas del Touch Bar, Noctalia
    escribe `amdgpu_bl1` (y muestra su control); el daemon lo detecta y lo guarda como OFFSET
    sobre la curva (estilo macOS), siguiendo tras él al cambiar la luz.
  - **Ajustar a gusto:** editar la tabla `CURVE = [(als, %), ...]` en el script y
    `sudo systemctl restart amdgpu-auto-brightness`. El ALS de Apple NO da lux: interior ≈ 2-6,
    tapado 0-1, ventana/sol decenas-cientos.
  - **Permisos:** el daemon corre como root (escribe sysfs directo). Además queda la regla
    udev `/etc/udev/rules.d/90-backlight-amdgpu.rules` (`chgrp video` + `g+w` a
    `amdgpu_bl1/brightness`) para que las teclas/apps de usuario también puedan escribirlo.

### CAUSA RAÍZ del brillo de pantalla (RESUELTA — pendiente REINICIAR)
Verificado por el usuario: escribir en `gmux_backlight` (incluso a 100) **no cambia el panel**.
La Touch Bar SÍ emite `KEY_BRIGHTNESSUP/DOWN` (capturado con evtest) y el bind SÍ corre el
comando; el problema es puro hardware/driver:
- `apple_gmux: Found gmux version 4.0.29 [indexed]` → el PWM del gmux **no controla el panel**
  en el MacBookPro13,3.
- `amdgpu: [drm] Skipping amdgpu DM backlight registration` → **amdgpu se negó a registrar su
  backlight nativo** porque la arbitración `acpi_video` eligió el gmux (vendor).
- El panel eDP-1 lo maneja **card1 = amdgpu** (card0 = i915). El control REAL del brillo es el
  PWM de amdgpu → hay que forzar que amdgpu lo registre.

**Fix aplicado (permanente, GRUB):** añadido `acpi_backlight=native` a
`GRUB_CMDLINE_LINUX_DEFAULT` en `/etc/default/grub` (backup en `/etc/default/grub.bak-*`) y
`sudo grub-mkconfig -o /boot/grub/grub.cfg`. Esto hace que la arbitración prefiera el backlight
nativo → amdgpu debe crear **`/sys/class/backlight/amdgpu_bl0`** que sí mueve el panel.

**TRAS 1er REINICIAR (2026-07-17):** `gmux_backlight` desapareció y se registró **`amdgpu_bl1`**
(ojo: `bl1`, no `bl0`; max=62451), único backlight, detectado por Noctalia. PERO al probar,
`brightnessctl`/Noctalia cambiaban el valor **sin mover el panel físico** (confirmado por el usuario).

### CAUSA RAÍZ REAL (2016 MBP): el PWM del GPU NO está cableado al panel → hay que usar AUX/DPCD
Diagnóstico definitivo (§debugfs `dri/0000:01:00.0/eDP-1/`):
- `amdgpu_current_backlight_pwm` **SÍ cambia** con el brillo (0xf484 ↔ 0x3a8a) → amdgpu genera
  bien el PWM, pero **el pin PWM no llega a la retroiluminación** en el MacBookPro13,3.
- El panel eDP (`/dev/drm_dp_aux0`) es **eDP v1.4** y sus DPCD dicen que soporta brillo por AUX:
  - `0x700=0x02` (eDP 1.4); `0x702=0x97` → **bit1 `BACKLIGHT_BRIGHTNESS_AUX_SET_CAP`=1** (2 bytes).
  - `0x721=0x04` → modo de control estaba en **PWM pin** (bits[1:0]=00). Ese era el problema.
- **PRUEBA EN VIVO que lo confirmó:** escribiendo DPCD por AUX el panel SÍ obedece:
  ```bash
  printf '\x06' | sudo dd of=/dev/drm_dp_aux0 bs=1 seek=$((0x721)) count=1 conv=notrunc  # modo AUX
  printf '\x20' | sudo dd of=/dev/drm_dp_aux0 bs=1 seek=$((0x722)) count=1 conv=notrunc  # brillo MSB (0x00-0xff)
  # (0x723 = LSB). El usuario confirmó: oscurece y aclara de verdad en todo el rango.
  ```

### FIX NATIVO PERMANENTE: `amdgpu.backlight=1` (fuerza AUX en vez de PWM)
El parámetro `amdgpu.backlight` estaba en `-1` (auto); como el panel no es OLED, auto elige **PWM**.
Forzando **`amdgpu.backlight=1`** amdgpu usa **AUX/DPCD** de forma nativa → `amdgpu_bl1` (y por tanto
`brightnessctl`, Noctalia y las teclas de brillo de la Touch Bar) controlan el panel REALMENTE,
sin scripts ni hacks. Añadido a GRUB (junto a `acpi_backlight=native`), backup en
`/etc/default/grub.bak-amdgpu-aux-*`, `grub-mkconfig` hecho:
```
GRUB_CMDLINE_LINUX_DEFAULT='... acpi_backlight=native amdgpu.backlight=1'
```

**RESULTADO TRAS EL 2º REINICIO (2026-07-17): `amdgpu.backlight=1` NO bastó.**
Comprobado: `cat /sys/module/amdgpu/parameters/backlight` → `1` (el param dice `1 = aux`),
`amdgpu_bl1` registrado (max=511000), PERO el panel sigue en **modo PWM**:
- DPCD `0x721 = 0x04` (bits[1:0]=00 → PWM), no `0x06` (AUX).
- Al mover `brightnessctl -d amdgpu_bl1` de 20%→90%, los registros AUX del panel
  `0x722/0x723` **se quedan en `0x0000`** → amdgpu escribe por PWM (pin no cableado), NO por AUX.
- Conclusión: en esta GPU **Baffin/Polaris (dce_v1/dm)** amdgpu ignora el modo AUX aunque se
  fuerce `amdgpu.backlight=1`. El AUX en vivo (escribir `0x721=0x06` + `0x722`) **sí mueve el
  panel** (reconfirmado por el usuario, barrido oscuro→brillante→medio).

### FIX DEFINITIVO QUE FUNCIONA: daemon ÚNICO amdgpu-backlight (AUX/DPCD + auto-curva) ✅
Como amdgpu no aplica AUX solo, se escribió un **daemon** que escribe el brillo REAL por AUX/DPCD.
**Evolución:** primero fueron 2 daemons (`amdgpu-aux-backlight` para el panel + `amdgpu-auto-brightness`
para el sensor); se **fusionaron en UNO** (`amdgpu-backlight`) por dos motivos: menos recursos y,
sobre todo, **evitar que el OSD de Noctalia saliera en cada cambio automático**.
- Script: **`/usr/local/bin/amdgpu-backlight.py`** · Servicio: **`amdgpu-backlight.service`**
  (systemd, `Nice=10`, ~5.5 MB, poll 0.3 s). Autodetecta el aux eDP (`EDP_DPCD_REV 0x700`),
  escribe `0x721=0x06` + `0x722/0x723` (nivel 16-bit), re-asserta cada ~3 s (DPMS/suspend),
  reabre el fd si el link cae.
- **REGLA DE ORO anti-OSD:** los cambios AUTOMÁTICOS (curva del ALS) van SOLO al panel por AUX;
  **NUNCA se escribe `/sys/class/backlight/amdgpu_bl1`**. Como Noctalia muestra su control al ver
  cambiar `amdgpu_bl1`, al no tocarlo el OSD **no aparece** en los ajustes automáticos.
- **Entrada manual:** las teclas de brillo del Touch Bar → Noctalia escribe `amdgpu_bl1` y muestra
  su OSD. El daemon detecta ese cambio (>1%) y lo toma como tu preferencia = **offset** sobre la
  curva (estilo macOS). Resultado: **el control SOLO sale cuando subes/bajas tú**.
- `amdgpu.backlight=1` y `acpi_backlight=native` en GRUB **se dejan** (registran `amdgpu_bl1`,
  que sirve de canal de entrada manual). El PWM nativo de amdgpu es inocuo (no cableado).
- Los antiguos `amdgpu-aux-backlight.*` y `amdgpu-auto-brightness.*` fueron **eliminados**.

**Estado:** ⌨️ Teclado ✅ · 🔆 Pantalla ✅ **FUNCIONANDO** vía daemon único AUX/DPCD (systemd).
💡 Auto-brillo por curva ✅ activo y silencioso (sin OSD en cambios automáticos). Ver §5.b.

## 5.c Escala de pantalla (HiDPI) — Hyprland ✅

Panel **2880×1800**. El escritorio es Hyprland con config **Lua** (Noctalia). La escala se define en
`~/.config/hypr/config/monitors.lua`:
```lua
hl.monitor({
    output    = MONITOR1,      -- eDP-1
    mode      = "preferred",   -- 2880x1800@60
    position  = "auto",
    scale     = "1.7",         -- pedido 1.7; Hyprland lo AJUSTA a 1.67 (válido más cercano). Más grande que 1.6.
})
```
- **Aplicar en vivo:** `hyprctl reload` (NO `hyprctl keyword monitor ...` → falla con "keyword can't
  work with non-legacy parsers" porque la config es Lua, no el parser legacy). Verificar:
  `hyprctl monitors | grep scale:`.
- **Escalas con divisor limpio** (buffer entero): 2880/1.5=1920, 2880/1.6=1800, 2880/1.8=1600, 2880/2=1440.
  Fraccionales no-limpias (p.ej. 1.7) → Hyprland las AJUSTA al valor válido más cercano (1.7 → 1.67).
  Fraccionales que NO dividen exacto Hyprland las ajusta/avisa.

**Estado:** ✅ **scale 1.7 (aplica 1.67)** (2026-07-19). Histórico: `auto`(=2) → 1.5 → 1.6 → **1.7/1.67** a petición del usuario (quería todo más grande).

## 5.d Trackpad estilo macOS — Hyprland ✅ (2026-07-18)

El trackpad SPI (`apple-spi-touchpad`) funciona por el driver mainline (§5), pero Hyprland arranca
con **defaults NO tipo Mac** (scroll invertido respecto a Mac, sin tap-to-click, sin clic por dedos).
Config en `~/.config/hypr/config/inputs.lua` dentro de `hl.config{ input.touchpad = {...} }`:
```lua
touchpad = {
    natural_scroll       = true,  -- contenido sigue a los dedos (como Mac)
    tap_to_click         = true,  -- tocar = clic
    tap_and_drag         = true,  -- tocar-y-arrastrar
    clickfinger_behavior = true,  -- 2 dedos = clic derecho, 3 dedos = clic medio
    disable_while_typing = true,  -- ignora el trackpad al teclear
    drag_lock            = true,
}
```
> ⚠️ Las claves del wrapper Lua van con **guion bajo** (`tap_to_click`, no `tap-to-click`) y anidadas
> en `input.touchpad`. Referencia de nombres: `/usr/share/hypr/stubs/hl.meta.lua`.

**Gestos (macOS):** swipe **horizontal de 3 y 4 dedos = cambiar de escritorio** (spaces). Antes el de
3 dedos hacía close/fullscreen/float (no-Mac) y solo el de 4 cambiaba workspace. Config final:
```lua
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 4, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 3, direction = "up",         action = "fullscreen" })
hl.gesture({ fingers = 3, direction = "down",       action = "close" })
```
- **Aplicar:** `hyprctl reload`. Verificar: `hyprctl getoption input:touchpad:natural_scroll`
  (usa guiones aquí: `tap-to-click`, `tap-and-drag`).

**Estado:** ✅ **FUNCIONANDO** — natural scroll + tap-to-click + clickfinger + tap&drag + disable-while-typing,
gestos de 3/4 dedos para spaces. Ajustable a gusto (scroll factor, invertir gesto, etc.).

### Teclado — acentos estilo macOS (Option + letra) ✅ (2026-07-18)
En macOS los acentos salen con **Option + letra** (o press-and-hold). En Wayland NO existe el popup
press-and-hold; el equivalente más cercano y que **no rompe las comillas para programar** es la
variante **`us altgr-intl`** (dead keys solo por AltGr = Alt derecha). En `inputs.lua`:
```lua
kb_layout  = "us",
kb_variant = "altgr-intl",
```
Uso: **AltDcha + a/e/i/o/u** → á é í ó ú · **AltDcha + n** → ñ · **AltDcha + '** luego `u` → ü.
`'` `"` `` ` `` `~` siguen normales (importante para código). Descartado `us intl` a secas porque
secuestra esas teclas como dead keys. Aplicar: `hyprctl reload`.

## 6. WiFi — ✅ 2.4 **y 5 GHz FUNCIONANDO** (2026-07-17)

### ✅ SOLUCIÓN QUE FUNCIONÓ (5 GHz habilitado, probado conectado a internet)
**La causa NO era falta de clm_blob**, sino la **NVRAM específica de placa del MacBookPro13,3**.
El firmware stock (7.35.177.61) trae el CLM interno con 5 GHz; solo faltaban los parámetros de
placa correctos (`boardtype`/`sromrev`) para que el firmware encienda el radio de 5 GHz.

Pasos EXACTOS (permanentes):
1. **NVRAM del 13,3** = adjunto **285753** del bug kernel 193121 (comment #63, Andy Holst, mismo
   modelo). Params clave: `boardrev=0x1101  sromrev=11  boardtype=0x073e  ccode=X3  regrev=15`.
   Copia guardada en `~/src/wifi-fw/brcmfmac43602-pcie.13-3.WORKING.txt`.
   - Editar `macaddr=` con la MAC real de la tarjeta = **`00:90:4c:0d:f4:3e`** (es la permaddr
     real de este OTP, `ethtool -P wlan0`).
   - Instalada con DOS nombres en `/lib/firmware/brcm/`:
     `brcmfmac43602-pcie.txt` **y** `brcmfmac43602-pcie.Apple Inc.-MacBookPro13,3.txt`.
   - ⚠️ Sobrevive a updates de `linux-firmware` (es un .txt propio, el paquete no lo trae).
2. **`/etc/modprobe.d/brcmfmac.conf`** → `options brcmfmac feature_disable=0x82000` (estabiliza).
3. Recargar: `nmcli radio wifi off; modprobe -r brcmfmac_wcc brcmfmac; modprobe brcmfmac`.
   → `iw phy info` ahora muestra **Band 1 Y Band 2**. Conectado a **Servextex-Megared** (5745
   MHz, canal 149), señal -48 dBm, ping OK. Perfil NM con autoconnect (prioridad 10).

### Lo que NO funciona (descartado, no repetir)
- ⚠️ **`clm_blob` de OTRO chip (ej. 43570) CUELGA el chip:** `brcmf_pcie_setup: Dongle setup
  failed` y `wlan0` no sube. El firmware valida el chip en el CLM. Revertir = borrar el .clm_blob
  y recargar. (El 5 GHz NO necesita clm_blob externo, ver arriba.)
- ⚠️ **NVRAM genérica / de otro modelo también cuelga** (`Dongle setup failed`). Debe ser la del
  13,3 (`boardtype=0x073e`). El gist `MikeRatcliffe` colgó por esto.
- El firmware `.bin` de macOS (`dlarray`, v7.77.0.0, tipo **bmac**) NO sirve: protocolo host
  distinto a brcmfmac (fullmac). El CLM de macOS es "tipo 1" (con punteros), no convertible
  fácil al "BLOB tipo 2" de brcmfmac. Nada de esto hizo falta.

### ⚠️ SEÑAL más débil que macOS — INVESTIGADO, sin fix por flags (2026-07-17)
**Síntoma:** a ~80 cm del router Linux marca **~-60 dBm** mientras macOS y el celular reciben lleno.
La tarjeta es **Apple `[106b:015a]`**. La NVRAM en uso (att-285753) está derivada de un ref de lab
**43569** (lo dicen sus comentarios), con solo 2 antenas y sin LNA externo.
**Pruebas A/B controladas (10 lecturas promediadas, sin mover la laptop):**
- `rxchain=7`+`aa2g/aa5g=7` (3ª antena RX): **-60 dBm** → **igual** que 2 antenas (-60). Sin efecto.
- `boardflags=0x10401001` (LNA externo 2G+5G ON): **-60 dBm** → **igual**. Sin efecto.
- ⚠️ OJO metodológico: las antenas WiFi van EN LA TAPA; el ángulo de tapa y la posición del cuerpo
  cambian la señal **15-20 dB**. Una medición aislada engaña (vi -41 momentáneo que NO se reprodujo).
  Solo vale A/B seguido sin moverse.
**Conclusión:** cambiar flags sueltos NO sirve; el problema es que **toda la tabla de calibración RF**
(femctrl, swctrlmap, ganancias, PA) es de otra placa y no corresponde al front-end real del MacBook.
Igualar a macOS exigiría la calibración exacta de Apple (OTP del chip / macOS) — nivel investigación,
incierto (ver §6.b). **Todo revertido a la NVRAM original 2-antenas probada.** El throughput real es
bueno igual (585-1170 Mbit/s). Opciones reales si molesta el número: dongle USB (MT7921/RTL8812AU,
5 GHz nativo Linux, ~US$15) · usar 2.4 GHz (más alcance) · aceptar (internet va bien).

### Notas red del usuario
- 5 GHz: SSID **`Servextex-Megared`** (canal 149), clave `V7JPT3XXTWNPA`. ✅ conectado.
- `phy` es self-managed (`country 99` vía `ccode=X3` de la nvram); canales 36-48 y 149-165
  usables, DFS (52-144) en modo pasivo. Suficiente para la red del usuario (149).

### macOS sigue instalado (partición APFS `nvme0n1p2`, 232 GB)
- Montado en solo-lectura con `apfs-fuse` (AUR). Volumen 0 = Data (FileVault), volumen 3 =
  Sistema. El firmware WiFi de Apple está en `/usr/share/firmware/wifi/` **pero solo para
  chips nuevos** (4355/4364/4377/4387/4388) en formato `.trx/.clmb/.txcb`.
- El firmware del **43602 está EMBEBIDO** en el binario Mach-O
  `IO80211FamilyLegacy.kext/.../AirPortBrcmNIC` (símbolos `_dlarray_43602a2pci` /
  `_dlarray_43602pci`). Extraerlo y convertirlo al formato brcmfmac (con CLM compatible) es
  ingeniería inversa de nivel investigación, **sin método documentado que funcione** y de
  resultado incierto. (t2linux solo soporta los chips nuevos por esto mismo.)

### Opciones realistas (pendiente de decisión del usuario)
1. **Dongle USB WiFi con 5 GHz nativo en Linux** (MediaTek MT7612U/MT7921 o RTL8812AU,
   ~US$10-20): plug-and-play, 5 GHz garantizado. **Recomendado.**
2. **2.4 GHz en la tarjeta interna**: funciona ya; solo falta la clave correcta del SSID
   "ERJEN" de 2.4 GHz. Nota: el AP ofrece `FT-PSK` (802.11r) — si el handshake falla,
   crear el perfil con `wifi-sec.pmf 1` (deshabilitar PMF).
3. **Intento de extracción del firmware embebido**: alto esfuerzo, incierto, puede colgar
   el WiFi. No recomendado como vía fiable.
4. **Dual-boot a macOS** para tareas que requieran WiFi rápido (macOS está intacto).

**Estado:** ⚠️ 2.4 GHz funcional (falta clave correcta) · 5 GHz **no viable** con la tarjeta
interna sin los blobs de Apple.

### 6.b Intento de extracción del firmware embebido (❌ YA NO HACE FALTA — resuelto en §6)
> **OBSOLETO:** el 5 GHz se resolvió con la NVRAM del 13,3 (§6), sin extraer nada de macOS.
> Se deja como referencia técnica. El binario `AirPortBrcmNIC` se conserva en `~/src/wifi-fw/`.
El usuario pidió intentarlo. Progreso guardado:
- **Binario de macOS copiado a `~/src/wifi-fw/AirPortBrcmNIC`** (8.6 MB) — ya NO hace falta
  remontar macOS. (macOS: `apfs-fuse -o ro,vol=3 /dev/nvme0n1p2 /mnt/macos`; clave FileVault
  del vol 0 Data = `Ermes200010`.)
- Símbolos localizados (`llvm-nm --print-size --defined-only`):
  `_dlarray_43602a2pci` @ `0x6ee7e0` (chip es **rev 2** → usar este),
  `_dlarray_43602pci` @ `0x6808b0`. Tipo `D` (data). El motor CLM (`_clm_*`) está en el
  binario como código; el CLM como DATO va dentro/junto al dlarray.
- **Plan de reanudación:**
  1. Calcular el tamaño del array (diferencia con el siguiente símbolo o layout de sección
     `__DATA`) y extraer los bytes con `llvm-objcopy --dump-section` o `dd` sobre el offset
     de fichero (vaddr − sección.vmaddr + sección.fileoff).
  2. Probar la imagen extraída como `/lib/firmware/brcm/brcmfmac43602-pcie.bin` (respaldar
     antes el original `.bin.zst` de linux-firmware).
  3. Recargar: `systemctl stop NetworkManager; modprobe -r brcmfmac_wcc brcmfmac;
     modprobe brcmfmac; systemctl start NetworkManager` y comprobar `iw phy | grep Band`
     (¿aparece Band 2 / 5 GHz?).
  4. Si "Dongle setup failed" → revertir restaurando el `.bin` original y recargar.
- Herramientas ya instaladas: `apfs-fuse` (AUR), `llvm-nm/objdump/objcopy`.

## 8. SUSPENSIÓN — pantalla negra al abrir la tapa (2026-07-17)

### Síntoma
Al cerrar la tapa el sistema suspendía, pero al abrirla **la pantalla no encendía (solo el
teclado)** y había que apagar a la fuerza. En logs: `PM: suspend entry (deep)` y **ni una línea
más** en ese boot → el GPU AMD (Baffin/Polaris) **se cuelga al reanudar desde `deep` (S3)**.
Es el fallo clásico de resume en los MacBook de doble GPU (Intel i915 + amdgpu).

### CAUSA RAÍZ y FIX: usar `s2idle` en vez de `deep`
`cat /sys/power/mem_sleep` daba `s2idle [deep]` → estaba usando **deep (S3)**, que no reanuda
el GPU. La solución fiable en este hardware es **suspend-to-idle (`s2idle`)**.
- **En vivo:** `echo s2idle | sudo tee /sys/power/mem_sleep`.
- **Permanente (GRUB):** añadido **`mem_sleep_default=s2idle`** a `GRUB_CMDLINE_LINUX_DEFAULT`
  en `/etc/default/grub` (backup `grub.bak-suspend-*`), `grub-mkconfig -o /boot/grub/grub.cfg`.
  Línea final: `... acpi_backlight=native amdgpu.backlight=1 mem_sleep_default=s2idle`.

### Red de seguridad para el brillo al despertar
El daemon de brillo escribe por `/dev/drm_dp_aux0`; ese fd puede quedar viejo tras resume. Hook
**`/usr/lib/systemd/system-sleep/99-macbook-resume`** (755) que en `post` hace
`systemctl restart amdgpu-backlight.service` → reabre el AUX y reasienta el brillo del panel.

### SEGUNDO CUELGUE (2026-07-17, ~09:51) — CON s2idle YA PUESTO
Aun con `s2idle` activo (`/sys/power/mem_sleep` = `[s2idle] deep`), al abrir la tapa la
**pantalla SÍ encendió pero quedó congelada**, y **WiFi (`brcmfmac`) y Touch Bar
(`apple_ibridge`) muertos** → apagado a la fuerza. Log del boot -1 termina en
`PM: suspend entry (s2idle)` sin más. Culpable conocido en T1: `brcmfmac` y `apple_ibridge`
no reanudan y cuelgan el sistema.

**FIX ampliado del hook `99-macbook-resume`** (backup `.bak-suspend2`): ahora en **`pre`**
descarga los módulos frágiles (`apple_ib_tb`, `apple_ib_als`, `apple_ibridge`, `brcmfmac_wcc`,
`brcmfmac`) y en **`post`** recarga WiFi (`modprobe brcmfmac`) + reinicia `amdgpu-backlight`.
Logea con tag `macbook-sleep` (`journalctl -t macbook-sleep`).

⚠️⚠️ **LECCIÓN IMPORTANTE — NO descargar `apple_ibridge` para suspender.** Se probó descargar
`apple_ibridge`/`apple_ib_tb` en `pre` y NO se recuperan por software: tras recargar módulo o
incluso re-enumerar el USB del iBridge (`05ac:8600`, unbind/bind de `1-3`), el display queda
clavado en `apple-ibridge APP7777:00: tb: Touchbar deactivated` y **nunca vuelve a activarse**.
`fnmode`/`idle_timeout` (`/sys/module/apple_ib_tb/parameters/`) son de **solo lectura**, no se
togglean en caliente. El estado del display DFR lo maneja el firmware del **chip T1** y solo se
re-inicializa limpio **AL ARRANCAR** → si se descarga el stack iBridge, la barra queda muerta
hasta reiniciar.

**Estrategia corregida:** el cuelgue real lo causa **solo `brcmfmac` (WiFi)**; la barra estaba
muerta porque TODO el sistema se congeló, no por fallo propio de `apple_ibridge`. El hook
`99-macbook-resume` ahora **solo descarga/recarga `brcmfmac`** en pre/post + reinicia
`amdgpu-backlight`. **NO toca la Touch Bar** (debe reanudar sola si el sistema no se congela).

**Estado:** 🔧 hook corregido (solo WiFi). **Requiere REINICIO** para recuperar la Touch Bar
(quedó muerta tras las pruebas de descarga del stack iBridge). Tras reiniciar: **pendiente que el
usuario cierre/abra la tapa** para validar el resume real con el hook nuevo. Si aún cuelga, el
siguiente sospechoso es el GPU AMD Polaris (probar `amdgpu.runpm=0` o, último recurso,
deshabilitar suspend al cerrar tapa y solo apagar pantalla/bloquear).

### INTENTO FALLIDO (2026-07-18): "deshabilitar suspensión" — DESCARTADO
Primero se enmascararon los sleep targets + logind ignore (el sistema nunca se dormía). **MALA
IDEA:** en una laptop que va al bulto, quedarse encendida = sobrecalentamiento. Revertido
(`systemctl unmask ...`, borrado el drop-in `10-macbook-nosuspend.conf`). NO repetir este enfoque.

### RESOLUCIÓN REAL (2026-07-18): HIBERNACIÓN (bag-safe) — configurada, PENDIENTE VALIDAR
**Hallazgo clave (repo Dunedan/mbp-2016-linux):** en el 13,3 el **resume de SUSPEND (S3/s2idle)
solo es fiable con la GPU Intel activa; con la AMD activa falla** — y el panel de esta máquina está
en la AMD. Por eso el suspend cuelga. La vía fiable para el caso "va al bulto" es **HIBERNAR**
(apaga del todo → sin calor ni batería en el bulto; el resume re-inicializa el hardware como un
arranque, así vuelven Touch Bar, audio, WiFi, BT, abanicos). El resume de hibernación NO pasa por
la ruta de "despertar" del GPU que cuelga.

**Configuración aplicada (permanente):**
1. **Swap en disco** (zram NO sirve para hibernar): `/swapfile` de **20 GB** en `/` (ext4), en
   `/etc/fstab` (`/swapfile none swap defaults,pri=10 0 0`). zram queda con prioridad mayor (100)
   para swap normal; el swapfile (pri 10) es el destino de la imagen de hibernación.
2. **resume en GRUB** (`/etc/default/grub`, backup `grub.bak-hibernate-*`):
   `resume=UUID=e25995b3-2261-4dff-88b9-5d7559388d64 resume_offset=60205056`
   (offset = `filefrag -v /swapfile | grep '^ *0:' | awk '{print $4}' | tr -d '.'`; recalcular si
   se recrea el swapfile). `grub-mkconfig -o /boot/grub/grub.cfg` + `mkinitcpio -P` hechos. El hook
   `systemd` de mkinitcpio hace el resume automático con esos params (no hace falta hook `resume`).
3. **Tapa cerrada → hibernar**: `/etc/systemd/logind.conf.d/10-macbook-hibernate.conf`
   (`HandleLidSwitch=hibernate`, `HandleLidSwitchExternalPower=hibernate`, `...Docked=hibernate`).
4. El hook `99-macbook-resume` (§8 arriba) también corre en hibernación (descarga/recarga
   brcmfmac, reinicia amdgpu-backlight) → ayuda a que WiFi/brillo vuelvan.

**PENDIENTE:** requiere **1 reinicio** (para que `resume=` esté activo) y luego **validar** con
`systemctl hibernate` observando: ¿apaga del todo? ¿al pulsar power restaura la sesión y vuelve
todo el hardware? Si el resume de hibernación TAMBIÉN falla en esta Polaris, el fallback bag-safe
es **apagar** (el arranque en frío sí trae todo). Próximo paso opcional tras validar: política de
inactividad (idle → apagar pantalla/bloquear; idle largo → hibernar) con hypridle.

## 9. WiFi — el "porcentaje bajo" NO es potencia de TX (2026-07-17)
El usuario veía "59%/72%" y pidió "subir la potencia". Aclaración: ese número es la **señal de
BAJADA** (cuánto oye la laptop al router, RSSI ≈ -61 dBm), **no** la potencia de transmisión de
la tarjeta. La TX ya está al **máximo (30-31 dBm)** y el enlace negocia **1170 Mbit/s** en 5 GHz
(canal 149) → rendimiento excelente. En 5 GHz el % se ve conservador (no penetra paredes como
2.4 GHz) pero la velocidad real es altísima. `iw dev wlan0 set txpower fixed 3000` se acepta pero
es cosmético en brcmfmac (fullmac: el firmware manda). No hay nada roto; el % bajo no se "sube"
desde la laptop (dependería del router / distancia / obstáculos). `ccode=X3` (country 99) sigue.

## 10. VENTILADORES / TÉRMICO — mbpfan (2026-07-18)

### Síntoma
Las **transiciones entre escritorios en Hyprland se sentían "toscas"** (tirones al cambiar de
workspace / mover ventanas). El usuario sospechaba que la GPU no aceleraba por hardware.

### Diagnóstico — NO era la GPU
- **Aceleración por hardware OK:** `glxinfo`/`eglinfo` → `direct rendering: Yes`, renderer
  `AMD Radeon RX (radeonsi, polaris11)`. No hay software rendering.
- **Hyprland ya renderiza en la AMD Pro 460** (la potente): el log de aquamarine dice
  `gpu /dev/dri/card1 becomes primary drm` + `Renderer: AMD Radeon RX` y el panel `eDP-1`
  cuelga de card1 (AMD). No hay que forzar `AQ_DRM_DEVICES`. **`gpu_busy_percent` = 0%** al
  cambiar de escritorio → la GPU ni se inmuta.
- **La GPU escala bien:** `pp_dpm_sclk` llega a nivel 7/7 (907 MHz) cuando hace falta.
- **CAUSA REAL = throttling térmico de la CPU.** `sensors` → `Package id 0: +100.0°C`
  (high=crit=100). El i7-6920HQ a 100°C se frena solo → los picos de CPU del compositor al
  animar se cortan = tirones. **`mbpfan` y `thermald` estaban inactivos**: los ventiladores
  giraban a ~4000 RPM cuando el `applesmc` permite hasta **5927/5489 RPM**.

### Control de ventilador (referencia sysfs)
`applesmc.768` expone control manual (útil para pruebas en vivo):
```bash
base=/sys/devices/platform/applesmc.768
echo 1 | sudo tee $base/fan1_manual $base/fan2_manual            # tomar control manual
cat $base/fan1_max                                               # 5927
echo 5927 | sudo tee $base/fan1_output                          # forzar al máximo
echo 0 | sudo tee $base/fan1_manual $base/fan2_manual            # devolver a automático
```
Prueba que confirmó el diagnóstico: forzando los fans al máximo la CPU bajó **100°C → 73°C** y
el "tosco" desapareció.

### FIX PERMANENTE — mbpfan (curva agresiva)
`mbpfan` NO está en repos oficiales → **AUR** (`paru -S mbpfan`). Config en `/etc/mbpfan.conf`:
```
low_temp = 50     # <50C: mínimo
high_temp = 55    # a partir de 55C sube con fuerza
max_temp = 68     # a 68C al máximo → a ~60C ya sopla duro (el usuario NO quiere sentir calor)
polling_interval = 1
```
`sudo systemctl enable --now mbpfan` → `enabled/active`, arranca en `sysinit.target`. mbpfan toma
el control manual del `applesmc` él mismo (`fanX_manual=1`) y modula según temperatura.
- **Permanencia ante updates:** pacman respeta `/etc/mbpfan.conf` (crea `.pacnew`, no lo pisa).
- **Ajuste de ruido:** subir `high_temp`/`max_temp` = más silencio, algo más de calor. Bajar = más
  frío y más ruido. Curva actual pensada para "no sentir calor nunca".

### Nota Hyprland (cosmético, complementario)
En `~/.config/hypr/config/decorations.lua` se bajó el blur (`passes 4→2`, `size 5→3`,
`new_optimizations`/`xray = true`) y las opacidades a `1.0`. **No era el cuello** (la GPU sobra),
pero quita carga gráfica innecesaria a 2880×1800@scale1.5 (ver §5.c). Se puede restaurar el blur sin problema.

### Sin márgenes ni bordes — aprovechar toda la pantalla (2026-07-20) ✅ CONFIRMADO por el usuario
El usuario no quería los **gaps (márgenes) ni bordes** de Hyprland — dejaban un marco de wallpaper
alrededor de las ventanas y esquinas redondeadas que se veían feas. En
`~/.config/hypr/config/decorations.lua` (backup `.bak-AAAAMMDD-HHMMSS` antes de tocar):
```lua
general = {
    gaps_in     = 0,   -- era 3  (separación entre ventanas)
    gaps_out    = 0,   -- era 8  (margen ventana↔borde de pantalla = el marco de wallpaper)
    border_size = 0,   -- era 2  (borde de color alrededor de cada ventana)
}
decoration = {
    rounding = 0,      -- era 10 (esquinas redondeadas → asomaban wallpaper en las esquinas)
}
```
Aplicar en vivo: `hyprctl reload`. Verificar: `hyprctl getoption general:gaps_out` (→ `css gap data: 0 0 0 0`),
`hyprctl getoption general:border_size` / `decoration:rounding` (→ `int: 0`).
- Las ventanas quedan **borde a borde, cuadradas, sin borde** → máximo espacio útil.
- Si algún día quiere **distinguir la ventana activa** en modo mosaico, subir `border_size` a `1`/`2` (cuesta poquísimo espacio).
- Nota: la barra Noctalia tiene su propio redondeo inferior (`radius_bottom_left/right = 12` en
  `~/.config/noctalia/config.toml`); si molesta ese detalle, ahí se pone a `0` (independiente de Hyprland).

### Pendiente / futuro
**Undervolt de la CPU** (`intel-undervolt`) para que el i7 corra más frío con el mismo rendimiento
= menos ruido de ventilador y cero throttling. En MacBook el MSR de undervolt PUEDE estar bloqueado
por firmware; hay que probar. Aún no aplicado (se explicó al usuario primero).

**Estado:** 🌡️ **FUNCIONANDO** — mbpfan activo y permanente, curva 50/55/68. CPU se mantiene
fresca bajo carga, transiciones fluidas. GPU descartada como problema (rinde de sobra).

## 11. Configuración en MÁQUINA NUEVA (2026-07-18) — desviaciones del runbook

> Se aplicó el runbook a una MacBookPro13,3 recién instalada. **Hardware idéntico**, pero el
> entorno base trae diferencias que INVALIDAN partes del runbook original. Documentadas aquí.

### ⚠️ DESVIACIÓN 1 — Bootloader **Limine**, NO GRUB
Esta CachyOS usa **Limine 12.5.0**. **`/etc/default/grub` NO existe** y `grub-mkconfig` no aplica.
Todo párametro de kernel que el runbook mete en GRUB va aquí:
```bash
# 1) editar la línea KERNEL_CMDLINE[default] en /etc/default/limine (añadir params antes de la ")
sudo sed -i 's|\(KERNEL_CMDLINE\[default\]+="[^"]*\)"|\1 PARAM1 PARAM2"|' /etc/default/limine
# 2) regenerar /boot/limine.conf
sudo limine-update
```
Verificar: `sudo grep cmdline /boot/limine.conf` y `cat /proc/cmdline` tras reboot.
Equivalencias runbook: brillo `acpi_backlight=native amdgpu.backlight=1` · hibernación `resume=UUID=...
resume_offset=...` → todo por Limine, NO GRUB. Backups en `/etc/default/limine.bak-*`.

### ⚠️ DESVIACIÓN 2 — sudo NOPASSWD hay que RECREARLO
El NOPASSWD del §0 era de la otra máquina. En la nueva se recreó:
`/etc/sudoers.d/99-ermesbatista-nopasswd` (`ermesbatista ALL=(ALL) NOPASSWD: ALL`, chmod 440).

### ⚠️ DESVIACIÓN 3 — el ALS expone `in_illuminance_raw`, no `in_illuminance_input`
En esta base hay varios sensores (`macsmc_light`, `hid_sensor_als` además de `apple_ib_als`). El
device `name=als` solo tiene **`in_illuminance_raw`**. El daemon v2 (abajo) prueba `input` y cae a
`raw`. La curva se recalibra sobre valores raw (editar `CURVE` + restart, sin reboot).

### Estado de la instalación (2026-07-18)
- **AUDIO ✅** DKMS CS8409 `LLVM=1` instalado (AUTOINSTALL, updates/dkms). Suena tras reboot.
- **TOUCH BAR ✅ FUNCIONA (fiable tras arreglar la carrera)** DKMS apple-ibridge (3 módulos, 3
  parches kernel 7.1, `LLVM=1`) + autoload (`/etc/modules-load.d/apple-ibridge.conf`). Ver §15 para
  la CAUSA REAL de la intermitencia y el fix.
  ⚠️ ERRORES MÍOS PREVIOS (corregidos): (1) afirmé "cargó/funciona" solo por dmesg sin verificar la
  pantalla; (2) declaré "imposible en kernel 6.3+ (t2linux #12), hace falta recompilar el kernel" —
  **FALSO**: el usuario confirmó que la barra SÍ enciende con este kernel/driver (lo había hecho en
  una MBP 2017 idéntica). La lección de t2linux #12 aplica a OTRO síntoma; aquí el problema era una
  carrera de binding (hid_sensor_hub), NO el kernel. Fix real en §15.
- **WiFi 5 GHz ✅** NVRAM del 13,3 en `/lib/firmware/brcm` (2 nombres) + `feature_disable=0x82000`.
  permaddr real = `00:90:4c:0d:f4:3e` (igual a la del kit — es el default Broadcom). **Band 1 y 2 OK.**
- **VENTILADORES ✅** `mbpfan` (AUR) + `/etc/mbpfan.conf` curva 50/55/68 + `enable --now`.
- **BRILLO 🔧 preparado (pendiente reboot)** — ver §5.b daemon **v2** anti-jank.

### 🔆 Daemon de brillo **v2** — arreglo del JANK de animaciones (2026-07-18)
**Diagnóstico del jank (confirmado por el usuario):** la config de brillo (no la térmica) degradaba
las animaciones del mouse y transiciones (saltos + lentitud). CAUSA: cada transacción **AUX/DPCD**
del daemon se serializa con los *atomic-commit* del compositor (misma capa DC de amdgpu). El v1
(Apéndice A) hacía **2 transacciones por cambio**, **re-asertaba cada 3 s** aunque nada cambiara, y
con **deadband 0.6% + ALS ruidoso** escribía casi cada 0.3 s → el compositor perdía frames.
**Arreglos en v2** (`/usr/local/bin/amdgpu-backlight.py`, kit actualizado):
1. **UNA sola transacción AUX** de 3 bytes `[modo,MSB,LSB]` en `0x721..0x723` (antes 2).
2. **SIN reassert periódico** (el hook system-sleep reinicia el servicio en resume).
3. **Deadband 4% + poll 1 s** → en luz estable **CERO escrituras AUX** = cero jank.
Resultado esperado: solo un hitch aislado al cambiar la luz de verdad. **Pendiente medir on/off tras
reboot** para confirmar. Service/udev iguales al Apéndice A.

## 12. FLUIDEZ / JANK de Hyprland en la GPU Polaris (2026-07-18) — ✅ RESUELTO

> Síntoma: mouse y transiciones de escritorio dan **saltos** ("como si no tuviera driver gráfico"),
> pese a que la GPU **sí acelera** (`glxinfo`: direct rendering Yes, renderer AMD radeonsi polaris11).
> El usuario estaba 100% seguro de que era el brillo; **NO era**. Bisección de causas (documentar
> cada una para replicar rápido en otra máquina / reformateo).

### DATO CLAVE del usuario
**Antes de nuestros cambios el sistema estaba FLUIDO** — con el blur (size5/passes4) y el VRR (=3)
**activados por default**. Se dañó **después de aplicar "los arreglos"** (audio, touchbar, wifi,
ventiladores, brillo + reboot). ⇒ el jank lo **introdujo uno de NUESTROS cambios**, no un default.

### Descartado (NO era la causa)
- **Daemon de brillo** — parado → seguía igual. En reposo escribía 0 AUX (v2 con deadband).
- **Scale fraccional 1.6** — probado scale 2 (entero) → seguía igual.
- **VRR** — probé `vrr=0`: bajó `gpu_busy` de 100% a 0% PERO el salto SIGUIÓ. Y estaba fluido antes
  CON `vrr=3`. ⇒ NO era la causa (el 100% era síntoma, no causa). Revertido a `vrr=3`.
  ⚠️ LECCIÓN: no confundir correlación (GPU 100%) con causa.
- **Blur / opacidades** — probé blur off + opacidad 1 → seguía igual. Y estaba fluido antes CON blur.
  ⇒ NO era la causa. Revertido a original (size5/passes4, 0.95/0.85).

### ✅✅ CAUSA CONFIRMADA (2026-07-18) — los params de kernel del brillo
Tras quitar **`acpi_backlight=native amdgpu.backlight=1`** del cmdline de Limine (`/etc/default/limine`
+ `limine-update`), deshabilitar el daemon de brillo y reiniciar → **VOLVIÓ LA FLUIDEZ, total.**
Confirmado por el usuario. **ESOS DOS PARÁMETROS ERAN EL JANK.** Además, sin ellos, **la Touch Bar
también arrancó bien** (antes esos params/el lío del brillo la estorbaban).

**🥇 REGLA para esta máquina (y probablemente la 2017 idéntica):**
1. **NO añadir `acpi_backlight=native` ni `amdgpu.backlight=1`.** Rompen la fluidez del compositor
   (mouse y transiciones a saltos) y NO hacen falta.
2. **El brillo de pantalla funciona NATIVO** por `/sys/class/backlight/gmux_backlight` (max 1023).
   Las teclas de brillo del Touch Bar (Noctalia) lo mueven de verdad. **NO hace falta el daemon AUX
   `amdgpu-backlight.py` ni nada del §4/§5.b/Apéndice A** — todo ese drama era de la máquina ORIGINAL
   (donde gmux no movía el panel); en ESTA sí lo mueve. Se dejó el daemon instalado pero
   **DESHABILITADO** (`systemctl disable amdgpu-backlight`).
3. En resumen: el §5.b entero (amdgpu.backlight=1 + AUX + daemon) **era la fuente del problema aquí.**

⚠️ LECCIÓN de método: perseguí VRR y blur (correlación con GPU 100%) sin ver que el usuario decía que
"antes estaba fluido". La causa era un cambio NUESTRO (los params), no un default. Escuchar el dato
"antes funcionaba" y bisecar NUESTROS cambios primero.

### ⌨️ Luz de teclado (Touch Bar) — binds Hyprland (2026-07-18) ✅
Hardware OK: LED `/sys/class/leds/spi::kbd_backlight` (max 255), `brightnessctl` sin sudo. Faltaban
los binds en `~/.config/hypr/config/binds.lua` (Noctalia no tiene comando de teclado → brightnessctl
directo). Añadidos y **probados funcionando** (botones del Touch Bar suben/bajan):
```lua
hl.bind("XF86KbdBrightnessUp",   hl.dsp.exec_cmd("brightnessctl -d 'spi::kbd_backlight' set 15%+"), { locked = true, repeating = true })
hl.bind("XF86KbdBrightnessDown", hl.dsp.exec_cmd("brightnessctl -d 'spi::kbd_backlight' set 15%-"), { locked = true, repeating = true })
hl.bind("XF86KbdLightOnOff",     hl.dsp.exec_cmd("brightnessctl -d 'spi::kbd_backlight' set 50%"),  { locked = true })
```

### Herramientas de diagnóstico usadas (para replicar)
- `glxinfo | grep -iE "renderer|direct rendering"` → confirmar aceleración real (no llvmpipe).
- `cat /sys/class/drm/card1/device/gpu_busy_percent` (repetido) → GPU saturada = 100% constante.
- `cat /sys/class/drm/card1/device/pp_dpm_sclk` → niveles de reloj.
- `hyprctl getoption misc:vrr` / `decoration:blur:enabled`.

## 13. OSD estilo macOS con swayosd (brillo/volumen MANUAL) + Noctalia OSD off (2026-07-18) ✅

**Objetivo del usuario:** que el brillo/volumen muestren OSD SOLO cuando los sube/baja **a mano**
(teclas del Touch Bar), y que el **auto-brillo** (§14) ajuste **en silencio** (sin OSD).

**Problema:** en esta máquina el brillo se controla escribiendo `gmux_backlight`, y **Noctalia
muestra su OSD ante CUALQUIER cambio del backlight** (lo vigila), sin distinguir quién lo hizo. Su
toggle `[osd.kinds] brightness` es **todo-o-nada** (probado: `false` mata el OSD de brillo para auto
Y manual, e incluso el IPC `brightness-osd` queda bloqueado). ⇒ con Noctalia solo NO se puede
"auto silencioso + manual con OSD".

**Solución que SÍ funciona (probada):** OSD de Noctalia de brillo/volumen APAGADO, y un OSD
independiente **swayosd** (estilo macOS, sale abajo) SOLO en las teclas manuales. El auto-brillo
escribe `gmux_backlight` directo → no llama a swayosd → **silencioso**; Noctalia apagado → tampoco.

Pasos (permanentes):
```bash
paru -S --noconfirm swayosd                       # AUR
```
1. **Server en autostart** — `~/.config/hypr/config/autostart.lua`, dentro de `hyprland.start`:
   ```lua
   hl.exec_cmd("swayosd-server")
   ```
2. **Teclas → swayosd** en `~/.config/hypr/config/binds.lua` (antes iban a `noctalia msg`):
   ```lua
   -- Volumen
   hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("swayosd-client --output-volume raise"),       { locked = true, repeating = true })
   hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("swayosd-client --output-volume lower"),       { locked = true, repeating = true })
   hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("swayosd-client --output-volume mute-toggle"), { locked = true })
   -- Brillo pantalla
   hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("swayosd-client --brightness raise --device gmux_backlight"), { locked = true, repeating = true })
   hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("swayosd-client --brightness lower --device gmux_backlight"), { locked = true, repeating = true })
   ```
3. **Apagar OSD de Noctalia** — `~/.config/noctalia/config.toml`:
   ```toml
   [osd.kinds]
   volume = false
   brightness = false
   ```
   Recargar: `noctalia msg config-reload` + `hyprctl reload`.

**Estado:** ✅ **FUNCIONANDO** — teclas del Touch Bar (brillo y volumen) muestran swayosd (abajo,
tipo Mac); Noctalia ya no muestra esos OSD. (Luz de teclado sigue con `brightnessctl` directo, §12.)

## 14. AUTO-BRILLO de pantalla por sensor de luz (ALS) — daemon `als-backlight` (2026-07-18) ✅

Ajusta el brillo de la pantalla a la luz ambiente (estilo macOS): **SILENCIOSO** (sin OSD), **suave**
(rampa ~60 Hz, no a escalones) y **sin jank** (escribe el backlight NATIVO, no AUX). Respeta el
ajuste manual como offset. Depende de §13 (OSD de Noctalia off + swayosd para el OSD manual).

**Cómo funciona:**
- Lee el ALS `iio:device0` (name=als) → `in_illuminance_input` (o `in_illuminance_raw` — varía entre
  boots) → curva luz→brillo con suavizado EMA.
- Escribe **`/sys/class/backlight/gmux_backlight/brightness` DIRECTO** (rampa fina a ~60 Hz para que
  se vea fluido). Permiso de escritura por regla udev (grupo `video`).
- **Silencioso:** NO llama a swayosd y el OSD de brillo de Noctalia está apagado → los cambios
  automáticos no muestran nada. El OSD solo sale con las teclas del Touch Bar (swayosd, §13).
- **Offset manual:** si subes/bajas con las teclas (swayosd escribe gmux), el daemon lo detecta y lo
  toma como preferencia (offset sobre la curva).

**Archivos (en el kit: `scripts/`, `systemd-user/`, `udev/`):**
```bash
# 1) permiso de escritura directa al gmux (rampa suave) — el usuario debe estar en grupo 'video'
sudo cp $KIT/udev/90-backlight-gmux.rules /etc/udev/rules.d/
sudo chgrp video /sys/class/backlight/gmux_backlight/brightness   # aplicar ya (esta sesión)
sudo chmod g+w  /sys/class/backlight/gmux_backlight/brightness
sudo udevadm control --reload
# 2) daemon + servicio de USUARIO (no root: usa sysfs directo)
install -Dm755 $KIT/scripts/als-backlight.py ~/.local/bin/als-backlight.py
install -Dm644 $KIT/systemd-user/als-backlight.service ~/.config/systemd/user/als-backlight.service
systemctl --user daemon-reload && systemctl --user enable --now als-backlight
```
Regla udev: `ACTION=="add", SUBSYSTEM=="backlight", KERNEL=="gmux_backlight", RUN+="/usr/bin/chgrp
video /sys/class/backlight/%k/brightness", RUN+="/usr/bin/chmod g+w /sys/class/backlight/%k/brightness"`

**Calibración del ALS (2026-07-18):** tapado=**0**, interior≈**20-23**, luz fuerte=**cientos**.
Curva actual `CURVE` (als→%): `(0,18)(2,35)(6,50)(15,65)(40,80)(120,92)(400,100)`.
**Tunear:** editar `CURVE` en `~/.local/bin/als-backlight.py` y `systemctl --user restart als-backlight`.

**Arranque:** Hyprland va por **UWSM** (sesión systemd de usuario) → el servicio `WantedBy=default.target`
arranca solo en el login. (Si alguna vez no arrancara: `loginctl enable-linger ermesbatista` o meterlo
en `autostart.lua` como swayosd-server.)

**Estado:** ✅✅ **VALIDADO** — suave y silencioso, CPU ~0.6%. Permanencia probada por el usuario
(reinicios + apagado completo): arranca solo y sigue funcionando.

## 15. TOUCH BAR intermitente en el arranque — carrera hid_sensor_hub (2026-07-18) ✅

**Síntoma:** a veces la barra enciende al arrancar, a veces queda en blanco; reiniciar suele
arreglarlo. Aleatorio.

**CAUSA REAL (de los logs de varios boots):** es una **carrera por la interfaz USB `.0002`** del
iBridge (`05ac:8600`). Secuencia en cada boot:
1. `hid-generic` toma `.0001` y `.0002` muy temprano.
2. A veces **`hid-sensor-hub`** (por el commit kernel 6.3+ que reconoce "sensor application
   collections") **agarra la `.0002`**.
3. `apple_ibridge` carga tarde (~5 s, autoload) y re-bindea: a `.0001` **siempre** le gana a
   hid-generic, pero a `.0002` **solo a veces** le gana a hid-sensor-hub.
- **Cuando hid-sensor-hub se queda con `.0002` → la Touch Bar NO enciende** (esa interfaz controla
  el DFR). Cuando apple-ibridge toma AMBAS → enciende.

**Señal de éxito/fallo (para diagnosticar):**
```bash
basename $(readlink /sys/bus/hid/devices/0003:05AC:8600.0002/driver)   # apple-ibridge-hid = OK ; hid-sensor-hub = FALLO
find /sys -name fnmode 2>/dev/null | grep 8600                          # presente = touchbar init OK
```

**FIX (de raíz, no reactivo): blacklist `hid_sensor_hub`.** En esta máquina NO se usa para nada
(el ALS del auto-brillo lo da **`apple_ib_als`**, y accel/luz van por **macsmc**; `hid_sensor_hub`
tenía usecount 0 y solo robaba la `.0002`). Bloqueándolo, apple-ibridge gana la `.0002` **siempre**.
```bash
sudo tee /etc/modprobe.d/blacklist-hid-sensor-hub.conf >/dev/null <<'EOF'
blacklist hid_sensor_hub
install hid_sensor_hub /usr/bin/false
EOF
sudo modprobe -r hid_sensor_hub          # descargar ya (usecount 0)
sudo mkinitcpio -P                        # por robustez (el blacklist en /etc también aplica en userspace)
```
⚠️ **GOTCHA:** `mkinitcpio -P` en CachyOS/Limine es un wrapper (`/usr/local/bin/mkinitcpio`) que copia
al ESP; si se lanza **desacoplado/en background** puede **colgarse** (bloqueado en `unix_stream_read`)
sin terminar la copia al ESP. Ejecutarlo en un **terminal normal (foreground)**. Si el ESP quedó
desactualizado, arreglarlo con `sudo limine-update` (regenera y copia el initramfs al ESP + limine.conf).
NOTA: aunque el initramfs del ESP quede viejo, `hid_sensor_hub` se carga en **userspace** (post-pivot),
así que el blacklist de `/etc/modprobe.d` aplica igual → el arranque nunca queda inseguro por esto.
(en el kit: `modprobe/blacklist-hid-sensor-hub.conf`)
**Bonus:** con esto el ALS es SIEMPRE `apple_ib_als` → `in_illuminance_input` consistente (antes el
campo variaba input/raw según quién ganaba la carrera).

**Estado:** ✅✅ **VALIDADO (2026-07-18)** — fix aplicado y probado por el usuario con **2 reinicios +
apagado completo**: la barra enciende **SIEMPRE**. Antes fallaba ~1 de cada 2. Resuelto de raíz.
(Plan B por si algún día fallara, no hizo falta: servicio post-boot que detecte `.0002` en
hid-sensor-hub y haga unbind+rebind a apple-ibridge-hid.)

## 16. HIBERNACIÓN (reemplaza suspensión) — Limine (2026-07-18)

**Por qué:** la SUSPENSIÓN (s2idle/deep) **cuelga el GPU AMD** al despertar en este modelo (§8). La
**hibernación** apaga del todo y al volver **re-inicializa el hardware como un arranque** (así vuelven
Touch Bar, audio, WiFi, brillo…), evitando la ruta de "wake" del GPU que cuelga. Ideal para "va al bulto".

**Config aplicada (permanente):**
1. **Swapfile 20 GB** (zram NO sirve para hibernar): `/swapfile` en `/` (ext4), en `/etc/fstab`:
   `/swapfile none swap defaults,pri=10 0 0` (zram queda pri 100 para swap normal; el swapfile pri 10
   es el destino de la imagen). Creado con `fallocate -l 20G` + `chmod 600` + `mkswap` + `swapon`.
2. **`resume=` en Limine** (NO GRUB) — `/etc/default/limine` `KERNEL_CMDLINE[default]` + `sudo limine-update`:
   `resume=UUID=e0a57e70-c719-4346-bf94-2c026a0cb58a resume_offset=50614272`
   (offset = `sudo filefrag -v /swapfile | awk '/^ *0:/{gsub(/\./,"",$4);print $4;exit}'` — **RECALCULAR
   si se recrea el swapfile**). Backup en `/etc/default/limine.bak-hibernate-*`.
3. El hook **`systemd`** de mkinitcpio maneja el resume automáticamente con esos params (no hace falta
   hook `resume`). Verificado: `busctl call ... login1.Manager CanHibernate` → **`yes`**.
4. **NO** se añadió el hook `99-macbook-resume` del §8 (era para el daemon `amdgpu-backlight`, que aquí
   NO se usa). Añadir un hook de system-sleep solo si algo no vuelve tras el resume.

**❌ RESULTADO (2026-07-18): LA HIBERNACIÓN NO FUNCIONA — cuelga igual que la suspensión.**
`systemctl hibernate` → pantalla en negro, cuelgue, hubo que apagar a la fuerza. El log (`journalctl
-b -1`) muestra que se atasca en el PRIMER paso: última línea del kernel `PM: hibernation: hibernation
entry` y nada más → **el GPU AMD Polaris cuelga al CONGELAR los dispositivos**, antes de escribir la
imagen. Es la MISMA pared que cuelga la suspensión (lado *freeze/suspend*, no *resume*). La suposición
del §8 (que hibernar esquivaba el bug del GPU) era **FALSA**. Confirmado nivel "research" (repo
Dunedan: en el 13,3 el sleep solo es fiable con la GPU Intel activa; el panel está en la AMD).

**DECISIÓN: fallback bag-safe = APAGAR (no dormir).** Cold boot trae todo (~30 s; ya arranca solo:
Touch Bar, WiFi, brillo, auto-brillo). Se quitó `resume=` del cmdline (hibernación abandonada). El
swapfile de 20 GB se deja como swap normal (pri 10) — inofensivo. Config de la tapa: pendiente de
elegir política (apagar en la tapa vs bloquear+apagar a mano) — ver §16.b cuando se decida.

## 16.b Intento de activar la GPU Intel (para que funcione el sleep) — ❌ ROMPIÓ EL ARRANQUE

**Idea:** el EFI del MacBook apaga la GPU **Intel** al arrancar no-macOS y solo deja la **AMD** (que
cuelga en sleep). La Intel NO aparece en `lspci` (`00:02.0` ausente). La doc dice que el sleep solo es
fiable con la Intel activa. Para encenderla:
- `apple_gmux.force_igd=1` (cmdline) + `options apple-gmux force_igd=y` → **NO basta.** El kernel avisa:
  `apple_gmux: force_idg is true, but couldn't find iGPU at 00:02.0! Is apple-set-os working?`
- Falta que el bootloader llame al protocolo EFI **`apple_set_os`** (decir "soy macOS"). **Limine NO
  lo hace nativo.**

**Lo que se intentó y salió MAL:** compilar `apple_set_os.efi` (aa15032261/apple_set_os-loader,
parcheado para encadenar a `\EFI\limine\limine_x64.efi`) y ponerlo primero en el BootOrder (con Limine
de fallback). **→ ROMPIÓ EL ARRANQUE.** El usuario tuvo que recuperar a mano (sacar la entrada
apple_set_os del BootOrder). ⚠️⚠️ **NO REPETIR ESTO.** Todo revertido y limpiado:
`efibootmgr -B` de la entrada, borrado el `.efi` del ESP, quitado `force_igd` del cmdline y el
`modprobe.d`, `limine-update`. La máquina volvió a Limine→AMD estable.

> LECCIÓN (ver memoria [[no-cirugia-arranque-riesgosa]]): NO hacer cirugía de EFI/bootloader con
> etiqueta de "bajo riesgo".

**2º intento (2026-07-19) con método SEGURO (BootNext, un disparo, sin tocar el default): TAMBIÉN
FALLÓ, y el dato es CONCLUYENTE.** El arranque Intel **se congela en el logo de Apple (la manzanita)**
— o sea NO pasa del **firmware**; el kernel Linux nunca corre (no hay journal del intento, confirmado
con `journalctl --list-boots`). ⇒ **encender la iGPU vía `apple_set_os` CUELGA EL FIRMWARE de esta
máquina en su propio logo.** Esto NO se arregla desde Linux/bootloader/kernel (i915 params, rEFInd,
shim — todos llaman al mismo `apple_set_os` que cuelga el firmware). Es un límite del **firmware EFI
de Apple** de esta unidad (reportado en algunos MBP 2016). **La red de seguridad BootNext SÍ funcionó**:
apagado forzoso → encendió solo en AMD, sin recuperación manual.

**CONCLUSIÓN sobre la Intel: NO viable en esta máquina** sin intervención a nivel de firmware (fuera
de alcance, riesgo de brick). Se queda en **AMD**. Todo el experimento revertido y limpio (Boot0007
borrado, shim fuera del ESP, cmdline sin params). Sleep → §16.c (apagar).

## 16.c SOLUCIÓN de tapa (reemplaza sleep) — split handler + logind ✅ FUNCIONA (2026-07-19)

Ni suspensión ni hibernación funcionan (bug GPU AMD, §16) y activar la Intel rompe el arranque (§16.b).
**No hay sleep.** Diseño **SPLIT** (probado y funcionando):

### CON sesión iniciada → handler propio (sistema sigue vivo, no suspende)
Al **cerrar** la tapa: pantalla off (`hyprctl dpms`), teclado off (`spi::kbd_backlight`), GPU AMD a
**`low`** (671→214 MHz), **WiFi off** (`nmcli radio wifi off`), **Bluetooth off** (`rfkill block
bluetooth`). Al **abrir**: restaura todo al instante (no estaba suspendido → sin cuelgue). A los
**5 min cerrada** → **antes de apagar restaura al estado "normal": WiFi on (`nmcli radio wifi on`) +
Bluetooth on (`rfkill unblock bluetooth`) + brillo del teclado a su valor previo
(`brightnessctl -d spi::kbd_backlight set $kbd_save`) + `sleep 2`**, y luego `systemctl poweroff`
(polkit `CanPowerOff=yes`, sin sudo). ⚠️ IMPRESCINDIBLE dejar todo "ON" antes del apagado porque
**se guarda el estado al apagar y se restaura al encender**:
- **WiFi/BT**: NetworkManager y systemd-rfkill guardan el estado → si quedan apagados, al encender vuelven apagados.
- **Teclado (fix 2026-07-20)**: `systemd-backlight@leds:spi::kbd_backlight.service` guarda el brillo del
  teclado al apagar. Si la tapa lo dejó en 0 y así se apaga, **al arrancar el teclado enciende SIN luz**
  y hay que subirlo a mano tras loguearse. Restaurando `kbd_save` (el valor previo al cerrar) antes del
  poweroff, systemd guarda un valor "ON" → al encender, el teclado ya ilumina. (Antes del fix esta rama
  reactivaba WiFi/BT pero se olvidaba del teclado.)

> ### ⚠️ WiFi/BT NO fiables por el "encender 2s antes del poweroff" — FIX real 2026-07-20 ✅ CONFIRMADO
> El re-encendido de WiFi/BT justo antes del `poweroff` es una **CARRERA** poco fiable: `systemd-rfkill`
> no siempre alcanza a persistir el "desbloqueado" antes de que el apagado desmonte su servicio (en el
> journal: *"systemd-rfkill.service: Deactivated"* + *"Transaction for systemd-rfkill.socket/start is
> destructive"*). Resultado: se arranca con WiFi **y** BT bloqueados y hay que encenderlos a mano.
> **Solución determinista (no depende del apagado):** un servicio que enciende ambos en CADA arranque:
> - `/etc/systemd/system/restore-radios.service` (oneshot, `After=NetworkManager.service bluetooth.service`):
>   `rfkill unblock all` + `nmcli radio wifi on` + `bluetoothctl power on`. `systemctl enable`.
> - `/etc/bluetooth/main.conf`: **`AutoEnable=true`** (descomentado) → bluetoothd enciende el adaptador
>   al encontrarlo (una vez desbloqueado el rfkill).
>
> Probado simulando el arranque malo (`rfkill block all` + `nmcli radio wifi off`) → `systemctl start
> restore-radios.service` → ambos quedan ON. El re-encendido del handler antes del poweroff se deja como
> respaldo (no estorba), pero el que garantiza es el servicio de arranque.
> Nota de diagnóstico: el BT Broadcom a veces logea *"BCM: failed to set baudrate"* al arrancar, pero se
> recupera solo (`chip id 126`, `management interface initialized`); NO es la causa del apagado.
- Script: `~/.local/bin/lid-handler.sh` (bucle, poll 3 s a `/proc/acpi/button/lid/*/state`). En el kit.
- Lanzado por Hyprland **envuelto en un inhibidor** para que logind NO actúe mientras hay sesión:
  `autostart.lua` → `hl.exec_cmd("systemd-inhibit --what=handle-lid-switch --who=lid-handler --why=tapa ~/.local/bin/lid-handler.sh")`

### SIN sesión (pantalla de login / boot) → logind apaga
Si cierras la tapa antes de iniciar sesión, no la vas a usar → que apague. Lo hace **logind**:
`/etc/systemd/logind.conf.d/10-macbook-lid.conf` con **`HandleLidSwitch=poweroff`** (+ ExternalPower;
Docked=ignore). Cubre el hueco del login SIN depender de la sesión. El inhibidor del handler (arriba)
hace que, CON sesión, logind no interfiera.

### Archivos (en el kit)
- `scripts/lid-handler.sh` → `~/.local/bin/lid-handler.sh`
- `systemd/restore-radios.service` → `/etc/systemd/system/` (`systemctl enable` — enciende WiFi/BT en cada boot)
- `main.conf`: `AutoEnable=true` en `/etc/bluetooth/main.conf`
- `systemd-logind/10-macbook-lid.conf` → `/etc/systemd/logind.conf.d/` (`HandleLidSwitch=poweroff`)
- `udev/91-amdgpu-powerlevel.rules` → `/etc/udev/rules.d/` (grupo `video` escribe
  `power_dpm_force_performance_level` sin sudo, para el GPU low)
- `autostart.lua`: la línea con `systemd-inhibit ... lid-handler.sh`

### ⚠️⚠️ REGLAS DE ORO (aprendidas a la mala — 2 apagados/sesiones perdidas)
- **NUNCA `systemctl restart systemd-logind` en caliente** → MATA la sesión gráfica (te tira al login,
  pantalla negra). Los cambios de `logind.conf` aplican SOLOS en el próximo arranque; si hay que
  aplicar en vivo usar `systemctl reload systemd-logind` (reload NO mata sesiones), o simplemente
  reiniciar. Un `restart` de logind fue lo que rompió la sesión dos veces (no la tapa).
- **`HandlePowerKey=poweroff`** es el default → un toque al botón de power APAGA sin confirmar.
- **NO simular la tapa** por comandos (dpms off, etc.): la prueba la hace el usuario cerrando la tapa
  en vivo. Ejecutar la simulación confunde y puede dejar estados a medias.
- **dpms por CLI en este Hyprland-Lua:** `hyprctl dispatch 'hl.dsp.dpms("off")'` / `("on")` (el
  `hyprctl dispatch dpms off` normal NO funciona — el fork evalúa Lua).
- La Touch Bar NO se toca (se apaga sola por inactividad; forzarla es riesgoso, §8/§15).
- El swapfile de 20 GB (§16) se deja como swap normal (inofensivo).

## 17. AUDIO — cuerpo/EQ de los altavoces con EasyEffects (2026-07-19) ✅

**Problema:** los altavoces (CS8409) en Linux salen **planos/sin cuerpo** — macOS les aplica un DSP/EQ
propietario (realce de graves + crossover + limitador) que en Linux no existe. Sonaba sin "relleno".

**Solución:** **EasyEffects** (EQ de PipeWire en tiempo real) con un preset moderado y **seguro**.
```bash
sudo pacman -S --needed easyeffects lsp-plugins-lv2 calf   # el EQ usa los plugins LSP (imprescindibles)
```
- **Autostart** (`autostart.lua`): `hl.exec_cmd("easyeffects --gapplication-service")` (servicio de fondo, sin ventana).
- **Preset `MacBook-Body`** (en el kit `easyeffects/MacBook-Body.json`), EQ paramétrico:
  - **105 Hz +5.5 dB** (cuerpo/graves) · **280 Hz +2.5 dB** (calidez) · **2500 Hz −2 dB** (menos dureza)
    · **9 kHz +2.5 dB** (aire) · **salida −3.5 dB** (headroom para no saturar).
- **Seguridad de bocinas:** realce MODERADO, sin bajos extremos (<100 Hz), con margen de salida.
  Los altavoces son chicos; forzar graves brutos distorsiona/daña. macOS usa limitador por lo mismo.

**⚠️ Gotchas de EasyEffects 8.x:**
- **NO usar `easyeffects -l <preset>` por CLI** en este equipo: BORRA el archivo del preset de
  `~/.config/easyeffects/output/` (reescribe su carpeta). **Cargar/afinar SOLO por la GUI.**
- El estado APLICADO en vivo vive en **`~/.config/easyeffects/db/`** (`equalizerrc`), NO en el preset.
  En el kit se respaldan **ambos**: `easyeffects/MacBook-Body.json` (portable, importar por GUI) y
  `easyeffects/db/` (estado exacto aplicado — copiar a `~/.config/easyeffects/db/`).
- Afinar por oído: abrir la app EasyEffects → Equalizer → mover la banda de ~105 Hz (más/menos cuerpo).

**Estado:** ✅ FUNCIONANDO — sonido con cuerpo, aprobado por el usuario. Preset + db en el kit.

## 18. Terminal / shell — quitar fastfetch al abrir (2026-07-19) ✅

CachyOS (shell **fish**) muestra las **especificaciones del equipo (fastfetch)** cada vez que abres
la terminal, vía `function fish_greeting` en `/usr/share/cachyos-fish-config/cachyos-config.fish`.
**Fix limpio (sin tocar el archivo del sistema, sobrevive updates):** sobrescribir `fish_greeting` con
una función vacía en `~/.config/fish/config.fish` (DESPUÉS del `source` de cachyos):
```fish
# desactivar fastfetch al abrir la terminal
function fish_greeting
end
```
Para revertir: borrar esa función (o poner `fastfetch` dentro).

### Helpers de git en fish (migrados desde `~/.bashrc`) — 2026-07-19
El usuario tenía aliases/funciones de git en `~/.bashrc` (sintaxis **bash**) e intentó `source ~/.bashrc`
en fish → falla (fish no entiende `PS1=...`, `export`, `funcion() {}`). Se tradujeron a **funciones nativas
de fish**, autocargadas desde `~/.config/fish/functions/` (una por archivo, sin `source`):
- `atras.fish` → `git checkout $argv`
- `subir.fish` → sin args `git pull`; con args `git add . && git commit -m "$argv" && git pull && git push`
- `greset.fish` → `git rm -r --cached . && git add . && commit "Ignore Reset" && pull && push`

**NO** se migró `gpull` (el usuario no lo usa; su ruta `/home/programacion/projects` ni existe). Tampoco
`PS1`, `PATH` (ya en `config.fish`) ni `ls`/`grep --color` (ya los pone la config de CachyOS).

### Tamaño de fuente del sistema (más grande) — 2026-07-19
En Hyprland no hay un solo "font size" global; se sube por toolkit:
- **GTK** (apps GTK): `gsettings set org.gnome.desktop.interface text-scaling-factor 1.1` (aplica al
  reabrir la app).
- **Qt** (usa qt6ct): en `~/.config/uwsm/env` (Hyprland va por UWSM) → `export QT_FONT_DPI="106"`
  (≈1.1x; aplica al próximo login). 96 = default, así que DPI/96 = factor.
- **Noctalia** (barra/shell): `ui_scale` en `~/.config/noctalia/config.toml` (estaba en 1.20).
Valor final elegido por el usuario: **1.1** (GTK) / **106** (Qt). Se probó 1.2 y era mucho.

### Reloj en formato 12h — Noctalia — 2026-07-19
El reloj de la barra (Noctalia) estaba en 24h. Se quiere **12 horas + día de la semana, TODO en español**.
Formato en `~/.config/noctalia/config.toml`:
```toml
[widget.clock]
format = "{:%I:%M %A %m/%d/%y}"   # 12h + día en español + fecha (ej: 05:11 domingo 07/19/26)
```
Y Noctalia arranca normal (español del sistema, es_DO) en `autostart.lua`:
```lua
hl.exec_cmd("noctalia")
```

⚠️ **DECISIÓN: 12h SIN AM/PM.** El `%p` (AM/PM) sale VACÍO en locales españoles (es_DO, es_US… ninguno
usa AM/PM; solo el inglés lo tiene). Se probó arrancar Noctalia con `LC_TIME=en_US.UTF-8` solo para él
para forzar el AM/PM → **ROMPIÓ EL CALENDARIO: los nombres de mes/día del calendario desplegable salían
en inglés** (el env afecta a TODO Noctalia, no solo al reloj). Descartado.
Otra opción era un **locale custom español+AMPM** (`localedef` copiando LC_TIME de es_DO y añadiendo
`am_pm "AM";"PM"`) pero `localedef` NO permite `copy` + override en la misma categoría
(*"cuando se utiliza `copy` no debe especificarse ninguna otra palabra clave"*), y habría requerido
reproducir todo el bloque LC_TIME a mano → frágil. Descartado por decisión del usuario:
> "si no sirve, déjalo como estaba, simple, ponme la hora en doce horas, deja que salga el día, solo que no salga el formato 24 horas."

**Resultado final:** 12h + día de la semana + fecha, todo en español; el calendario desplegable queda
en español. No hay indicador AM/PM (el usuario distingue mañana/tarde sin él).

> **Título de sección:** era "Reloj en formato 12h (AM/PM)"; corregido a "12h" al descartar el AM/PM.

## 19. Atajos copiar/pegar estilo macOS con Cmd (Super) — Hyprland (2026-07-19) ✅

El usuario quería usar **Cmd (tecla Command = SUPER)** para copiar/pegar como en Mac. Se remapeó en
`~/.config/hypr/config/binds.lua` (mainMod = SUPER):

| Cmd + | Función | Cómo |
|---|---|---|
| **C** | Copiar | script `mac-clip.sh copy` (apps: Ctrl+C · terminal: Ctrl+Shift+C) |
| **V** | Pegar | script `mac-clip.sh paste` (apps: Ctrl+V · terminal: Ctrl+Shift+V) |
| **X** | Cortar | `hl.dsp.send_shortcut({ mods="CTRL", key="x", window="activewindow" })` |
| **Z** | Deshacer | `send_shortcut` Ctrl+Z |
| **A** | Ajustes (Noctalia settings-toggle) | (antes era notificaciones) |
| **B** | Portapapeles (Noctalia clipboard) | (movido desde Cmd+V) |

**Atajos de Noctalia desplazados:** calculadora (Cmd+C) → **eliminada** (se usa el launcher);
control-center (Cmd+X) y notificaciones (Cmd+A) → **sin atajo** (se abren desde la barra).

**Terminal:** `Ctrl+C` sigue siendo **interrumpir** (intacto). El script `~/.local/bin/mac-clip.sh`
(en el kit) detecta si la ventana es terminal (`hyprctl activewindow -j | jq .class` → kitty/alacritty/
foot/ghostty/konsole) y manda **Ctrl+Shift+C/V** ahí, o **Ctrl+C/V** en el resto. Requiere `jq`.

**Nota técnica (fork Hyprland-Lua):** enviar teclas a la ventana activa = `hl.dsp.send_shortcut({ mods
= "CTRL", key = "c", window = "activewindow" })` (es una TABLA con claves; `mods` acepta "CTRL SHIFT").
Por CLI para probar: `hyprctl dispatch 'hl.dsp.send_shortcut({ mods="CTRL", key="c", window="activewindow" })'`.

**Estado:** ✅ FUNCIONANDO — probado por el usuario. Script en el kit (`scripts/mac-clip.sh`).

## 20. Captura de pantalla estilo macOS — Hyprland (2026-07-19) ✅

El MacBook **no tiene tecla `Print`/Impr Pant**, así que los binds por defecto de Noctalia
(`Print` → región, `SUPER+Print` → pantalla completa) eran inalcanzables. Se añadieron atajos
al estilo macOS en `~/.config/hypr/config/binds.lua` (sección *Screen Capture*, mainMod = SUPER):

| Cmd + | Función | Comando |
|---|---|---|
| **Shift + 4** | Captura de **región** (selección con mouse) | `noctalia msg screenshot-region` |
| **Shift + 5** | Captura de **pantalla completa** | `noctalia msg screenshot-fullscreen` |

- `Cmd+Shift+4` es idéntico al atajo de región de macOS y estaba **libre**.
- `Cmd+Shift+3` (fullscreen en macOS) está **ocupado** (`SUPER+SHIFT+3` = mover ventana al monitor 3),
  por eso fullscreen quedó en **`Cmd+Shift+5`**.
- Noctalia usa por debajo `grim` + `slurp` + `satty` (editor para anotar antes de guardar).
- Los binds `Print`/`SUPER+Print` se dejaron intactos (por si se conecta un teclado externo con Print).

Aplicado en vivo con `hyprctl reload`. Verificado en `hyprctl binds -j`: `modmask=65` (SUPER+SHIFT)
con `key=4` y `key=5` registrados.

## 7. Log de progreso

- [x] **Captura de pantalla ✅ 2026-07-19 — MacBook sin tecla Print; añadidos `Cmd+Shift+4` (región) y `Cmd+Shift+5` (pantalla completa) en binds.lua → `noctalia msg screenshot-*`. §20**
- [x] **Helpers git en fish ✅ 2026-07-19 — migrados `atras`/`subir`/`greset` de `~/.bashrc` (bash) a `~/.config/fish/functions/`. `gpull` descartado. §18**
- [x] Diagnóstico completo del hardware
- [x] sudo NOPASSWD configurado
- [x] dkms instalado, repos clonados
- [x] **Hallazgo clave: el kernel usa CLANG → compilar con `LLVM=1`, no GCC/KCFLAGS**
- [x] **Audio FUNCIONANDO ✅ — probado tras reinicio 2026-07-17, suena por altavoces (DKMS+clang, permanente)**
- [x] **Touch Bar funcionando ✅ — confirmado tras reinicio 2026-07-17 (DKMS+clang, parches kernel 7.1, autoload)**
- [x] **Brillo de pantalla FUNCIONANDO ✅ (2026-07-17): PWM del GPU no cableado; el panel usa AUX/DPCD. `amdgpu.backlight=1` NO bastó en Polaris (siguió en PWM). Solución definitiva: daemon `amdgpu-aux-backlight.py` (systemd) que espeja `amdgpu_bl1` → DPCD AUX. brightnessctl/Noctalia/Touch Bar mueven el panel de verdad.**
- [x] **Auto-brillo con el sensor de luz ✅ 2026-07-17 — wluma descartado (lento/pesado); reemplazado por daemon propio por CURVA `amdgpu-auto-brightness` (systemd, ligero, respuesta inmediata, respeta ajuste manual). §5.b**
- [x] **WiFi 2.4 y 5 GHz FUNCIONANDO ✅ 2026-07-17 — NVRAM del 13,3 (bug 193121 att.285753, boardtype=0x073e) + feature_disable=0x82000. Conectado a Servextex-Megared 5GHz con internet. Permanente. §6**
- [x] **SUSPENSIÓN 🔧 2026-07-17 — pantalla negra al abrir tapa por cuelgue del GPU AMD en `deep` (S3). Fix: `mem_sleep_default=s2idle` en GRUB + hook de resume que reinicia el daemon de brillo. Pendiente prueba del usuario. §8**
- [~] **SUSPENSIÓN → HIBERNACIÓN 🔧 2026-07-18 — s2idle cuelga el GPU AMD al despertar (repo Dunedan: 13,3 solo resume fiable con Intel activa; panel está en AMD). Descartado "deshabilitar suspend" (peligroso en bulto). Configurada HIBERNACIÓN bag-safe: swapfile 20G en disco + `resume=UUID=...:resume_offset=60205056` en GRUB + `mkinitcpio -P` + tapa→hibernate (logind). PENDIENTE reiniciar y validar `systemctl hibernate`. Fallback si falla = apagar. §8**
- [x] **WiFi señal < macOS INVESTIGADO 2026-07-17 — A/B controlado: ni 3ª antena (`rxchain=7`) ni LNA externo (`boardflags=0x10401001`) cambian nada (~-60 dBm en los 3 casos). Causa: tabla de calibración RF es de otra placa (ref 43569), no del MacBook. Revertido a original 2-ant. Fix real = calibración Apple (OTP, incierto) o dongle USB. §6**
- [x] **ESCALA DE PANTALLA ✅ 2026-07-18 — scale del monitor en `~/.config/hypr/config/monitors.lua`: `auto`(=2) → 1.5 → **1.6** (2880×1800 → 1800×1125 lógico). Aplicado con `hyprctl reload`. §5.c**
- [x] **TRACKPAD + TECLADO estilo macOS ✅ 2026-07-18 — `input.touchpad` en `inputs.lua`: natural_scroll, tap_to_click, tap_and_drag, clickfinger, disable_while_typing, drag_lock. Gestos 3/4 dedos horizontal = spaces. Teclado `us altgr-intl` para acentos con AltDcha (Option) sin romper comillas. §5.d**
- [x] **VENTILADORES / TÉRMICO ✅ 2026-07-18 — transiciones "toscas" en Hyprland NO eran la GPU (AMD Pro 460 renderiza, 0% uso) sino throttling de la CPU a 100°C sin control de ventiladores. Fix: `mbpfan` (AUR) + `/etc/mbpfan.conf` curva agresiva 50/55/68 + `systemctl enable --now mbpfan`. Permanente. Undervolt pendiente. §10**

### Config máquina nueva 2026-07-18 (ver §11)
- [x] **MÁQUINA NUEVA — bootloader Limine (no GRUB), sudo NOPASSWD recreado, ALS=in_illuminance_raw. §11**
- [x] **AUDIO ✅ FUNCIONA (probado tras reboot) — DKMS CS8409 LLVM=1.**
- [x] **TOUCH BAR ✅ FUNCIONA — DKMS apple-ibridge, 3 parches, autoload. NO era imposible (error mío "kernel 6.3 lo rompe" = falso).**
- [x] **TOUCH BAR intermitencia en boot ✅ RESUELTA y VALIDADA (2 reinicios + apagado, enciende siempre) — carrera: hid_sensor_hub robaba la interfaz .0002 → barra en blanco. Fix de raíz: blacklist hid_sensor_hub (no se usa aquí; ALS=apple_ib_als). §15.**
- [x] **WiFi 2.4+5 GHz ✅ FUNCIONA (NVRAM 13,3, Band 1+2, conectado).**
- [x] **VENTILADORES ✅ FUNCIONA — mbpfan curva 50/55/68 + enable --now.**
- [x] **BRILLO PANTALLA ✅ FUNCIONA NATIVO (gmux_backlight) — teclas Touch Bar lo mueven. Daemon AUX y params `acpi_backlight=native amdgpu.backlight=1` NO usados (deshabilitados): ERAN LA CAUSA DEL JANK. §12**
- [x] **JANK del compositor ✅ RESUELTO — causa = esos 2 params de kernel del brillo. Descartados VRR/blur/scale/daemon. §12**
- [x] **LUZ TECLADO ✅ FUNCIONA — binds `spi::kbd_backlight` en binds.lua (botones Touch Bar suben/bajan). §12**
- [x] **PERMANENCIA ✅ CONFIRMADA — reinicio + apagado completo: Touch Bar, audio, WiFi, brillo, todo persiste.**
- [x] **OSD estilo macOS (swayosd) ✅ — brillo+volumen manual con OSD abajo; Noctalia OSD off (todo-o-nada, no separa auto/manual). Auto-brillo escribirá gmux directo = silencioso. §13**
- [x] **AUTO-BRILLO pantalla por ALS ✅ FUNCIONA — daemon `~/.local/bin/als-backlight.py` (systemd user, enable). Lee ALS → escribe gmux DIRECTO (udev video g+w), rampa ~60Hz SUAVE, silencioso (sin OSD), offset manual. Calibrado (tapado0/interior~20/sol cientos). §14. ✅ VALIDADO permanencia (reinicios + apagado).**
- [x] **AUDIO cuerpo/EQ ✅ FUNCIONA — EasyEffects + plugins LSP/Calf + preset MacBook-Body (105Hz+5.5, 280Hz+2.5, 2500Hz−2, 9k+2.5, salida−3.5). Autostart `easyeffects --gapplication-service`. OJO: CLI `-l` borra el preset → cargar por GUI; estado vive en db/. Kit: easyeffects/. §17**
- [x] **SLEEP ❌ NO viable (bug GPU AMD): suspensión Y hibernación cuelgan en el freeze del GPU (§16). Intel (que arreglaría el sleep) ❌ NO viable: `apple_set_os` CUELGA EL FIRMWARE en el logo de Apple (§16.b) — 2 intentos, el 2º con BootNext (recuperación auto OK). Todo revertido. Se queda AMD.**
- [x] **TAPA (reemplaza sleep) ✅ FUNCIONA (probado) — SPLIT: CON sesión, handler `~/.local/bin/lid-handler.sh` (envuelto en `systemd-inhibit`) → cerrar: pantalla+teclado+GPU low+WiFi+BT off, sistema vivo; abrir: restaura al instante; 5 min cerrada → apagar. SIN sesión (login), logind `HandleLidSwitch=poweroff`. §16.c**
- [x] **Restauración tras tapa-apagado ✅ FUNCIONA (confirmado por el usuario 2026-07-20) — al encender vuelven solos: teclado con luz (`kbd_save` restaurado antes del poweroff) + WiFi + Bluetooth (servicio `restore-radios.service` en cada boot + `AutoEnable=true`). Reemplaza el "encender 2s antes del poweroff" que era una carrera no fiable. §16.c**
- [x] **⚠️ LECCIÓN CRÍTICA: `systemctl restart systemd-logind` en caliente MATA la sesión gráfica (2 veces me pasó, no era la tapa). Usar `reload` o esperar al próximo boot. NO simular la tapa por comandos. §16.c**
- [x] **⚠️ LECCIÓN: 2 arranques rotos por cirugía EFI (apple_set_os) que minimicé como "bajo riesgo". Ver memoria no-cirugia-arranque-riesgosa. BootNext = recuperación auto (apagar+encender → AMD).**

## Apéndice A — `amdgpu-backlight.py` v1 ORIGINAL (reemplazado por v2, ver §11/§5.b)

> ⚠️ El código de abajo es el **v1** que causaba el jank. El daemon en uso es el **v2**
> (`~/macbook-setup-kit/scripts/amdgpu-backlight.py`), con 1 sola transacción AUX, sin reassert
> periódico y deadband/poll grandes. Se conserva el v1 como referencia del problema.

Instalar en `/usr/local/bin/amdgpu-backlight.py` (permiso 755). También en `~/macbook-setup-kit/scripts/`.
Servicio `/etc/systemd/system/amdgpu-backlight.service`:
```ini
[Unit]
Description=Brillo unificado MacBookPro13,3: auto-curva (ALS) + panel AUX/DPCD
After=multi-user.target
Wants=multi-user.target
[Service]
Type=simple
ExecStart=/usr/local/bin/amdgpu-backlight.py
Restart=always
RestartSec=2
Nice=10
[Install]
WantedBy=multi-user.target
```
Regla udev `/etc/udev/rules.d/90-backlight-amdgpu.rules` (para que apps de usuario escriban el brillo):
```
ACTION=="add", SUBSYSTEM=="backlight", KERNEL=="amdgpu_bl1", RUN+="/usr/bin/chgrp video /sys/class/backlight/%k/brightness", RUN+="/usr/bin/chmod g+w /sys/class/backlight/%k/brightness"
```
Modprobe WiFi `/etc/modprobe.d/brcmfmac.conf`:
```
options brcmfmac feature_disable=0x82000
```

Daemon (`amdgpu-backlight.py`):
```python
#!/usr/bin/env python3
# Daemon unico de brillo para MacBookPro13,3 (GPU AMD Polaris, panel eDP AUX/DPCD).
#   1) Auto-brillo por CURVA segun el sensor de luz ambiente (ALS).
#   2) Puente al panel: escribe el brillo REAL por AUX/DPCD (el PWM del GPU no esta cableado).
# Los cambios AUTOMATICOS van SOLO al panel via AUX (NO tocan amdgpu_bl1) -> Noctalia no muestra
# OSD. amdgpu_bl1 = entrada MANUAL (teclas): el daemon lo detecta y lo usa como offset (macOS-like).
import os
import glob
import time

BL = "/sys/class/backlight/amdgpu_bl1"
REG_MODE = 0x721
REG_MSB = 0x722
AUX_MODE_BYTE = 0x06   # habilita control de brillo por AUX (bits[1:0]=10)

# --- curva luz(ALS crudo) -> brillo(%) ; interpolacion lineal ; ALS interior ~2-6 ---
CURVE = [
    (0,   18),
    (2,   35),
    (6,   50),
    (15,  65),
    (40,  80),
    (120, 92),
    (400, 100),
]

MIN_PCT = 5
MAX_PCT = 100
POLL = 0.3
EMA_ALPHA = 0.25
STEP_PCT = 3.0
DEADBAND_PCT = 0.6
OFFSET_CLAMP = 60.0
REASSERT_SEC = 3.0


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def find_als_path():
    for d in sorted(glob.glob("/sys/bus/iio/devices/iio:device*")):
        try:
            if open(f"{d}/name").read().strip() == "als":
                return f"{d}/in_illuminance_input"
        except OSError:
            continue
    return None


def is_edp(fd):
    try:
        rev = os.pread(fd, 1, 0x700)
        return len(rev) == 1 and rev[0] in (0x01, 0x02, 0x03)
    except OSError:
        return False


def open_edp_aux():
    cands = ["/dev/drm_dp_aux0"] + sorted(glob.glob("/dev/drm_dp_aux*"))
    seen = set()
    for p in cands:
        if p in seen or not os.path.exists(p):
            continue
        seen.add(p)
        try:
            fd = os.open(p, os.O_RDWR)
        except OSError:
            continue
        if is_edp(fd):
            return fd
        os.close(fd)
    return None


def curve_pct(als):
    pts = CURVE
    if als <= pts[0][0]:
        return pts[0][1]
    if als >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= als <= x1:
            t = (als - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return pts[-1][1]


def main():
    als_path = None
    while als_path is None:
        als_path = find_als_path()
        if als_path is None:
            time.sleep(2)

    max_bl = read_int(f"{BL}/max_brightness")
    manual_tol = 0.01 * max_bl

    def write_panel(fd, pct):
        val = max(0, min(65535, round(pct / 100.0 * 65535)))
        os.pwrite(fd, bytes([AUX_MODE_BYTE]), REG_MODE)
        os.pwrite(fd, bytes([(val >> 8) & 0xFF, val & 0xFF]), REG_MSB)

    fd = None
    ema = read_int(als_path)
    last_manual = read_int(f"{BL}/brightness")
    manual_pct = last_manual / max_bl * 100.0
    offset = max(-OFFSET_CLAMP, min(OFFSET_CLAMP, manual_pct - curve_pct(ema)))
    panel_pct = manual_pct
    last_reassert = 0.0
    ticks = 0

    while True:
        ticks += 1
        try:
            if fd is None:
                fd = open_edp_aux()
                if fd is None:
                    time.sleep(0.5)
                    continue

            raw_als = read_int(als_path)
            ema = EMA_ALPHA * raw_als + (1 - EMA_ALPHA) * ema

            cur_manual = read_int(f"{BL}/brightness")
            if abs(cur_manual - last_manual) > manual_tol:
                manual_pct = cur_manual / max_bl * 100.0
                offset = max(-OFFSET_CLAMP, min(OFFSET_CLAMP,
                                                manual_pct - curve_pct(ema)))
            last_manual = cur_manual

            target = max(MIN_PCT, min(MAX_PCT, curve_pct(ema) + offset))

            now = ticks * POLL
            need_reassert = (now - last_reassert) >= REASSERT_SEC
            if abs(target - panel_pct) > DEADBAND_PCT:
                if target > panel_pct:
                    panel_pct = min(target, panel_pct + STEP_PCT)
                else:
                    panel_pct = max(target, panel_pct - STEP_PCT)
                write_panel(fd, panel_pct)
            elif need_reassert:
                write_panel(fd, panel_pct)
                last_reassert = now
        except OSError:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            fd = None
            time.sleep(0.5)
        time.sleep(POLL)


if __name__ == "__main__":
    main()
```
