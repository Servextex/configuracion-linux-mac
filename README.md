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

## 🤖 Recomendado: hazlo con un agente de IA (mucho más rápido)

**Toda esta configuración y documentación se hizo con la ayuda de un agente de IA corriendo
localmente en la propia máquina.** Es la forma más rápida y menos tediosa de replicarlo: el
agente diagnostica el hardware, ejecuta los comandos, edita los archivos de configuración y
va documentando cada paso por ti — en vez de que tú copies y pegues decenas de comandos a mano.

### Cómo se arrancó (ejemplo)

1. **Instalar un primer agente de IA** para tener asistencia desde el inicio. Aquí se empezó
   con **[Antigravity](https://antigravity.google/)** (el editor con agente de Google).
2. **Desde ese agente, instalar el agente principal:** se usó Antigravity para instalar
   **[Claude Code](https://www.claude.com/product/claude-code)**, que fue el que ejecutó la
   mayor parte del trabajo (diagnóstico, comandos, edición de configs y esta documentación).
3. A partir de ahí, se le va pidiendo al agente cada tarea de estas guías y él la ejecuta.

> El agente concreto es **a tu gusto** — Claude Code, otro CLI, la extensión que prefieras.
> Lo importante es que corra **localmente** en el equipo que estás configurando, para que
> pueda ejecutar comandos y tocar archivos directamente.

### Dale acceso total al agente MIENTRAS dura la configuración

Para que el proceso no sea tedioso, lo ideal es **darle acceso total al agente de forma
temporal** durante la configuración, para que **no pida confirmación en cada paso**. Si tienes
que aprobar cada comando uno por uno, el proceso se vuelve lentísimo. Dos ajustes ayudan:

1. **Que el agente no pida confirmación.** Actívale su modo de permisos amplios / "saltar
   confirmaciones" (en Claude Code, por ejemplo, su modo sin prompts de permisos). Así ejecuta
   los comandos de las guías sin detenerse a preguntar cada vez.

2. **Quitar la clave de `sudo` temporalmente.** Para que el agente pueda ejecutar comandos con
   privilegios sin trabarse pidiendo contraseña a cada rato:
   ```bash
   # Reemplaza tu-usuario por tu usuario real ($USER)
   echo 'tu-usuario ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/99-setup-nopasswd
   sudo chmod 440 /etc/sudoers.d/99-setup-nopasswd
   ```

> 🔒 **IMPORTANTE — revertir al terminar.** Estos dos ajustes **bajan la seguridad** del equipo
> y son **solo para la fase de configuración**. En cuanto termines, **vuelve a exigir la clave de
> `sudo`** eliminando el archivo:
> ```bash
> sudo rm /etc/sudoers.d/99-setup-nopasswd
> ```
> Y desactiva el modo "sin confirmaciones" del agente. No dejes la máquina de uso diario con
> `sudo` sin contraseña ni con un agente con acceso total permanente.

### ¿Prefieres hacerlo manualmente?

Se puede, todos los runbooks tienen los comandos exactos. Pero **ten en cuenta que a mano
toma bastante más tiempo y es más tedioso** (diagnosticar, buscar cada comando, editar cada
config, verificar). Con un agente local el mismo proceso se hace mucho más rápido y con menos
errores.

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
