#!/usr/bin/env python3
# Auto-brillo de PANTALLA por sensor de luz (ALS) — MacBookPro13,3 / CachyOS / Hyprland.
#
# Diseño (ver §13/§14 del doc macbook-linux-setup.md):
#   - Escribe el backlight NATIVO gmux_backlight (sysfs directo, permiso por udev
#     90-backlight-gmux.rules) → SIN AUX = SIN jank.
#   - Rampa SUAVE (~60 pasos/seg) para que se vea fluido como la Touch Bar (no a escalones).
#   - NO llama a swayosd y el OSD de brillo de Noctalia está apagado → cambios AUTOMÁTICOS
#     SILENCIOSOS (sin OSD). El OSD solo sale con las teclas del Touch Bar (van por swayosd).
#   - Respeta el ajuste MANUAL: si el usuario cambia el brillo (swayosd escribe gmux), lo
#     detecta y lo toma como OFFSET sobre la curva (estilo macOS).
#
# El ALS de Apple NO da lux. Calibrado (2026-07-18): tapado=0, interior≈20-23, luz fuerte=cientos.
# Ajustar a gusto: editar CURVE y  systemctl --user restart als-backlight
# El campo iio varía entre boots (in_illuminance_input vs in_illuminance_raw) → find_als prueba ambos.

import os
import glob
import time

BL = "/sys/class/backlight/gmux_backlight"
BRIGHT = f"{BL}/brightness"

# curva  luz(ALS) -> brillo(%)  ; interpolación lineal
CURVE = [
    (0,   18),
    (2,   35),
    (6,   50),
    (15,  65),
    (40,  80),
    (120, 92),
    (400, 100),
]

MIN_PCT = 8
MAX_PCT = 100
ALS_INTERVAL = 0.4     # s entre lecturas del sensor
EMA_ALPHA = 0.25       # suavizado del sensor
OFFSET_CLAMP = 50.0    # tope del offset manual
RAMP_TICK = 1.0 / 60   # ~60 Hz durante la rampa (suave)
IDLE_TICK = 0.15       # en reposo, poll lento (bajo consumo)
RAMP_FRAC = 0.02       # paso de rampa = 2% del rango por tick → rango completo ~0.8s
MANUAL_TOL_FRAC = 0.015
DEADBAND_FRAC = 0.004


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def find_als():
    for d in sorted(glob.glob("/sys/bus/iio/devices/iio:device*")):
        try:
            if open(f"{d}/name").read().strip() == "als":
                for fld in ("in_illuminance_input", "in_illuminance_raw",
                            "in_intensity_both_input"):
                    p = f"{d}/{fld}"
                    if os.path.exists(p):
                        return p
        except OSError:
            continue
    return None


def curve_pct(a):
    p = CURVE
    if a <= p[0][0]:
        return p[0][1]
    if a >= p[-1][0]:
        return p[-1][1]
    for (x0, y0), (x1, y1) in zip(p, p[1:]):
        if x0 <= a <= x1:
            return y0 + (a - x0) / (x1 - x0) * (y1 - y0)
    return p[-1][1]


def main():
    als = None
    while als is None:
        als = find_als()
        if als is None:
            time.sleep(2)

    maxb = read_int(f"{BL}/max_brightness")
    ramp_step = max(1, int(maxb * RAMP_FRAC))
    manual_tol = maxb * MANUAL_TOL_FRAC
    deadband = maxb * DEADBAND_FRAC

    def write(v):
        v = max(0, min(maxb, int(round(v))))
        try:
            with open(BRIGHT, "w") as f:
                f.write(str(v))
        except OSError:
            pass

    ema = float(read_int(als))
    cur = float(read_int(BRIGHT))
    last_written = cur
    offset = max(-OFFSET_CLAMP, min(OFFSET_CLAMP, cur / maxb * 100 - curve_pct(ema)))
    next_als = 0.0

    while True:
        now = time.monotonic()

        if now >= next_als:
            next_als = now + ALS_INTERVAL
            try:
                ema = EMA_ALPHA * read_int(als) + (1 - EMA_ALPHA) * ema
            except OSError:
                pass
            # detección de ajuste manual (swayosd escribió gmux)
            try:
                actual = read_int(BRIGHT)
            except OSError:
                actual = last_written
            if abs(actual - last_written) > manual_tol:
                cur = float(actual)
                offset = max(-OFFSET_CLAMP,
                             min(OFFSET_CLAMP, actual / maxb * 100 - curve_pct(ema)))

        target = max(MIN_PCT, min(MAX_PCT, curve_pct(ema) + offset)) / 100.0 * maxb

        if abs(target - cur) > deadband:
            if target > cur:
                cur = min(target, cur + ramp_step)
            else:
                cur = max(target, cur - ramp_step)
            write(cur)
            last_written = cur
            time.sleep(RAMP_TICK)
        else:
            time.sleep(IDLE_TICK)


if __name__ == "__main__":
    main()
