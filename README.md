# Configuración de Linux en hardware Mac (CachyOS + Hyprland)

Runbooks, kits de configuración y notas de solución de problemas para correr **Linux
(CachyOS / Arch)** en equipos **Apple**: un **Mac mini 8,1 (2018, Intel + chip T2)** y un
**MacBook Pro 13,3 (2016, Intel + AMD)**.

Todo el stack es el mismo en ambas máquinas:

- **SO:** CachyOS (Arch-based)
- **Bootloader:** Limine (no GRUB en las instalaciones nuevas)
- **Compositor:** Hyprland (Wayland, config en Lua)
- **Shell gráfico:** Noctalia · **Shell de terminal:** fish
- **Audio:** PipeWire + WirePlumber

> ⚠️ **Hardware específico.** Estas guías resuelven problemas concretos de estos modelos de
> Apple (WiFi Broadcom, chip T2, Touch Bar, brillo por AMD, ventilador por `macsmc`, etc.).
> Verifica tu modelo con `cat /sys/class/dmi/id/product_name` antes de aplicar nada. En otro
> hardware muchos pasos **no aplican**.

---

## 📁 Estructura del repositorio

```
configuracion-linux-mac/
├── guias/              Runbooks largos "de principio a fin" por equipo
├── runbooks/           Recetas cortas para ajustes puntuales del sistema
├── macmini-t2-kit/     Configs listas para copiar → Mac mini 8,1 (chip T2)
└── macbook-setup-kit/  Configs listas para copiar → MacBook Pro 13,3
```

---

## 📖 Guías completas (`guias/`)

| Documento | Equipo | Qué cubre |
|---|---|---|
| [`macmini-8-1-cachyos.md`](guias/macmini-8-1-cachyos.md) | Mac mini 8,1 (T2) | Registro de problemas diagnosticados y resueltos: WiFi BCM4364, audio T2, ventilador `macsmc_hwmon`, Bluetooth, etc. |
| [`macbook-linux-setup.md`](guias/macbook-linux-setup.md) | MacBook Pro 13,3 | Puesta a punto de periféricos: brillo nativo AMD (`gmux_backlight`), Touch Bar, suspensión, WiFi. Incluye **RUNBOOK DEFINITIVO**. |
| [`instalar-programas-cachyos.md`](guias/instalar-programas-cachyos.md) | Ambos | Runbook reutilizable de instalación de software (Chrome, VS Code, MongoDB con réplica, etc.) vía `pacman` + AUR. |

---

## 🔧 Runbooks cortos (`runbooks/`)

Recetas de un solo tema, con comandos exactos y las "trampas" a recordar:

| Runbook | Tema |
|---|---|
| [`Tema-Iconos-Papirus.md`](runbooks/Tema-Iconos-Papirus.md) | Iconos por lenguaje (Python, JS…) cambiando el tema a Papirus (GTK + KDE) |
| [`Quitar-Transparencia-Hyprland-Noctalia.md`](runbooks/Quitar-Transparencia-Hyprland-Noctalia.md) | Apagar transparencia/blur en Hyprland y Noctalia |
| [`README-Configuracion-Disco-Descargas.md`](runbooks/README-Configuracion-Disco-Descargas.md) | Reconfigurar disco de descargas (+ script [`reconfigurar-disco.sh`](runbooks/reconfigurar-disco.sh)) |
| [`redireccion-apps-mensajeria-disco-externo.md`](runbooks/redireccion-apps-mensajeria-disco-externo.md) | Redirigir apps de mensajería a un disco externo |
| [`Web-Apps-Chrome-WhatsApp-Keep-Notes.md`](runbooks/Web-Apps-Chrome-WhatsApp-Keep-Notes.md) | Crear web-apps de Chrome (WhatsApp, Keep, Notes) |

---

## 📦 Kits de configuración

Carpetas con archivos de config **listos para copiar** al equipo correspondiente. Cada kit
acompaña a su guía larga (arriba).

### `macmini-t2-kit/` — Mac mini 8,1 (chip T2)
Configs de Hyprland (`hypr/*.lua`), Noctalia, fish (`config.fish` + funciones), audio T2
(`audio/`), servicios systemd (ventilador, rclone), scripts (`macmini-fan.py`, `mac-clip.sh`)
y utilidades t2linux (`fetch-macOS-v2.py`, `firmware-linux-parcheado.sh`).

### `macbook-setup-kit/` — MacBook Pro 13,3
Ver su [`README.md`](macbook-setup-kit/README.md) propio. Incluye NVRAM WiFi, daemon de
auto-brillo AMD, servicios systemd, reglas udev, grub y hooks de suspensión.

---

## ⚠️ Firmware NO incluido (copyright)

El firmware WiFi de Broadcom extraído de macOS (`brcm-4364-firmware-sonoma.tar`) **no está en
este repositorio** porque es software propietario de Apple/Broadcom y no puede redistribuirse.
Para obtenerlo legítimamente, extráelo de macOS con el flujo del script
[`macmini-t2-kit/t2linux/firmware-linux-parcheado.sh`](macmini-t2-kit/t2linux/firmware-linux-parcheado.sh)
(basado en el proyecto **[t2linux](https://wiki.t2linux.org/)**).

---

## 🔒 Nota de privacidad

Esta es una versión **pública y sanitizada**: se reemplazaron correo personal y direcciones
MAC reales por placeholders (`tu-correo@ejemplo.com`, `AA:AA:...`). Cambia esos valores por
los de tu equipo al aplicar las guías.

---

## 🙏 Créditos

Los scripts de la carpeta `t2linux/` son de terceros y conservan su licencia y copyright
originales (proyecto [t2linux](https://github.com/t2linux) — Aditya Garg, Orlando Chamberlain,
Sharpened Blade). El resto de la documentación y configs propias se publican bajo la licencia
de este repositorio (ver [`LICENSE`](LICENSE)).
