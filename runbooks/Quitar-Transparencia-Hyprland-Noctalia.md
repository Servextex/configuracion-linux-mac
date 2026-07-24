# Quitar la transparencia (Hyprland + Noctalia)

Documentado el 2026-07-21. Equipo: Mac Mini con CachyOS. Usuario: `ermesbatista`.

**IMPORTANTE:** este equipo NO usa KDE/KWin como escritorio. Usa:
- **Compositor:** Hyprland  (config Lua en `~/.config/hypr/`)
- **Shell / barra / dock / paneles:** Noctalia  (config en `~/.config/noctalia/config.toml`)

Por eso tocar KWin (kwinrc, kwinrulesrc, blur/contrast) **NO sirve de nada** — KWin ni
siquiera corre. La transparencia sale de **dos** sitios y hay que apagar ambos.

---

## 1. Ventanas transparentes → Hyprland

Archivo: `~/.config/hypr/config/decorations.lua`, sección `decoration = { ... }`.

Valores que traían transparencia (por defecto de CachyOS):
```lua
active_opacity = 0.95,      -- ventana activa 95% (algo transparente)
inactive_opacity = 0.85,    -- ventana inactiva 85% (bien transparente)
blur = {
    size = 5,
    passes = 4,
    special = true,
},
```

Dejarlo SÓLIDO (sin transparencia):
```lua
active_opacity = 1,
inactive_opacity = 1,
fullscreen_opacity = 1,
blur = {
    enabled = false,        -- <-- apaga el desenfoque
    size = 5,
    passes = 4,
    special = true,
},
```

Aplicar sin reiniciar:
```bash
hyprctl reload
```
Verificar:
```bash
hyprctl getoption decoration:active_opacity     # debe decir float: 1.000000
hyprctl getoption decoration:inactive_opacity   # debe decir float: 1.000000
```

---

## 2. Barra, dock y paneles transparentes → Noctalia

Archivo: `~/.config/noctalia/config.toml`, sección `[shell.panel]`.

La clave es **`transparency_mode`**, con 3 valores posibles:
- `"glass"`  = todo translúcido (era el valor por defecto)
- `"soft"`   = translucidez suave
- `"solid"`  = **SÓLIDO, sin transparencia**  ← el que queremos

Agregar/editar bajo `[shell.panel]`:
```toml
    [shell.panel]
    open_near_click_control_center = true
    session_placement = "floating"
    session_position = "center"
    transparency_mode = "solid"
```

Noctalia recarga solo al guardar el archivo (vigila el config). Si no, se puede
reiniciar el shell desde Hyprland.

---

## Resumen rápido (copiar/pegar mental)

| Qué se ve transparente | Archivo | Cambio |
|---|---|---|
| Ventanas de apps | `~/.config/hypr/config/decorations.lua` | `active_opacity = 1`, `inactive_opacity = 1`, `blur.enabled = false` → `hyprctl reload` |
| Barra / dock / paneles | `~/.config/noctalia/config.toml` `[shell.panel]` | `transparency_mode = "solid"` |

> Ambos cambios están en archivos de config, así que **son permanentes** (sobreviven
> reinicio). Hay backups automáticos junto a cada archivo (`*.bak-FECHA`).
