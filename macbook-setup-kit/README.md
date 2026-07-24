# Kit de configuración — MacBookPro13,3 (CachyOS/Arch, Hyprland)

Copia esta carpeta a la MacBook nueva (USB) y sigue el **RUNBOOK** del documento
`macbook-linux-setup.md`. Solo sirve para hardware IDÉNTICO: verifica con
`cat /sys/class/dmi/id/product_name` → debe decir `MacBookPro13,3`.

REGLA DE ORO: el kernel de CachyOS usa clang → todos los DKMS con `LLVM=1`.

## Contenido
- `firmware/brcmfmac43602-pcie.txt` — NVRAM que HABILITA el WiFi 2.4 **y 5 GHz**
  (bug kernel 193121, adjunto 285753, boardtype=0x073e). `macaddr=00:90:4c:0d:f4:3e`
  (cámbiala si `ethtool -P wlan0` muestra otra). Va a `/lib/firmware/brcm/` con dos nombres:
  `brcmfmac43602-pcie.txt` y `brcmfmac43602-pcie.Apple Inc.-MacBookPro13,3.txt`.
- `modprobe/brcmfmac.conf` → `/etc/modprobe.d/` (feature_disable=0x82000, estabiliza).
- `scripts/amdgpu-backlight.py` → `/usr/local/bin/` (755). Daemon único: auto-brillo por curva
  (sensor de luz) + puente al panel por AUX/DPCD. NO dispara el OSD en cambios automáticos.
- `systemd/amdgpu-backlight.service` → `/etc/systemd/system/` (enable --now).
- `udev/90-backlight-amdgpu.rules` → `/etc/udev/rules.d/` (permite escribir el brillo sin sudo).
- `system-sleep/99-macbook-resume` → `/usr/lib/systemd/system-sleep/` (755). SUSPENSIÓN:
  al despertar reinicia `amdgpu-backlight.service` para que el panel encienda con brillo
  (reabre el fd AUX/DPCD que queda viejo tras resume).

## GRUB: añadir a GRUB_CMDLINE_LINUX_DEFAULT y `grub-mkconfig`:
    acpi_backlight=native amdgpu.backlight=1 mem_sleep_default=s2idle
  (brillo: acpi_backlight=native amdgpu.backlight=1 · SUSPENSIÓN: mem_sleep_default=s2idle
   → sin s2idle el GPU AMD se cuelga al reanudar desde `deep` y la pantalla no enciende.)

## No incluido (se clona en el momento):
- Audio: https://github.com/davidjo/snd_hda_macbookpro  (dkms.conf: MAKE="make LLVM=1")
- Touch Bar: https://github.com/marc-git/macbook12-spi-driver -b touchbar-driver-hid-driver
  (3 parches kernel 7.1 — ver §5 del documento).
