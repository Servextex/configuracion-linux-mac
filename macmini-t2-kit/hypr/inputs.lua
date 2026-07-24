-- Input configuration

hl.config({
    input = {
        -- sensitivity = -0.25,
        accel_profile = "flat",

        -- Acentos estilo macOS (Option + letra). En Wayland no existe el popup press-and-hold;
        -- la variante altgr-intl pone las dead keys SOLO en AltGr (Alt derecha), asi ' " ` ~
        -- siguen normales para programar.
        --   AltDcha + a/e/i/o/u -> aeiou con tilde  ·  AltDcha + n -> enye  ·  AltDcha + ' y luego u -> u con dieresis
        kb_layout  = "us",
        kb_variant = "altgr-intl",

        -- Magic Trackpad (Bluetooth) estilo macOS. Aplica en cuanto el trackpad se conecta.
        touchpad = {
            natural_scroll       = true,  -- el contenido sigue a los dedos (como Mac)
            tap_to_click         = true,  -- tocar = clic
            tap_and_drag         = true,  -- tocar-y-arrastrar
            clickfinger_behavior = true,  -- 2 dedos = clic derecho, 3 dedos = clic medio
            disable_while_typing = true,  -- ignora el trackpad al teclear
            drag_lock            = true,
        },
    },
    -- Uncomment the section below to enable software cursors; this can help with cursor display or behavior issues
    -- cursor = {
    --     no_hardware_cursors = 1,
    -- },
})

-- Gestos estilo macOS: swipe horizontal de 3 Y 4 dedos = cambiar de escritorio (spaces).
-- Antes el de 3 dedos hacia close/fullscreen/float (no-Mac) y solo el de 4 cambiaba workspace.
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 4, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 3, direction = "up",         action = "fullscreen" })
hl.gesture({ fingers = 3, direction = "down",       action = "close" })
