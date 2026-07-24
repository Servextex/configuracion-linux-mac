# Mac mini 8,1 + CachyOS — Registro de configuración

Documentación de problemas diagnosticados y resueltos en este equipo.

---

## Identificación del equipo

| Dato | Valor |
|---|---|
| Modelo | **Macmini8,1** (Apple Inc., 2018) |
| CPU | Intel Core i3-8100B @ 3.60 GHz |
| Hostname | `MacMiniErmes` |
| SO | CachyOS (Arch-based) |
| Kernel | `7.1.3-2-cachyos` |
| Escritorio | Hyprland (Wayland) |
| Locale | `es_DO.UTF-8` |
| Instalación | 21 jul 2026, ~12:29–12:32 |
| Disco | NVMe 113 GB — `/boot` vfat 4G, `/` ext4 109G |
| Audio | PipeWire 1.6.8 + WirePlumber 0.5.15 |
| Bootloader | **Limine** (NO GRUB) — params en `/etc/default/limine` + `sudo limine-update` |
| Escritorio | Hyprland 0.56 (fork con config **Lua**) + Noctalia 5.0 + shell **fish** |
| WiFi | Broadcom **BCM4364** `[14e4:4464]` PCI `03:00.0` → `brcmfmac` (firmware de Apple, §3) |
| Ethernet | Broadcom NetXtreme BCM57766 → `enp4s0` (funciona de fábrica) |
| Ventilador | 1 fan, 1700–4400 RPM, vía driver **`macsmc_hwmon`** (ACPI `APP0001:00`), §4 |
| Monitores | 2 × 1920×1080 (DP-1, DP-2), scale 1.0 — **no es HiDPI** |
| Entrada | Magic Trackpad + Magic Keyboard **por Bluetooth** (no hay teclado interno) |

> **Kit de archivos:** `macmini-t2-kit/` en esta misma USB (firmware WiFi ya convertido, daemon
> del ventilador, servicio systemd, modprobe, scripts). Con él, una reinstalación no necesita
> volver a descargar nada de Apple.

> ⚠️ **Este equipo NO es el MacBook.** El runbook `macbook-linux-setup.md` de esta USB es de un
> **MacBookPro13,3 (portátil, chip T1)**: sirve como método y como catálogo de trampas, pero su
> WiFi (NVRAM BCM43602), audio CS8409, Touch Bar, brillo/ALS, `mbpfan`, tapa e hibernación
> **no aplican aquí**. Un runbook por modelo.

---

## 1. Volumen de altavoz Bluetooth no responde — RESUELTO

**Fecha:** 21 jul 2026

### Síntoma

Altavoces **Logitech Z607** (`AA:AA:AA:AA:AA:AA`) conectados por Bluetooth. El control de
volumen del sistema no tenía ningún efecto sobre el sonido: se movía el slider por todo su
recorrido y el volumen real no cambiaba. **Lo único que funcionaba era llevarlo a 0**, que sí
silenciaba.

### Causa raíz

El altavoz anuncia soporte de **AVRCP Absolute Volume** (UUID `A/V Remote Control Target`),
que permite que el volumen lo controle el propio dispositivo por hardware. PipeWire lo detecta
y delega el volumen al altavoz — pero **los Z607 ignoran los comandos `SetAbsoluteVolume`**.

Resultado: PipeWire cree que el hardware maneja el volumen, así que no aplica volumen por
software; y el altavoz nunca obedece. El volumen queda en tierra de nadie.

El 0 sí funcionaba porque el *mute* es un comando AVRCP distinto que el altavoz sí implementa.

### Evidencia del diagnóstico

Bandera del sink delegando volumen al hardware:

```
$ pactl list sinks | grep -A2 bluez_output
Flags: HARDWARE HW_VOLUME_CTRL DECIBEL_VOLUME LATENCY
       api.bluez5.profile = "a2dp-sink"
       api.bluez5.codec   = "sbc"
```

Prueba decisiva — cambiar el volumen saltándose el escritorio:

```
$ pactl set-sink-volume bluez_output.C0_28_8D_F8_CD_2E.1 20%
```

El volumen reportado bajó a 20% pero **el sonido no cambió**. Eso descartó que el problema
fuera el slider o las teclas de Hyprland: PipeWire mandaba la orden correctamente y el
altavoz la ignoraba.

### Solución aplicada

Se desactivó el control de volumen por hardware para Bluetooth, forzando a PipeWire a aplicar
el volumen por software.

**Archivo creado:** `~/.config/wireplumber/wireplumber.conf.d/51-bluez-no-hw-volume.conf`

```
monitor.bluez.properties = {
  bluez5.enable-hw-volume = false
}
```

Aplicar los cambios:

```bash
systemctl --user restart wireplumber
bluetoothctl disconnect AA:AA:AA:AA:AA:AA
bluetoothctl connect AA:AA:AA:AA:AA:AA
```

> El reconecte es **obligatorio**: el sink se crea al conectar, así que reiniciar WirePlumber
> solo no basta — hay que forzar que el sink se recree con la nueva propiedad.

### Verificación

WirePlumber confirma que lee el fragmento de config:

```
$ WIREPLUMBER_DEBUG=3 wireplumber 2>&1 | grep 51-bluez
wp-conf: opening fragment file: /home/ermesbatista/.config/wireplumber/wireplumber.conf.d/51-bluez-no-hw-volume.conf
wp-conf: section 'monitor.bluez.properties' is used as-is from .../51-bluez-no-hw-volume.conf
```

Volumen confirmado funcionando en todo el recorrido del control.

**Nota honesta:** `pactl` sigue mostrando la bandera `HW_VOLUME_CTRL` en el sink incluso
después del arreglo. Aparentemente la capa de compatibilidad `pipewire-pulse` la reporta de
forma genérica y no refleja el cambio. **No es indicativo de fallo** — lo que importa es que
el volumen responde. No usar esa bandera para verificar si el arreglo sigue activo; probar el
volumen directamente.

### Revertir

```bash
rm ~/.config/wireplumber/wireplumber.conf.d/51-bluez-no-hw-volume.conf
systemctl --user restart wireplumber
```

### Datos de referencia del dispositivo

| Dato | Valor |
|---|---|
| Dispositivo | Logi Z607 |
| MAC | `AA:AA:AA:AA:AA:AA` |
| Sink | `bluez_output.C0_28_8D_F8_CD_2E.1` |
| Perfil activo | `a2dp-sink` (SBC) |
| Perfiles disponibles | `a2dp-sink` (SBC), `a2dp-sink-sbc_xq` (SBC-XQ), `off` |

> Si se quiere mejor calidad de audio, existe el perfil **SBC-XQ**:
> `pactl set-card-profile bluez_card.C0_28_8D_F8_CD_2E a2dp-sink-sbc_xq`
> (no probado en este equipo)

### Cómo reconocer este mismo problema en otro altavoz

Todos estos síntomas juntos apuntan a AVRCP roto:

1. El slider de volumen no hace nada, pero el 0 sí silencia
2. `pactl set-sink-volume <sink> 20%` cambia el número pero no el sonido
3. `pactl list sinks` muestra `HW_VOLUME_CTRL` en el sink Bluetooth

El arreglo es el mismo archivo de arriba — aplica a **todos** los dispositivos Bluetooth, no
solo a este, porque `monitor.bluez.properties` es global.

---

## 2. Contraseña de sudo no funciona — RESUELTO (falsa alarma)

**Fecha:** 21 jul 2026

### Sospecha inicial

Se sospechaba que CachyOS había bloqueado la cuenta.

### Hallazgo: la cuenta NO está bloqueada

| Chequeo | Resultado |
|---|---|
| `passwd -S` | `P` → contraseña usable, no bloqueada |
| `chage -l` | Contraseña caduca en 2300; cuenta nunca caduca |
| Grupo `wheel` | Sí pertenece |
| `faillock` | Por debajo del umbral, sin bloqueo activo |

### Causa real de los fallos

El journal reveló que los fallos **no eran por contraseña incorrecta**:

```
sudo[8757]: pam_faillock(sudo:auth): Consecutive login failures for user ermesbatista
            account temporarily locked
sudo[8361]: pam_unix(sudo:auth): auth could not identify password for [ermesbatista]
sudo[8361]: pam_unix(sudo:auth): conversation failed
```

`conversation failed` = **sudo no tenía terminal donde preguntar la contraseña**. Los intentos
venían de una sesión no interactiva (una sesión previa de Claude Code intentando escribir
`/etc/sudoers.d/99-ermesbatista-nopasswd`). Cada intento sin TTY se contaba como fallo, y a
los 3 fallos PAM aplicó el bloqueo temporal estándar (10 min), que ya expiró.

### Factores de riesgo detectados

Dos cosas que podrían hacer que la contraseña esté realmente mal sin que se note:

1. **Autologin activo** — `/etc/sddm.conf` tiene `[Autologin]` y el usuario está en el grupo
   `nopasswdlogin`. **Nunca se escribe la contraseña al entrar**, así que un error de tecleo
   durante la instalación pasaría desapercibido durante días.

2. **Desajuste de teclado** entre consola y escritorio:
   - VC Keymap (TTY): `us-acentos` — **con teclas muertas**
   - X11 Layout: `us`, variante `altgr-intl`

   Si la contraseña contiene `'`, `"`, `` ` `` o `~`, se escriben distinto en cada entorno.
   Instalar con un layout y luego teclear en otro produce contraseñas que "no funcionan".

### Desenlace: CONFIRMADO, la contraseña estaba bien

Probado en una terminal real (con TTY) con `sudo -v`: **funciona sin problema**.

No había nada que arreglar. La contraseña siempre fue correcta y la cuenta nunca estuvo
bloqueada por CachyOS. Todo el episodio fue el efecto secundario de lanzar `sudo` desde
sesiones sin TTY, que PAM contabilizó como intentos fallidos.

**Lección para la próxima:** si `sudo` falla, mirar el journal *antes* de asumir que la
contraseña está mal. `conversation failed` y `could not identify password` significan
"no pude preguntar", no "contraseña incorrecta" — son problemas totalmente distintos.

Si algún día sí hiciera falta limpiar el contador de fallos:

```bash
faillock --user $USER --reset   # requiere root
```

### Nota importante

**No se configuró NOPASSWD** en `/etc/sudoers.d/`. Hacerlo dejaría el equipo con acceso root
sin contraseña de forma permanente. Si en algún momento se hace, que sea una decisión
consciente y no un parche para saltarse este problema.

> **ACTUALIZACIÓN (21 jul 2026, tarde):** para la sesión de trabajo de §3–§6 **sí se activó
> NOPASSWD temporalmente**, como decisión consciente del usuario, porque `sudo` desde la
> herramienta Bash no tiene TTY y no puede pedir contraseña (ver el archivo creado a mano:
> `/etc/sudoers.d/99-ermesbatista-nopasswd`, modo 440).
> **REVERTIR AL TERMINAR:**
> ```bash
> sudo rm /etc/sudoers.d/99-ermesbatista-nopasswd
> ```

---

## 3. WiFi no funciona (BCM4364) — RESUELTO

**Fecha:** 21 jul 2026

### Síntoma

No existe `wlan0`. Solo hay red por cable (`enp4s0`). `nmcli radio` reporta `wifi: missing`.

### Causa raíz

La tarjeta **sí** la ve el kernel y el driver **sí** carga; lo que falta es el **firmware
propietario de Apple**, que **no viene en `linux-firmware` y nunca vendrá**:

```
brcmfmac: brcmf_fw_alloc_request: using brcm/brcmfmac4364b2-pcie for chip BCM4364/3
brcmfmac 0000:03:00.0: Direct firmware load for brcm/brcmfmac4364b2-pcie.bin failed with error -2
brcmfmac 0000:03:00.0: brcmf_pcie_setup: Dongle setup failed
ieee80211 phy0: brcmf_fw_crashed: Firmware has halted or crashed
```

⚠️ **Diferencia con el MacBook (§6 de `macbook-linux-setup.md`):** allá el `.bin` existía y solo
faltaba la **NVRAM** (`.txt`) de la placa. **Aquí falta el `.bin` completo**, más `.clm_blob` y
`.txcap_blob`. No sirve de nada tocar NVRAM ni `feature_disable`.

⚠️ Complicación: **este disco está 100 % Linux**, no hay macOS ni partición APFS de donde sacar el
firmware, y la ESP de Apple fue reformateada por la instalación (`/boot` no tiene `EFI/APPLE/`).
Según la wiki de t2linux, en ese caso **solo queda el Método 5**: bajar una imagen de recuperación
de macOS de los servidores de Apple y extraer el firmware de ahí. Es firmware **del hardware que ya
posees** — se necesita internet (aquí: el cable).

### Solución aplicada

```bash
# 1) el script oficial de t2linux (incluye el conversor de nombres, obra de Asahi Linux)
curl -fsSL -O https://wiki.t2linux.org/tools/firmware.sh

# 2) imagen de recuperacion de Apple, NO interactivo (~844 MB)
curl -fsSL -O https://raw.githubusercontent.com/kholia/OSX-KVM/master/fetch-macOS-v2.py
python3 fetch-macOS-v2.py --action download -s sonoma -o recovery
#    "Image verification failed ([Errno 25] Inappropriate ioctl for device)" al final es
#    INOFENSIVO: es el chequeo de progreso pidiendo un TTY, no un fallo de datos.

# 3) extraer el firmware SIN dmg2img ni montar nada  <-- ver "atajo" abajo
sudo pacman -S --needed 7zip
7z x -o./fwextract recovery/BaseSystem.dmg "macOS Base System/usr/share/firmware/*"

# 4) convertir del formato Apple (.trx/.clmb/.txcb) al formato brcmfmac
bash firmware.sh rename_only "…/macOS Base System/usr/share/firmware" firmware-renamed.tar

# 5) instalar y recargar (sin reiniciar)
sudo tar -xC /lib/firmware/brcm -f firmware-renamed.tar
sudo modprobe -r brcmfmac_wcc brcmfmac ; sudo modprobe brcmfmac
nmcli radio wifi on
```

> ### ⭐ ATAJO IMPORTANTE — `7z` en vez de `dmg2img` (ahorra media hora)
> El método oficial manda instalar **`dmg2img`** (solo en **AUR**), convertir el `.dmg` a `.img`,
> y montarlo con `losetup -P` + `mount`. En este equipo `dmg2img` **se quedó 10+ minutos colgado
> bajando sus fuentes de SourceForge** y nunca terminó (además no hay `paru`/`yay` instalado).
> **`7z` está en los repos oficiales y lee el DMG directamente** (`Type = Dmg`, ve los 55.760
> archivos del volumen). Extrae la carpeta del firmware en segundos: **sin AUR, sin `dmg2img`,
> sin `losetup`, sin `mount`, sin root.**

> ### GOTCHA del script — `rename_only` no existe en la rama Linux
> `firmware.sh` expone el subcomando `rename_only` **solo cuando corre en macOS**. En Linux el
> `case` lo rechaza con `Error: Invalid option!`. Se arregla añadiéndolo al `case ${subcmd}` de la
> rama Linux (justo después de `case ${subcmd} in`, ~línea 941):
> ```bash
> ("rename_only")
>     rename_firmware "${args[@]}" ${verbose}
>     ;;
> ```
> La copia parcheada quedó en el kit; los subcomandos `get_from_*` del script sí funcionan tal cual,
> pero son los que exigen `dmg2img`.

### Verificación

```
brcmfmac: brcmf_c_process_txcap_blob: TxCap blob found, loading
brcmfmac: brcmf_c_preinit_dcmds: Firmware: BCM4364/3 wl0: Jul 26 2024 version 9.30.514.0.32.5.94
```

```bash
ip -br link | grep wlan0                                        # wlan0 existe
sudo iw phy phy0 info | grep -E '^\s+Band [0-9]'                # Band 1 Y Band 2 -> 2.4 + 5 GHz
nmcli -f SSID,CHAN,FREQ,SIGNAL dev wifi list
```

**Estado:** ✅ **2.4 GHz y 5 GHz funcionando**, detecta `Servextex SRL 5G` (canal 149, 5745 MHz).

### Permanencia y reinstalación

- El firmware vive en `/lib/firmware/brcm/` (68 archivos `4364*`). **`linux-firmware` no lo pisa**
  porque ese paquete no incluye chips Apple.
- **Respaldo en la USB:** `macmini-t2-kit/firmware/brcm-4364-firmware-sonoma.tar`. Tras una
  reinstalación **no hay que descargar los 844 MB otra vez**:
  ```bash
  sudo tar -xC /lib/firmware/brcm -f /ruta/al/kit/firmware/brcm-4364-firmware-sonoma.tar
  sudo modprobe -r brcmfmac_wcc brcmfmac ; sudo modprobe brcmfmac
  ```
- `/etc/modprobe.d/brcmfmac.conf` (`feature_disable=0x82000`) ya lo genera **chwd** solo. No tocarlo.

### Notas

- El nombrado final incluye variantes por placa (`brcmfmac4364b2-pcie.apple,ekans.bin`,
  `…apple,hanauma…`, `…kauai…`). **El kernel elige la correcta solo** — no hace falta averiguar
  cuál es la de este Mac mini ni renombrar nada a mano.
- **Bluetooth:** el log dice `BCM4364B0 Maui Olympic GEN (MFG)` y `BCM: firmware Patch file not
  found`. No se corrigió **porque no hace falta**: el BT funciona (teclado, trackpad y Z607
  conectan). Según t2linux el parche `.hcd` solo es necesario en MacBookPro15,4 / 16,3 / MacBookAir9,1.

---

## 4. Ventilador clavado al mínimo → CPU a 94-100 °C — RESUELTO

**Fecha:** 21 jul 2026

### Síntoma

```
Package id 0:  +94.0°C  (high = +100.0°C, crit = +100.0°C)
fan1_input = 1692 RPM      <- el MINIMO, mientras la CPU se cocina
fan1_min = 1700  ·  fan1_max = 4400
```

Es el **mismo problema del §10 del MacBook** (throttling térmico), pero por **otra causa y con
otro mecanismo**: el SMC del T2 no recibe bajo Linux las temperaturas que le daría macOS, así que
deja el ventilador en reposo aunque la CPU esté al límite.

### Por qué `t2fanrd` NO sirve aquí

Está **instalado** (`t2fanrd r12.8502787-1`) pero venía `disabled`/`inactive`, y aunque se active
no funciona: busca el ventilador en

```
/sys/devices/pci*/*/*/*/APP0001:00/fan*        con archivos  fanN_manual  y  fanN_output
```

(lo del kernel **t2linux** con `applesmc` parcheado). En este CachyOS el SMC lo expone el driver
**`macsmc_hwmon`** por **ACPI**, en `/sys/class/hwmon/hwmonN/` con la interfaz hwmon estándar
(`fan1_input`, `fan1_target`) — el glob nunca coincide. Tampoco sirve `fancontrol` de lm_sensors:
ese quiere `pwmN`, y aquí no hay `pwm`.

### CAUSA RAÍZ / la llave: el parámetro `fan_control` del módulo

```bash
modinfo macsmc_hwmon | grep parm
# parm: fan_control:Override the SMC to set your own fan speeds on supported machines (bool)
cat /sys/module/macsmc_hwmon/parameters/fan_control     # -> N   (desactivado de fábrica)
```

Con `fan_control=N` **todos** los atributos son `r--r--r--`. Activándolo, `fan1_target` pasa a
**`rw-r--r--`** y el ventilador obedece de verdad (probado: 1679 → 3206 RPM y de vuelta).

### Solución aplicada

```bash
# 1) permanencia del parametro (el modulo carga en USERSPACE, no desde el initramfs:
#    /etc/modprobe.d basta y NO hay que tocar mkinitcpio)
echo 'options macsmc-hwmon fan_control=1' | sudo tee /etc/modprobe.d/99-macsmc-fan.conf

# 2) aplicar en vivo
sudo modprobe -r macsmc_hwmon && sudo modprobe macsmc_hwmon fan_control=1

# 3) daemon de curva propio + servicio
sudo install -m755 macmini-fan.py /usr/local/bin/macmini-fan.py
sudo systemctl enable --now macmini-fan.service
```

Ambos archivos están en el kit: `macmini-t2-kit/scripts/macmini-fan.py`,
`macmini-t2-kit/systemd/macmini-fan.service`, `macmini-t2-kit/modprobe/99-macsmc-fan.conf`.

### La curva — y por qué NO se copió la del MacBook

Primer intento con la curva de `mbpfan` del portátil (**low 50 / high 55 / max 68**): el ventilador
quedó **CLAVADO en 4400 RPM** de forma permanente. Motivo: el i3-8100B del Mac mini **vive
normalmente entre 70 y 92 °C**, o sea siempre por encima del "máximo" de esa curva. Copiar la curva
del portátil tal cual = secador de pelo perpetuo.

Curva final (perfil **fresco**, elegido por el usuario), en `CURVE` dentro del script:

| CPU | Ventilador |
|---|---|
| ≤ 50 °C | 1700 RPM (mínimo) |
| 60 °C | 2600 RPM |
| 70 °C | 3400 RPM |
| 80 °C | 4100 RPM |
| ≥ 88 °C | 4400 RPM (máximo) |

**Para ajustar:** editar `CURVE` en `/usr/local/bin/macmini-fan.py` y
`sudo systemctl restart macmini-fan`. Subir los grados = más silencio; bajarlos = más frío.

Detalles del daemon: interpola linealmente entre puntos, suaviza con EMA (`EMA_ALPHA`), rampa
asimétrica (sube rápido `STEP_UP=400`, baja lento `STEP_DOWN=120` para que no "bombee" el ruido),
banda muerta de 60 RPM, y **al recibir SIGTERM deja el ventilador en 2600 RPM, nunca en el mínimo**
(si el daemon muriera con el equipo caliente, el SMC no lo subiría solo).

### Verificación

| | Antes | Después |
|---|---|---|
| CPU | **94 °C** | **55–77 °C** |
| Ventilador | 1692 RPM (fijo) | 2200–3700 RPM (modulando) |

```bash
systemctl is-active macmini-fan
sensors | grep 'Package id 0'
cat /sys/class/hwmon/hwmon4/fan1_target /sys/class/hwmon/hwmon4/fan1_input
```

### Revertir

```bash
sudo systemctl disable --now macmini-fan
sudo rm /etc/modprobe.d/99-macsmc-fan.conf /usr/local/bin/macmini-fan.py \
        /etc/systemd/system/macmini-fan.service
sudo systemctl daemon-reload && sudo modprobe -r macsmc_hwmon && sudo modprobe macsmc_hwmon
```

> ⚠️ El número de `hwmon` (aquí `hwmon4`) **puede cambiar entre arranques**. El daemon no lo asume:
> busca el que tenga `name == macsmc_hwmon`. Para comandos a mano:
> `H=$(dirname $(grep -l macsmc_hwmon /sys/class/hwmon/*/name))`

---

## 5. Atajos y entrada estilo macOS — APLICADO

**Fecha:** 21 jul 2026

Todo esto **sí se pudo copiar del MacBook** (§5.d, §19 y §20 de `macbook-linux-setup.md`) porque el
escritorio es idéntico: Hyprland con config **Lua** + Noctalia. Ojo: **Noctalia 5.0 cambió los
comandos** respecto al documento del portátil (`panel-toggle <cosa>` en vez de los antiguos).

Backups automáticos antes de tocar: `binds.lua.bak-AAAAMMDD-HHMMSS`, `inputs.lua.bak-…`.

### 5.a Copiar/pegar con Cmd (§19) — `~/.config/hypr/config/binds.lua`

| Cmd + | Función | Cómo |
|---|---|---|
| **C** | Copiar | `~/.local/bin/mac-clip.sh copy` |
| **V** | Pegar | `~/.local/bin/mac-clip.sh paste` |
| **X** | Cortar | `send_shortcut` Ctrl+X |
| **Z** | Deshacer | `send_shortcut` Ctrl+Z |
| **A** | Ajustes de Noctalia | `settings-toggle` (venía en Cmd+Z) |
| **B** | Portapapeles | `panel-toggle clipboard` (venía en Cmd+V) |

`mac-clip.sh` (en el kit) detecta si la ventana activa es terminal (`hyprctl activewindow -j | jq
.class` → kitty/alacritty/foot/ghostty/konsole) y ahí manda **Ctrl+Shift+C/V**, en el resto
**Ctrl+C/V**. Así **`Ctrl+C` sigue siendo INTERRUMPIR en la terminal**. Requiere `jq` (ya estaba).

Atajos desplazados: **calculadora (Cmd+C) eliminada** (se abre desde el launcher) y
**control-center (Cmd+X) y notificaciones (Cmd+A) quedan sin atajo** (se abren desde la barra).

### 5.b Capturas de pantalla (§20)

| Cmd + | Función |
|---|---|
| **Shift + 4** | Captura de **región** (idéntico a macOS) |
| **Shift + 5** | Captura de **pantalla completa** |

`Cmd+Shift+3` (el de macOS para pantalla completa) **está ocupado** por "mover ventana al monitor
3", por eso fullscreen quedó en **5** — mismo compromiso que en el portátil. Los binds `Print` /
`Cmd+Print` se dejaron intactos por si se conecta un teclado con tecla Print.

### 5.c Magic Trackpad + acentos (§5.d) — `~/.config/hypr/config/inputs.lua`

```lua
kb_layout  = "us",
kb_variant = "altgr-intl",   -- acentos con AltDcha, sin romper ' " ` ~ para programar
touchpad = {
    natural_scroll = true, tap_to_click = true, tap_and_drag = true,
    clickfinger_behavior = true, disable_while_typing = true, drag_lock = true,
    scroll_factor = 0.4,   -- velocidad de desplazamiento tipo Mac (añadido 2026-07-21)
},
```

Gestos: **3 y 4 dedos horizontal = cambiar de escritorio** (antes el de 3 hacía close/fullscreen/
float, que no es comportamiento Mac). Se conservan 3-dedos arriba = fullscreen y abajo = cerrar.

- **`scroll_factor` (velocidad de scroll):** el default de Hyprland es `1.0`, que se sentía
  **disparado** (nada tipo Mac). Se fijó en **`0.4`** para un desplazamiento controlado estilo macOS.
  Ajuste a gusto: **menor = más lento** (0.3 / 0.25), **mayor = más rápido** (0.5). Aplicar con
  `hyprctl reload`. Verificar: `hyprctl getoption input:touchpad:scroll_factor` → `0.400000`.

- Uso de acentos: **AltDcha + a/e/i/o/u** → á é í ó ú · **AltDcha + n** → ñ · **AltDcha + '** y
  luego `u` → ü. Verificado: el teclado pasa a `English (intl., with AltGr dead keys)`.
- ⚠️ Las claves del wrapper Lua van con **guion bajo** y anidadas en `input.touchpad`. Referencia
  de nombres: `/usr/share/hypr/stubs/hl.meta.lua`.
- ⚠️ El Magic Trackpad puede estar **desconectado** al aplicar esto: no importa, la config no
  depende del dispositivo y surte efecto en cuanto se conecta.

### Aplicar y verificar

```bash
hyprctl reload
hyprctl getoption input:kb_variant                    # altgr-intl
hyprctl getoption input:touchpad:natural_scroll       # true   (¡con GUIONES aquí!)
hyprctl binds | grep -c 'key:'
```

> ⚠️ **`hyprctl binds -j` devuelve JSON inválido en este fork** (`jq` falla con *Invalid numeric
> literal*), y la salida de texto muestra `dispatcher: __lua` **sin el comando**. Para comprobar
> binds hay que cruzar `modmask` + `key` (SUPER = 64, SUPER+SHIFT = 65). **Los atajos solo se
> validan de verdad usándolos.**

---

## 6. Terminal, reloj y audio — APLICADO

**Fecha:** 21 jul 2026

### 6.a Quitar fastfetch al abrir la terminal (§18)

CachyOS (shell **fish**) imprime las especificaciones del equipo en cada terminal, vía
`function fish_greeting` en `/usr/share/cachyos-fish-config/cachyos-config.fish`. Fix limpio **sin
tocar el archivo del sistema** (sobrevive a las actualizaciones): sobrescribir la función en
`~/.config/fish/config.fish`, **después** del `source` de cachyos:

```fish
function fish_greeting
end
```

La plantilla de CachyOS ya trae ese bloque comentado — solo hubo que descomentarlo. Revertir:
borrar la función o poner `fastfetch` dentro.

### 6.b Helpers de git en fish (§18)

Traducidos a **funciones nativas de fish** (autocargadas desde `~/.config/fish/functions/`, una por
archivo, sin `source`). Ojo: `source ~/.bashrc` **no funciona** en fish (no entiende `export`,
`PS1=`, `funcion() {}`), y el encadenado de fish es `; and`, no `&&`.

| Función | Qué hace |
|---|---|
| `atras <rama>` | `git checkout` |
| `subir` | sin argumentos: `git pull` |
| `subir <mensaje>` | `add .` + `commit -m "<mensaje>"` + `pull` + `push` |
| `greset` | `git rm -r --cached .` + `add .` + commit *"Ignore Reset"* + `pull` + `push` |

Igual que en el portátil, **no** se migró `gpull` (no se usa).

### 6.c Reloj en 12 horas (§18) — `~/.config/noctalia/config.toml`

```toml
[widget.clock]
format = "{:%I:%M %A %m/%d/%y}"     # 12h + dia de la semana + fecha (ej: 01:46 martes 07/21/26)
```

Recargar: `noctalia msg config-reload`.

⚠️ **SIN AM/PM, y es a propósito** (lección ya aprendida en el portátil): `%p` sale **vacío** en
locales españoles (`es_DO`); forzar `LC_TIME=en_US` solo para Noctalia **rompe el calendario**
(los meses y días salen en inglés, porque la variable afecta a todo Noctalia). No reintentarlo.

### 6.d EasyEffects (§17) — instalado

> ⚠️ **Esta sección quedó SUPERADA el mismo día. Ver §7**, que documenta el estado final del audio
> (perfil ALSA del T2 + preset `MacBook-Body` **sí aplicado** al altavoz interno). Lo de abajo se
> conserva porque explica la instalación y los gotchas de la app.

```bash
sudo pacman -S --needed easyeffects lsp-plugins-lv2 calf
# autostart en ~/.config/hypr/config/autostart.lua:
hl.exec_cmd("easyeffects --gapplication-service")
```

El preset **`MacBook-Body`** del portátil se copió a `~/.config/easyeffects/output/` pero
**deliberadamente NO se activó**: está diseñado para los **altavoces chicos internos de una laptop**
(+5.5 dB a 105 Hz, +2.5 dB a 280 Hz). El audio de este equipo sale por unos **Logitech Z607 con
subwoofer** — ese realce embarraría el sonido y forzaría el sub. Queda **disponible para importar
desde la GUI** si algún día se usa otra salida.

⚠️ **Gotcha heredado del portátil, sigue vigente:** **NO usar `easyeffects -l <preset>` por CLI**
— borra el archivo del preset. Cargar y afinar **solo desde la GUI**. El estado aplicado en vivo
vive en `~/.config/easyeffects/db/`, no en el archivo del preset.

---

## 7. Audio: prioridad de tiempo real y perfil del T2 — RESUELTO

**Fecha:** 21 jul 2026

### 7.a Prioridad de tiempo real de WirePlumber — APLICADO

#### Síntoma

Al arrancar, WirePlumber avisaba:

```
mod.rt: could not set nice-level to -11: Permiso denegado
```

Sin prioridad de tiempo real, el servidor de audio compite con el resto de procesos y puede
producir **microcortes y chasquidos bajo carga** (compilar, navegador pesado, juegos).

#### Causa raíz

El paquete `realtime-privileges 5-1` **ya estaba instalado** y trae los permisos correctos en
`/etc/security/limits.d/99-realtime-privileges.conf`:

```
@realtime - rtprio 98
@realtime - memlock unlimited
@realtime - nice -11
```

**Pero el grupo `realtime` estaba vacío** — el usuario nunca fue añadido. Instalar el paquete
no añade a nadie al grupo; ese paso es manual y se había saltado.

El usuario sí estaba en `audio` (grupo que crea `cachyos-settings` en
`/etc/security/limits.d/20-audio.conf`), pero ese grupo **solo concede `rtprio 99`** — ni `nice`
ni `memlock`. De ahí que el `rtprio` estuviera bien y el `nice` fallara.

| Límite | Antes | Después (tras re-login) | Lo concede |
|---|---|---|---|
| RTPRIO | 99 ✅ | 99 | `@audio` |
| **NICE** | **0** ❌ | **-11** | `@realtime` |
| **MEMLOCK** | **8192 KB** ❌ | ilimitado | `@realtime` |

#### Solución aplicada

```bash
sudo usermod -aG realtime ermesbatista
```

Verificado:

```
$ getent group realtime
realtime:x:968:ermesbatista
```

#### ⚠️ Requiere cerrar sesión y volver a entrar

Los límites de PAM se aplican **al abrir la sesión**, no al proceso en marcha. Hasta el próximo
login los valores siguen siendo los viejos y el aviso seguirá saliendo. Un reinicio también vale.

#### Trampa al verificar (importante)

**No verificar con `su`.** En este sistema `/etc/pam.d/su` y `/etc/pam.d/su-l` **no incluyen
`system-auth` en la parte de `session`**, así que `pam_limits` nunca corre por esa vía y
`prlimit` devuelve los valores por defecto del kernel (`RTPRIO 0`), que parecen *peores* que los
reales. Es un falso negativo.

La cadena que sí aplica los límites es la del login gráfico:

```
sddm-autologin → system-local-login → system-login → system-auth → pam_limits.so
```

Verificación correcta, **en una terminal después de re-loguear**:

```bash
prlimit --nice --rtprio --memlock     # NICE debe ser 31 (= 20 - (-11)), MEMLOCK unlimited
journalctl --user -b -u wireplumber | grep mod.rt   # no debe salir nada
```

#### Revertir

```bash
sudo gpasswd -d ermesbatista realtime
```

### 7.b Perfil de audio `apple-t2x1.conf` — APLICADO

#### El aviso

```
spa.alsa: profile-set '/usr/share/alsa-card-profile/mixer/profile-sets/apple-t2x1.conf'
          can't be accessed: No existe el fichero o el directorio
```

#### Causa raíz — es un hueco del paquete, no un fallo del equipo

La regla udev de `apple-t2-audio-config` compone el nombre del perfil leyendo `/proc/asound/cards`:

```
/usr/lib/udev/rules.d/92-apple-t2-audio.rules
PROGRAM="/usr/bin/sed -n 's/.*AppleT2x\([0-9]\).*/\1/p' /proc/asound/cards"
ENV{ACP_PROFILE_SET}="apple-t2x%c.conf"
```

Este equipo se identifica como **`AppleT2x1`** (1 altavoz, mono):

```
$ cat /proc/asound/cards
 0 [Audio]: AppleT2x1 - Apple T2 Audio
```

Pero el paquete `apple-t2-audio-config 0.3-2` **solo trae `apple-t2x2`, `x4` y `x6`**. El Mac mini
se quedó fuera. Al no encontrar perfil, PipeWire cae a `output:mono-fallback`.

#### Qué cuesta realmente

El hardware expone tres PCM:

```
$ aplay -l / arecord -l
card 0, device 0: Speaker         ← altavoz interno
card 0, device 2: Codec Output    ← jack de auriculares 3.5mm
card 0, device 3: Codec Input     ← entrada
```

Con `mono-fallback` solo se expone **un puerto genérico** (`analog-output`), así que **el jack de
auriculares de 3.5mm no aparece como salida seleccionable**.

#### Canales verificados en el hardware (no a ojo)

**No vale copiar el `apple-t2x2.conf`**: ese mapea un `BuiltinMic` en `device 1` que este equipo
**no tiene** (el Mac mini 2018 no lleva micrófono interno; la entrada de audio es la del webcam
USB). Los canales se midieron uno a uno:

```
$ aplay -D hw:0,2 --dump-hw-params /dev/zero   → CHANNELS: 2, S24_LE, 48000
$ arecord -D hw:0,3 --dump-hw-params           → CHANNELS: 1, S32_LE, 48000
$ cat /proc/asound/Audio/pcm0p/sub0/hw_params  → channels: 1, S24_LE, 48000
```

> `hw:0,0` no responde a `--dump-hw-params` porque lo tiene tomado el sink activo; por eso el
> altavoz se verifica leyendo `/proc/asound/`, no con `aplay`.

| PCM | Dispositivo | Canales | Mapeo |
|---|---|---|---|
| `hw:0,0` | Speaker (interno) | 1 | `mono` |
| `hw:0,2` | Codec Output (jack 3.5mm) | 2 | `left,right` |
| `hw:0,3` | Codec Input | 1 | `mono` |

#### Solución aplicada

Creado `/usr/share/alsa-card-profile/mixer/profile-sets/apple-t2x1.conf` (y copia en
`/usr/share/pulseaudio/alsa-mixer/profile-sets/` por consistencia con el paquete), modo 644 root:

```
[Mapping Speakers]
device-strings = hw:%f,0
paths-output = t2-speakers
channel-map = mono
direction = output

[Mapping Headphones]
device-strings = hw:%f,2
paths-output = t2-headphones
channel-map = left,right
direction = output

[Mapping HeadsetMic]
device-strings = hw:%f,3
paths-input = t2-headset-mic
channel-map = mono
direction = input

[Profile Default]
description = Default Profile
output-mappings = Speakers Headphones
input-mappings = HeadsetMic
```

Los `paths-*` que referencia (`t2-speakers`, `t2-headphones`, `t2-headset-mic`) **sí vienen** en el
paquete; solo faltaba el profile-set.

Aplicar:

```bash
sudo udevadm trigger --subsystem-match=sound --action=change
sudo udevadm settle
systemctl --user restart wireplumber
```

#### Verificación

Antes (1 sink genérico):

```
Active Profile: output:mono-fallback
  analog-output: Salida analógica (availability unknown)
```

Después (2 salidas + 1 entrada, con **detección de jack funcionando**):

```
Active Profile: Default
  Default: Default Profile (sinks: 2, sources: 1)
  t2-speakers:    Altavoces  (type: Speaker,    priority: 10000, availability unknown)
  t2-headphones:  Auriculares (type: Headphones, priority: 20000, not available)
  t2-headset-mic: Micrófono acoplado (type: Headset, priority: 20000, not available)
```

```
$ pactl list sinks short
alsa_output.pci-0000_02_00.3.Speakers     s24-32le 1ch 48000Hz
alsa_output.pci-0000_02_00.3.Headphones   s24-32le 2ch 48000Hz
```

El **`not available`** de `t2-headphones` es la prueba de que va bien: la detección de jack sabe
que ahora mismo no hay nada enchufado. Al conectar auriculares pasa a `available` y el audio
conmuta solo (prioridad 20000 > 10000 del altavoz).

El aviso `apple-t2x1.conf can't be accessed` desapareció del log.

#### ⚠️ Efecto secundario: tumba el Bluetooth

Recrear la tarjeta ALSA (`udevadm trigger` + reiniciar WirePlumber) **desconecta el altavoz
Bluetooth**, y al desaparecer su sink PipeWire pone por defecto el altavoz interno. En el log:

```
spa.bluez5.sink.media: connection (.../sep1/fd0) terminated unexpectedly
spa.bluez5: Failure in Bluetooth audio transport
```

No es un fallo del perfil, es el reinicio de WirePlumber. Además el Z607 entra en **standby solo**
si deja de recibir audio, lo que realimenta el problema. Tras cualquier reinicio de WirePlumber:

```bash
bluetoothctl connect AA:AA:AA:AA:AA:AA
sleep 4
pactl set-default-sink bluez_output.C0_28_8D_F8_CD_2E.1
```

> Si `set-default-sink` responde `Failure: No such entity` es que el sink ya se cayó otra vez —
> el altavoz se durmió. Reconectar y repetir sin esperar demasiado entre los dos comandos.

#### Revertir

```bash
sudo rm /usr/share/alsa-card-profile/mixer/profile-sets/apple-t2x1.conf
sudo rm /usr/share/pulseaudio/alsa-mixer/profile-sets/apple-t2x1.conf
systemctl --user restart wireplumber
```

Se vuelve a `mono-fallback`, que funciona (sin jack).

#### Nota de mantenimiento

El archivo está en `/usr/share/`, **fuera del control de pacman**. Un futuro update de
`apple-t2-audio-config` que llegue a incluir `apple-t2x1.conf` daría **conflicto de archivo**
(`exists in filesystem`). Si eso pasa, borrar el nuestro y quedarse con el del paquete.

**Respaldo:** `macmini-t2-kit/audio/apple-t2x1.conf` en esta USB.

---

### 7.c Audio con EasyEffects (EQ) — APLICADO

**Fecha:** 21 jul 2026

**Regla de esta máquina: TODO el audio pasa por EasyEffects**, con el preset `MacBook-Body`, sea
cual sea la salida (altavoz interno, Z607 Bluetooth, auriculares, HDMI). Un solo preset, sin
excepciones y sin tener que tocar nada al cambiar de bocina.

#### Motivo

El **altavoz interno** suena feo aun con el perfil correcto (§7.b): es un altavoz **mono, pequeño
y sin caja**, y macOS le aplica un **DSP propietario** (realce de graves + limitador) que en Linux
no existe. Es el mismo caso que el CS8409 del MacBook (§17 de `macbook-linux-setup.md`) y la
solución es la misma: **EasyEffects**.

Comprobado de paso que **la tarjeta del T2 no expone ningún control de mezcla ALSA**
(`amixer -c 0 scontrols` sale vacío): todo el volumen es por software, no hay nada que "destapar"
por el lado del mixer.

#### Instalación

```bash
sudo pacman -S --needed easyeffects lsp-plugins-lv2 calf   # el EQ usa los plugins LSP
# autostart en ~/.config/hypr/config/autostart.lua:
hl.exec_cmd("easyeffects --service-mode")
# preset (viene del kit del MacBook, es el mismo):
cp .../macbook-setup-kit/easyeffects/MacBook-Body.json ~/.local/share/easyeffects/output/
easyeffects -l MacBook-Body
```

Preset **`MacBook-Body`**: 105 Hz **+5.5 dB** (cuerpo) · 280 Hz **+2.5 dB** (calidez) ·
2500 Hz **−2 dB** (menos dureza) · 9 kHz **+2.5 dB** (aire) · salida **−3.5 dB** (headroom).

#### Que arranque solo y siga a cualquier bocina

En `~/.config/easyeffects/db/easyeffectsrc`:

```ini
[Presets]
lastLoadedOutputPreset=MacBook-Body     # lo pone la app sola al cargar un preset

[StreamOutputs]
useDefaultOutputDevice=true             # sigue a la salida por defecto del sistema
processAllOutputs=true                  # procesa todas las salidas
```

Con eso: al arrancar la sesión, EasyEffects levanta en modo servicio, carga `MacBook-Body` solo, y
**se mueve solo** a la bocina que esté puesta por defecto. No hay nada que hacer a mano.

#### Dos hallazgos de EasyEffects 8.2.7 (el doc del MacBook está desactualizado en esto)

1. **Los presets YA NO viven en `~/.config/easyeffects/`.** La 8.2 los movió a
   **`~/.local/share/easyeffects/output/`**. En `~/.config/easyeffects/db/` solo queda
   `easyeffectsrc` (estado de la app). Si copias un preset a la ruta vieja, **la app lo migra y la
   carpeta vieja desaparece** — parece que se borró, pero está en la nueva.
2. **El gotcha "`easyeffects -l` borra el preset" YA NO APLICA.** En el MacBook (8.x anterior)
   cargar por CLI destruía el archivo; **aquí se probó con respaldo previo y sobrevive intacto**.
   `easyeffects -l MacBook-Body` es seguro en 8.2.7.

> Dato suelto por si algún día hiciera falta: el **autoload por dispositivo** (preset distinto
> según la bocina) **no funciona** en esta versión — se probaron las dos convenciones de nombre de
> archivo, con la app reiniciada entre pruebas, y nunca disparó. Aquí **no importa**, porque todo
> el audio lleva el mismo preset.

#### ⚠️ TRAMPA al hacer pruebas de audio: te deja la salida cambiada

Probar cosas de audio implica `pactl set-default-sink` y reiniciar WirePlumber, y **eso deja la
salida por defecto donde quedó la última prueba** — normalmente en el altavoz interno, con el
Bluetooth conectado pero mudo. Pasó exactamente eso en esta sesión: "el Bluetooth no suena" cuando
`bluetoothctl info` decía `Connected: yes` y el sink existía; simplemente no era el dispositivo por
defecto.

**Volver al Bluetooth (los dos pasos, en este orden):**

```bash
pactl set-default-sink bluez_output.C0_28_8D_F8_CD_2E.1
# arrastrar tambien lo que YA estaba sonando (si no, el audio en curso se queda en el otro sink):
for i in $(pactl list short sink-inputs | awk '{print $1}'); do
    pactl move-sink-input $i bluez_output.C0_28_8D_F8_CD_2E.1
done
```

Diagnóstico rápido de "no suena por X": `pactl get-default-sink` (¿es el que crees?) ·
`pactl list short sinks` (¿`RUNNING` o `SUSPENDED`?) · `bluetoothctl info <MAC>` (¿`Connected`?).

#### Verificación

```bash
pgrep -x easyeffects                                  # corriendo
easyeffects -p                                        # lista: MacBook-Body
pw-cli ls Node | grep -c ee_soe_equalizer             # 1 = EQ activo
pw-link -l | grep -A2 ee_soe_output_level             # a que salida esta llegando DE VERDAD
pactl get-default-sink                                # cual es la salida por defecto
```

Estado comprobado: EQ activo (1 nodo), cadena
`app → easyeffects_sink → [EQ] → ee_soe_output_level → bluez_output…Z607`.

#### Ajustar a oído

Abrir la app (EasyEffects) → **Ecualizador** → mover la banda de ~105 Hz (más/menos cuerpo). El
estado aplicado se guarda solo. Es la forma prevista de afinarlo; no hace falta editar el JSON.

#### Revertir

```bash
pkill -x easyeffects
sed -i '/easyeffects/d' ~/.config/hypr/config/autostart.lua
sudo pacman -Rns easyeffects lsp-plugins-lv2 calf
rm -rf ~/.config/easyeffects ~/.local/share/easyeffects
```

**Respaldo:** `macmini-t2-kit/audio/easyeffects/MacBook-Body.json` en esta USB.

---

## 8. Sin márgenes ni bordes en Hyprland — APLICADO

**Fecha:** 21 jul 2026

### Origen

Estaba documentado en `macbook-linux-setup.md` (§ *Sin márgenes ni bordes*, marcado
**✅ CONFIRMADO por el usuario**) pero **nunca se aplicó en este equipo**. El Mac mini tenía
todavía los valores de fábrica de CachyOS, exactamente los "era" del runbook del portátil.

Los gaps dejan un **marco de wallpaper** alrededor de las ventanas, y el `rounding` hace que
asome wallpaper en las cuatro esquinas de cada ventana.

### Solución aplicada

`~/.config/hypr/config/decorations.lua` (backup previo `decorations.lua.bak-20260721-143054`):

```lua
general = {
    gaps_in     = 0,   -- era 3   (separación entre ventanas)
    gaps_out    = 0,   -- era 8   (margen ventana↔borde de pantalla = el marco de wallpaper)
    border_size = 1,   -- era 2   (ver nota abajo: se probó 0 y el usuario pidió 1)
}
decoration = {
    rounding = 0,      -- era 10  (esquinas redondeadas → asomaba wallpaper)
}
```

> **`border_size = 1`, no `0`.** Aquí se diverge del runbook del portátil a propósito. Se aplicó
> primero `0` (como allí) y el usuario pidió subirlo a `1` para poder distinguir la ventana con
> foco en modo mosaico. Un píxel no quita espacio apreciable y recupera la pista visual.
> El degradado ya estaba configurado en `colors.lua`:
> activa = 45° de `#82dccc` → `#007d6f`, inactiva = `#798bb2`.

Aplicar en vivo, sin reiniciar sesión:

```bash
hyprctl reload
```

### Verificación

```
$ hyprctl getoption general:gaps_in       → css gap data: 0 0 0 0
$ hyprctl getoption general:gaps_out      → css gap data: 0 0 0 0
$ hyprctl getoption general:border_size   → int: 1
$ hyprctl getoption decoration:rounding   → int: 0
```

Ventanas **borde a borde y cuadradas**, con 1 px de borde para identificar el foco → máximo
espacio útil sin perder la pista visual.

### Revertir

```bash
cp ~/.config/hypr/config/decorations.lua.bak-20260721-143054 \
   ~/.config/hypr/config/decorations.lua
hyprctl reload
```

### Notas

- **Ventana activa**: resuelto con `border_size = 1` (ver arriba). Si el píxel se queda corto,
  `2` sigue siendo barato; para volver al look totalmente limpio del portátil, `0`.
- **Barra Noctalia**: tiene su redondeo propio, independiente de Hyprland. Aquí ya estaba con
  `margin_edge = 0` y `margin_ends = 0`; conserva `radius_bottom_left/right = 12`, **igual que en
  el portátil**, así que se deja para que ambos equipos coincidan. Si algún día molesta, se pone a
  `0` en `~/.config/noctalia/config.toml`.
- **Transparencia**: este equipo mantiene `active_opacity = 0.95` / `inactive_opacity = 0.85` y
  `blur` en `size 5, passes 4`. En el portátil se bajaron a `1.0` y `size 3, passes 2`, pero **allí
  era por rendimiento** a 2880×1800@scale1.5; aquí son 2×1080p y la GPU no sufre. Se deja el look
  original a propósito — es cuestión de gusto, no de fallo.

---

## 9. OSD estilo macOS (swayosd) y teclas de brillo — APLICADO

**Fecha:** 21 jul 2026

### 9.a OSD de volumen con swayosd — APLICADO

Estaba en `macbook-linux-setup.md` §13 y **nunca se aplicó aquí**: swayosd ni siquiera estaba
instalado, las teclas de volumen iban al OSD de Noctalia y `config.toml` no tenía `[osd.kinds]`.

#### Diferencia con el portátil

Allá el §13 cubría **brillo Y volumen**, y su motivo principal era que el auto-brillo por sensor
(ALS) no disparase el OSD. **Aquí solo aplica el volumen**: este equipo no tiene panel interno
(`/sys/class/backlight/` está vacío), no hay ALS y no hay auto-brillo. Por eso el OSD de brillo de
Noctalia se deja **encendido** — ver §9.b.

#### Solución aplicada

```bash
sudo pacman -S swayosd          # en repos oficiales, no hace falta AUR
```

1. **Server en autostart** — `~/.config/hypr/config/autostart.lua`:
   ```lua
   hl.exec_cmd("swayosd-server")
   ```

2. **Teclas de audio → swayosd** — `~/.config/hypr/config/binds.lua`
   (backup `binds.lua.bak-20260721-145256`):
   ```lua
   hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("swayosd-client --output-volume raise"),       { locked = true, repeating = true })
   hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("swayosd-client --output-volume lower"),       { locked = true, repeating = true })
   hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("swayosd-client --output-volume mute-toggle"), { locked = true })
   hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("swayosd-client --input-volume mute-toggle"),  { locked = true })
   ```
   > El mic-mute usa `--input-volume mute-toggle` de swayosd (en el portátil seguía en
   > `noctalia msg mic-mute`); así los cuatro controles de audio usan el mismo OSD.

3. **Apagar SOLO el OSD de volumen de Noctalia** — `~/.config/noctalia/config.toml`
   (backup `config.toml.bak-20260721-145256`):
   ```toml
   [osd.kinds]
   volume = false
   ```
   > **Sin `brightness = false`**, a diferencia del portátil. Ver §9.b.

4. Recargar: `noctalia msg config-reload` && `hyprctl reload`

#### Verificación

```
$ pgrep -a swayosd
128414 swayosd-server

$ swayosd-client --output-volume raise   → 90% → 95%
$ swayosd-client --output-volume lower   → 5 puntos por pulsación
$ swayosd-client --output-volume mute-toggle → Mute: yes → Mute: no
```

> **Detalle observado:** tres llamadas a `lower` separadas por 1 s solo movieron 5 puntos; con 2 s
> de separación cada una bajó sus 5 puntos. Es el debounce del servidor de swayosd al recibir
> llamadas encadenadas por script. **Con pulsaciones reales de teclado no se nota** (los binds
> llevan `repeating = true`). No es un fallo.

#### Revertir

```bash
cp ~/.config/hypr/config/binds.lua.bak-20260721-145256 ~/.config/hypr/config/binds.lua
cp ~/.config/noctalia/config.toml.bak-20260721-145256 ~/.config/noctalia/config.toml
# quitar la linea swayosd-server de autostart.lua
noctalia msg config-reload && hyprctl reload
```

### 9.b Teclas de brillo: NO pueden funcionar en este equipo

#### Hallazgo

`binds.lua` tiene las teclas de brillo apuntando a `noctalia msg brightness-up/down`, pero
**no hacían absolutamente nada**:

- `/sys/class/backlight/` está **vacío** → no hay panel interno (son 2 monitores externos).
- `ddcutil` no estaba instalado → sin vía por software para monitores externos.

#### Diagnóstico definitivo

Instalado `ddcutil` y probado el bus I2C:

```
$ sudo ddcutil detect
Invalid display  /dev/i2c-4  card1-DP-1  →  DDC communication failed
Invalid display  /dev/i2c-5  card1-DP-2  →  This monitor does not support DDC/CI.
                                            (I2C slave address x37 is unresponsive)
```

**Ninguno de los dos monitores soporta DDC/CI.** No es un problema de configuración ni de
permisos: el hardware no responde al protocolo. **El brillo se ajusta con los botones físicos del
monitor, y punto.**

#### Qué se dejó preparado

`ddcutil` se **deja instalado** y el usuario **añadido al grupo `i2c`**, con el módulo cargándose
en el arranque:

```bash
sudo usermod -aG i2c ermesbatista
echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf
```

Así, el día que se conecte un monitor que **sí** soporte DDC/CI, las teclas de brillo (que siguen
apuntando a Noctalia) funcionarán sin tocar nada más. Requiere re-login para que el grupo `i2c`
tenga efecto.

Los binds de brillo **se dejan como están** a propósito: no estorban, y son los que se activarán
con un monitor compatible.

#### Comprobar en el futuro

```bash
sudo ddcutil detect          # ¿aparece "Display 1" en vez de "Invalid display"?
ddcutil getvcp 10            # leer el brillo actual (sin sudo si el grupo i2c ya aplicó)
```

---

## Otras observaciones del sistema

Cosas detectadas de paso, **no** son problemas urgentes:

### Avisos de WirePlumber al arrancar

Los tres avisos que salían al arrancar quedan investigados y cerrados. Ver **§7** para el de
prioridad de tiempo real, que era el único con impacto real.

| Aviso | Desenlace |
|---|---|
| `nice-level to -11: Permiso denegado` | **RESUELTO** — ver §7 |
| `apple-t2x1.conf can't be accessed` | **RESUELTO** — ver §7.b |
| `libcamera SPA plugin is missing` | **RESUELTO** — ver abajo |

#### libcamera — INSTALADO

```
s-monitors-libcamera: PipeWire's libcamera SPA plugin is missing or broken
```

```bash
sudo pacman -S pipewire-libcamera     # + libcamera, libcamera-ipa, libyaml, libyuv (~143 KiB)
```

El aviso desapareció y ahora el log dice `INFO Camera libcamera v0.7.2`.

**El riesgo que había que descartar:** instalar libcamera junto a V4L2 a veces hace que la misma
cámara aparezca **duplicada** en las aplicaciones (una vez por cada backend), que es peor que el
aviso original. Se midió antes y después:

```
$ pw-dump | grep -c '"Video/Source"'
1     ← antes
1     ← después
```

**No se duplicó.** La EMEET SmartCam C960 2K sigue apareciendo una sola vez, como
`EMEET SmartCam C960 2K (V4L2)`. Si en algún momento aparece dos veces, revertir con
`sudo pacman -R pipewire-libcamera`.

> Nota: la cámara es UVC estándar y ya funcionaba por V4L2 (`/dev/video0`, `/dev/video1`).
> `libcamera` no le añade capacidades hoy — sirve para cámaras con ISP (Raspberry Pi, sensores
> embebidos, portátiles con IPU6). Se instala para dejar la pila de vídeo completa y sin avisos,
> no porque haga falta ahora.

### Adaptador Bluetooth

Ráfaga de errores del adaptador **al conectar** (no continua):

```
spa.bluez5.sink.media: Missing completion reports for packet: Bluetooth adapter firmware bug?
kernel: Bluetooth: hci0: unknown advertising packet type: 0x24
```

Es el Broadcom de Apple, conocido por esto. Fueron 8 mensajes en una ráfaga de 1 segundo
durante la conexión y luego silencio — **no está causando problemas de audio**. Solo
investigar si aparecen cortes continuos.

### Dispositivos Bluetooth emparejados

Estado actual (21 jul 2026) — **todos marcados como trusted, ya resuelto**:

| Dispositivo | MAC | Tipo | Trusted | WakeAllowed |
|---|---|---|---|---|
| Logi Z607 | `AA:AA:AA:AA:AA:AA` | altavoz | sí | — |
| Magic Trackpad | `BB:BB:BB:BB:BB:BB` | entrada | sí | sí |
| Ermes Keyboard | `CC:CC:CC:CC:CC:CC` | entrada | sí | sí |

Los dos dispositivos de entrada además tienen `WakeAllowed: yes`, así que pueden despertar el
equipo desde suspensión.

#### Qué es `Trusted` y por qué importa aquí

`Paired` y `Trusted` son cosas distintas:

- **Paired** — ya intercambiaron llaves de cifrado, se conocen.
- **Trusted** — "autoriza a este aparato automáticamente, sin preguntar".

La diferencia se nota cuando **el dispositivo inicia la conexión** (el teclado se despierta al
pulsar una tecla y pide conectarse). Si no es *trusted*, BlueZ le pide autorización a un
*agente* — el applet Bluetooth del escritorio. **Si en ese momento no hay agente corriendo, no
hay quien responda y la conexión se rechaza.**

Eso pasa justo al arrancar: en la pantalla de login o antes de que Hyprland cargue del todo.

**En este equipo el riesgo es real:** el teclado y el trackpad son Bluetooth y no hay teclado
USB de respaldo. Si no reconectan al arrancar, el equipo queda **sin entrada** y solo se
recupera enchufando un teclado USB.

Para marcarlos (ya hecho en este equipo, se deja como referencia para una reinstalación):

```bash
bluetoothctl trust BB:BB:BB:BB:BB:BB   # Magic Trackpad
bluetoothctl trust CC:CC:CC:CC:CC:CC   # Ermes Keyboard
```

No compromete la seguridad: `trust` solo aplica a dispositivos **ya emparejados**, que ya
tienen las llaves. No abre ninguna puerta nueva, solo evita el diálogo de confirmación.
Persiste en `/var/lib/bluetooth/` y se revierte con `bluetoothctl untrust <MAC>`.

> El Z607 quedó *trusted* solo, probablemente por el applet del escritorio al reconectarlo
> durante el arreglo del volumen.

---

## Comandos útiles de diagnóstico

```bash
# Estado del audio
pactl info                                  # servidor y sink por defecto
pactl list sinks short                      # todos los sinks
pactl list sinks | grep -A20 bluez_output   # detalle del sink Bluetooth
pactl list cards | grep -A15 bluez_card     # perfiles disponibles

# Bluetooth
bluetoothctl devices Connected
bluetoothctl info <MAC>

# Ver si WirePlumber lee un fragmento de config
WIREPLUMBER_DEBUG=3 timeout 5 wireplumber 2>&1 | grep -i "fragment\|section"

# Propiedades bluez5 que acepta el plugin
strings /usr/lib/spa-0.2/bluez5/libspa-bluez5.so | grep -E "^bluez5\.[a-z-]+$" | sort -u

# Estado de la cuenta / bloqueos
faillock --user $USER
passwd -S
chage -l $USER
journalctl --since "-1h" -g "sudo|authentication"

# WiFi (§3)
journalctl -k -b | grep -i brcmfmac          # que firmware busca / si cargo
ls /lib/firmware/brcm/ | grep 4364           # 68 archivos si esta instalado
sudo iw phy phy0 info | grep -E '^\s+Band'   # Band 1 = 2.4 GHz, Band 2 = 5 GHz
nmcli -f SSID,CHAN,FREQ,SIGNAL dev wifi list

# Ventilador / temperatura (§4)
H=$(dirname $(grep -l macsmc_hwmon /sys/class/hwmon/*/name))   # el numero de hwmon CAMBIA
cat $H/fan1_input $H/fan1_target $H/fan1_min $H/fan1_max
cat /sys/module/macsmc_hwmon/parameters/fan_control             # debe decir Y
sensors | grep 'Package id 0'
systemctl status macmini-fan

# Hyprland (§5)
hyprctl getoption input:touchpad:natural_scroll   # OJO: guiones aqui, guion bajo en el .lua
hyprctl getoption input:kb_variant
hyprctl devices | grep -i keymap
hyprctl monitors | grep -E 'Monitor|scale'
```

---

## 8. Instalación de programas — APLICADO

**Fecha:** 21 jul 2026

Se instaló **todo** el runbook [`instalar-programas-cachyos.md`](instalar-programas-cachyos.md)
**MENOS la §4 (servidor MongoDB)**: el usuario ya tiene un servidor de base de datos aparte. Sí se
instaló **MongoDB Compass** (`mongodb-compass-bin`), que es solo el cliente GUI para conectarse a
ese servidor.

**29 paquetes instalados y verificados** — 15 de repos oficiales + 12 de AUR + los del descompresor.

**Añadido después (21 jul):** **Zoom** (`paru -S zoom`, AUR, v7.1.5) — no estaba en la lista original;
se agregó también al runbook de programas. Para compartir pantalla en Wayland necesita los portales
`xdg-desktop-portal-hyprland` + `xdg-desktop-portal-gtk`, que ya vienen con el meta de CachyOS.

### ⚠️ TRAMPA: `paru-bin` no sirve en este sistema — usar el `paru` del repo

`paru` no venía instalado. El primer intento fue con **`paru-bin`** (AUR, binario precompilado) y
falla nada más ejecutarse:

```
paru: error while loading shared libraries: libalpm.so.15: cannot open shared object file
```

El binario del AUR está enlazado contra **libalpm.so.15** y este sistema tiene **libalpm.so.16**
(pacman 7.1). Compilar `paru` desde fuente sí funciona (se enlaza con la del sistema), **pero es
innecesario**: `paru` **está en los repos de CachyOS**.

```bash
sudo pacman -S paru        # <- ESTO. Nada de paru-bin ni de compilar desde AUR.
paru --version             # paru v2.1.0 - libalpm v16.0.1
```

> Detalle: el `paru` compilado desde el AUR arrancaba pero fallaba al resolver los paquetes
> (`no se pudieron encontrar todos los paquetes necesarios ... (target)`) aunque `paru -Si` sí los
> encontraba en el AUR. Con el del repo funcionó a la primera. **No perder tiempo: usar el del repo.**

### ⚠️ Mirror desincronizado (error 404 en un `.sig`)

A mitad de la instalación de AUR:

```
error: no se pudo obtener el archivo «cmake-4.4.0-1.1-x86_64_v3.pkg.tar.zst.sig»
       desde mirror.krfoss.org: The requested URL returned error: 404
```

No es culpa de los paquetes: es un **mirror con la firma desincronizada**. Se arregla refrescando
las bases de datos y reintentando:

```bash
sudo pacman -Syy      # refresca DBs (NO -Syu, para no arrastrar el kernel sin querer)
pacman -Qu | wc -l    # comprobar cuantos updates quedan pendientes antes de seguir
```

### Extras de escritorio aplicados (§8 del runbook de programas)

```bash
# gestor de archivos, visores y descompresor por defecto
xdg-mime default org.gnome.Nautilus.desktop inode/directory
xdg-mime default org.gnome.Papers.desktop application/pdf
# + Loupe para 10 tipos de imagen y File Roller para 10 tipos de comprimido (bucles del runbook)

# Hyprland: Super+E abre Nautilus
#   ~/.config/hypr/config/variables.lua : FILE_MANAGER = "nautilus"   (estaba "dolphin")

# puente para apps que llaman a "dolphin" por su nombre (p.ej. "mostrar en carpeta")
~/.local/bin/dolphin  ->  script que redirige a nautilus

# Arduino: puerto serie sin sudo (requiere RE-LOGUEAR para que aplique)
sudo usermod -aG uucp,lock ermesbatista

mkdir -p ~/Pictures/Wallpapers    # rotacion aleatoria de fondos, se activa por la GUI de Noctalia
```

**Presentar en TV** (`gnome-network-displays`): atajo **`Super + M`** añadido a `binds.lua` y
lanzador buscable `~/.local/share/applications/presentar-tv.desktop` (keywords: tv, presentar,
espejo, airplay, cast, miracast…).

### ⚠️ `ufw` ESTÁ ACTIVO en este equipo → las reglas de casting SÍ hacían falta

Es la causa documentada del "la TV se queda cargando": las Smart-TV tipo **Chromecast** descargan el
vídeo de un **puerto alto aleatorio** de la máquina, y `ufw deny incoming` lo bloquea. Aplicadas:

```bash
for net in 192.168.0.0/16 10.0.0.0/8 172.16.0.0/12; do
  sudo ufw allow proto tcp from $net to any port 32768:60999 comment 'Chromecast/cast media (GND)'
done
sudo ufw allow 7236/tcp comment 'Miracast RTSP'
sudo ufw allow from 192.168.49.0/24 comment 'Miracast Wi-Fi Direct'
```

Diagnóstico si aun así no va: `sudo journalctl -k | grep 'UFW BLOCK'` (sale la IP de la TV).

### Lo que NO se aplicó de ese runbook (y por qué)

| Punto | Motivo |
|---|---|
| **§4 MongoDB (servidor, réplica, keyFile)** | El usuario ya tiene un servidor de BD aparte. Solo se instaló **Compass** (cliente). Si hiciera falta el shell para conectarse al servidor remoto: `paru -S mongosh-bin mongodb-tools-bin` |
| **§6 Apps Electron diminutas** (`ELECTRON_OZONE_PLATFORM_HINT`, `--force-device-scale-factor=1.67`) | **NO APLICA.** Es un parche para el panel HiDPI 2880×1800 a escala 1.67 del MacBook. Aquí son dos monitores 1920×1080 a scale 1.0 — aplicarlo dejaría las apps enormes |
| **Quitar Dolphin** (`pacman -Rdd dolphin`) | Es dependencia del meta `cachyos-hypr-noctalia`. Nautilus ya es el predeterminado y el puente está puesto, así que quitarlo solo aporta riesgo. (El propio runbook del MacBook acaba diciendo "Dolphin quedó instalado") |

### Requieren tu intervención (no se pueden automatizar)

- ✅ **Google Drive con rclone** — **YA HECHO**, ver §8.b.
- **GitHub CLI**: `gh auth login` (GitHub.com → HTTPS → login por navegador).
- **Re-loguear** para que aplique el grupo `uucp` del Arduino.

### 8.b Google Drive montado con rclone — APLICADO

**Fecha:** 21 jul 2026 · Cuenta: `tu-correo@ejemplo.com` · Carpeta: **`~/GoogleDrive`**

Google no tiene cliente Linux. Solución gratis del runbook de programas (§7): `rclone` montando el
Drive como una carpeta más, con caché local.

#### Credenciales propias (obligatorio)

El `client_id` compartido de rclone **se retira en 2026**, así que hay que crear uno propio en
**https://console.cloud.google.com/**:

1. Proyecto nuevo (aquí: número **561660312847**).
2. **Habilitar la Google Drive API** ← ver la trampa de abajo.
3. **Pantalla de consentimiento OAuth** → Externo → **PUBLICAR a Producción**
   (si se queda en "Prueba", el token **caduca a los 7 días** y da `Error 403 access_denied`).
4. **Credenciales → ID de cliente OAuth → App de escritorio** → copiar Client ID y Client Secret.

> 🔐 **Las credenciales NO se anotan en este archivo** (esta USB circula). Están guardadas en
> `~/.config/rclone/rclone.conf` de la máquina. Si se pierden, se regeneran desde la consola de
> Google con los pasos de arriba.

#### ⚠️ TRAMPA: "habilitar la Drive API" es un paso APARTE y es fácil saltárselo

Crear el proyecto y las credenciales **no habilita la API**. Si falta, la autorización del navegador
funciona, el token se guarda bien, y el fallo aparece recién al usar el remoto:

```
CRITICAL: Failed to create file system for "gdrive:": couldn't find root directory ID:
googleapi: Error 403: Google Drive API has not been used in project 561660312847 before
or it is disabled.
```

Se arregla en un clic, con el enlace que el propio error incluye
(`https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=<NUMERO>`)
→ **HABILITAR**, esperar 1-2 min a que propague y reintentar. **El token NO hay que rehacerlo.**

#### Comandos (los que funcionaron)

```bash
CID=...   # termina en .apps.googleusercontent.com
CSEC=...  # empieza por GOCSPX-
rclone config create gdrive drive scope drive client_id "$CID" client_secret "$CSEC" --non-interactive

# abre el navegador para autorizar la cuenta; al terminar IMPRIME el token JSON:
rclone authorize "drive" "$CID" "$CSEC"
#   -> "If your browser doesn't open automatically go to: http://127.0.0.1:53682/auth?state=..."
#   -> en la pantalla de Google: "Google no ha verificado esta aplicacion" es NORMAL (la app es tuya):
#      Configuracion avanzada -> Ir a ... (no seguro) -> Permitir

# guardar el token (el JSON completo entre las lineas "Paste the following..."):
rclone config update gdrive token '<JSON_DEL_TOKEN>' --non-interactive
rclone lsd gdrive:        # prueba: lista las carpetas del Drive
```

> El runbook del MacBook avisa de que `config update` **a veces se cuelga** levantando el puerto
> :53682 — el token ya quedó escrito, se puede matar. Aquí se lanzó con `timeout 25` por eso, y
> se comprobó con `grep -c refresh_token ~/.config/rclone/rclone.conf` → `1`.

#### Montaje automático al iniciar sesión

`~/.config/systemd/user/rclone-gdrive.service` (en el kit: `systemd/`), con caché VFS de 10 GB:

```bash
systemctl --user daemon-reload
systemctl --user enable --now rclone-gdrive.service
```

#### Verificación

```bash
systemctl --user is-active rclone-gdrive        # active
mount | grep -i googledrive                     # gdrive: on /home/.../GoogleDrive type fuse.rclone
ls ~/GoogleDrive                                # tus archivos
```

Estado comprobado: montado en `~/GoogleDrive`, carpetas visibles (Archivos cobrador,
EL-COBRADOR-FOTOS, NIC.DO, Opal, Parrilla PIRD…).

#### Revertir

```bash
systemctl --user disable --now rclone-gdrive.service
fusermount3 -u ~/GoogleDrive 2>/dev/null
rclone config delete gdrive
```

---

## Barrido completo del runbook del portátil (21 jul 2026)

Se revisó **sección por sección** `macbook-linux-setup.md` contra este equipo, para dejar de
descubrir huecos de uno en uno. Estado de cada una:

| § del portátil | Aplica aquí | Estado |
|---|---|---|
| 4. Audio CS8409 | ❌ | Es del chip T1; aquí es T2 → §7.b |
| 5. Touch Bar | ❌ | No hay Touch Bar |
| 5.b Brillo / luz teclado / ALS | ⚠️ parcial | Sin panel interno ni ALS. Brillo externo imposible → §9.b |
| 5.c Escala HiDPI | ❌ | 2×1080p @ scale 1.0, agrandar quitaría espacio |
| 5.d Trackpad macOS | ✅ | Aplicado → §5.c |
| 6. WiFi | ✅ | Aplicado → §3 |
| 8 / 16.c Tapa y suspensión | ❌ | Es un mini, no tiene tapa |
| 10. Ventiladores (mbpfan) | ✅ adaptado | Aquí es `macsmc_hwmon` → §4 |
| 12. Jank de Hyprland | ❌ | Es de la GPU Polaris + params de brillo. **`/proc/cmdline` verificado limpio**: no tiene `acpi_backlight=native` ni `amdgpu.backlight=1` |
| 13. OSD swayosd | ✅ adaptado | Solo volumen → §9.a |
| 14. Auto-brillo ALS | ❌ | No hay sensor de luz ni backlight |
| 15. Touch Bar en arranque | ❌ | No hay Touch Bar |
| 16. Hibernación | ❌ | Equipo de escritorio, siempre enchufado |
| 17. EasyEffects | ⚠️ | Instalado; preset del portátil NO aplicado (era para sus altavoces) → §6.d |
| 18. Terminal / fastfetch | ✅ | Aplicado → §6.a, §6.b |
| 19. Copiar/pegar con Cmd | ✅ | Aplicado → §5.a |
| 20. Capturas de pantalla | ✅ | Aplicado → §5.b |
| *Sin márgenes ni bordes* | ✅ adaptado | `border_size = 1` en vez de `0` → §8 |

**Conclusión:** no queda nada del runbook del portátil sin aplicar o sin razonar por qué no aplica.

---

## 9. GNOME Keyring (contraseñas de Chrome y demás) — APLICADO

**Fecha:** 21 jul 2026

### Qué es y por qué hacía falta

Es el **almacén de contraseñas** del escritorio (el *Secret Service* de D-Bus). Lo usan Chrome,
Signal, Bitwarden, VS Code, Postman… para guardar sesiones y credenciales. `libsecret` (la librería
cliente) ya estaba, pero **faltaba el servicio**: `gnome-keyring` no estaba instalado, así que no
había dónde guardar nada.

```bash
sudo pacman -S --needed gnome-keyring seahorse   # seahorse = GUI para ver/gestionar las claves
```

### ⚠️ EL PUNTO CLAVE DE ESTE EQUIPO: se entra SIN contraseña

CachyOS ya trae el PAM preparado (`pam_gnome_keyring.so` está en `/etc/pam.d/sddm` y en
`/etc/pam.d/sddm-autologin`), y lo normal es que el keyring se desbloquee **con la contraseña que
escribes al iniciar sesión**. Pero aquí **nunca se escribe una**: `/etc/pam.d/sddm-autologin` tiene
`auth required pam_permit.so` y `/etc/sddm.conf` tiene `[Autologin]` (ver §2). **PAM no recibe
ninguna contraseña → no puede desbloquear nada.**

Resultado si no se hace nada: al abrir Chrome sale el diálogo *"Escribe la contraseña para
desbloquear tu llavero de inicio de sesión"* en cada arranque.

### Solución aplicada: keyring de login con contraseña VACÍA

```bash
printf '\0' | gnome-keyring-daemon --daemonize --login        # crea/desbloquea el keyring 'login'
gnome-keyring-daemon --start --components=secrets,ssh
```

Crea `~/.local/share/keyrings/login.keyring` (+ `user.keystore`) con clave vacía → se desbloquea
solo, sin diálogos.

> **Sobre la seguridad:** con clave vacía las credenciales quedan protegidas solo por los permisos
> del archivo (`-rw-------`), no por cifrado real. **No empeora el modelo de seguridad de este
> equipo**, porque ya se entra a la sesión sin contraseña: quien tenga acceso físico ya podía abrir
> Chrome y ver las contraseñas guardadas. Si algún día se quita el autologin, conviene ponerle
> contraseña al keyring (Seahorse → llavero *Login* → clic derecho → *Cambiar contraseña*), y
> entonces PAM lo desbloqueará solo al iniciar sesión.

### Arranque automático

`pam_gnome_keyring.so auto_start` ya lo levanta al entrar, y además se añadió al autostart de
Hyprland (`~/.config/hypr/config/autostart.lua`) por robustez:

```lua
hl.exec_cmd("gnome-keyring-daemon --start --components=secrets,ssh")
```

El componente `ssh` además hace de **agente SSH** (recuerda las passphrases de tus claves).

### Verificación

```bash
busctl --user list | grep org.freedesktop.secrets    # el servicio debe estar registrado
ls ~/.local/share/keyrings/                          # login.keyring + user.keystore

# prueba real de guardar/leer/borrar:
secret-tool store --label='prueba' servicio prueba <<< "secreto123"
secret-tool lookup servicio prueba                   # -> secreto123
secret-tool clear servicio prueba
```

Probado y funcionando (guardó, leyó y borró correctamente).

### Revertir

```bash
sudo pacman -Rns gnome-keyring seahorse
rm -rf ~/.local/share/keyrings
sed -i '/gnome-keyring/d' ~/.config/hypr/config/autostart.lua
```

---

## Pendiente / no aplicado (y por qué)

- **Conectarse a la red WiFi**: el hardware ya funciona y escanea; falta elegir SSID y clave.
- **Validar tras un reinicio completo** que ventilador y WiFi arrancan solos (todo quedó
  `enabled`, pero el propio método de esta casa dice **verificar, no asumir**).
- **Revertir el NOPASSWD** de sudo: `sudo rm /etc/sudoers.d/99-ermesbatista-nopasswd` (ver §2).
- **Escalado de fuente** (§18 del portátil, GTK 1.1 / Qt `QT_FONT_DPI=106`): **no aplicado a
  propósito** — allá hacía falta por el panel HiDPI de 2880×1800; aquí los dos monitores son
  1920×1080 a scale 1.0 y agrandar solo quitaría espacio útil.
- **Firmware Bluetooth `.hcd`**: innecesario en este modelo (§3).
- **Re-login pendiente para §7.a y §9.b**: el usuario ya está en los grupos `realtime` e `i2c`,
  pero los límites de PAM y los permisos de grupo no entran hasta cerrar sesión y volver a entrar.
  Verificar entonces con `prlimit --nice --rtprio --memlock` (NICE debe ser 31, MEMLOCK unlimited),
  que `journalctl --user -b -u wireplumber | grep mod.rt` no devuelve nada, y que `id -nG` incluye
  `realtime` e `i2c`.
- **Validar que `swayosd-server` arranca solo** (§9.a): quedó en `autostart.lua`, pero en esta
  sesión se lanzó a mano. Tras el próximo login: `pgrep -a swayosd` debe devolver el proceso.
- **Probar el jack de 3.5mm** (§7.b): el perfil ya expone el puerto y la detección de jack
  responde, pero **no se ha enchufado nada todavía** para confirmar que conmuta y suena. Método de
  esta casa: verificar, no asumir.
- **Conflicto futuro de `apple-t2x1.conf`** (§7.b): vive en `/usr/share/`, fuera de pacman. Si un
  update de `apple-t2-audio-config` lo incluye, dará `exists in filesystem` — borrar el nuestro.

---

*Documentado el 21 de julio de 2026. §1–§2 por la mañana; §3–§6 por la tarde.*
