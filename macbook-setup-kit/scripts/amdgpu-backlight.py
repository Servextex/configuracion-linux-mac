#!/usr/bin/env python3
# Daemon de brillo v2 para MacBookPro13,3 (GPU AMD Polaris, panel eDP AUX/DPCD).
#
# v2 (2026-07-18): reescrito para NO degradar las animaciones del compositor.
#   CAUSA del jank en v1: cada transaccion AUX/DPCD se serializa con los atomic-commit
#   del compositor (misma capa DC de amdgpu). v1 hacia 2 transacciones por cambio,
#   re-asertaba el panel CADA 3s aunque nada cambiara, y con deadband minusculo (0.6%)
#   + ALS ruidoso escribia casi cada 0.3s -> el compositor perdia frames (saltos/lentitud).
#   ARREGLOS:
#     (1) UNA sola transaccion AUX de 3 bytes [modo,msb,lsb] en 0x721..0x723 (antes 2).
#     (2) SIN reassert periodico (el hook system-sleep reinicia el servicio en resume).
#     (3) deadband grande (4%) + poll lento (1s) -> en luz estable = CERO escrituras AUX.
#   => en reposo no toca el canal AUX -> el compositor no pierde frames.
#
# Auto-brillo por CURVA del sensor de luz (ALS). Entrada MANUAL por amdgpu_bl1 (teclas
# del Touch Bar via Noctalia) = se toma como offset sobre la curva (estilo macOS).
# Ajustar curva a gusto: editar CURVE y  sudo systemctl restart amdgpu-backlight

import os
import glob
import time

BL = "/sys/class/backlight/amdgpu_bl1"
REG_MODE = 0x721           # se escriben 0x721(modo),0x722(MSB),0x723(LSB) en UNA transaccion
AUX_MODE_BYTE = 0x06       # control de brillo por AUX (bits[1:0]=10)

# --- curva luz(ALS crudo) -> brillo(%). En este equipo el ALS expone in_illuminance_raw;
#     recalibrar en vivo (editar + restart). El ALS de Apple NO da lux. ---
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
POLL = 1.0             # v1: 0.3 -> v2 lento (auto-brillo no necesita mas)
EMA_ALPHA = 0.15       # suavizado fuerte del sensor (menor = mas suave)
STEP_PCT = 8.0         # rampa: max cambio de brillo por ciclo (transicion suave)
DEADBAND_PCT = 4.0     # v1: 0.6 -> v2 grande: el ruido del ALS NO dispara escrituras
OFFSET_CLAMP = 60.0


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def find_als_path():
    for d in sorted(glob.glob("/sys/bus/iio/devices/iio:device*")):
        try:
            if open(f"{d}/name").read().strip() == "als":
                for field in ("in_illuminance_input", "in_illuminance_raw"):
                    p = f"{d}/{field}"
                    if os.path.exists(p):
                        return p
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
    for p in sorted(glob.glob("/dev/drm_dp_aux*")):
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


def write_panel(fd, pct):
    # UNA sola transaccion AUX: modo(0x721) + MSB(0x722) + LSB(0x723)
    val = max(0, min(65535, round(pct / 100.0 * 65535)))
    os.pwrite(fd, bytes([AUX_MODE_BYTE, (val >> 8) & 0xFF, val & 0xFF]), REG_MODE)


def main():
    als_path = None
    while als_path is None:
        als_path = find_als_path()
        if als_path is None:
            time.sleep(2)

    # esperar a amdgpu_bl1 (aparece tras reboot con los params de Limine)
    while not os.path.exists(f"{BL}/max_brightness"):
        time.sleep(2)
    max_bl = read_int(f"{BL}/max_brightness")
    manual_tol = 0.01 * max_bl  # 1% => cambio manual real (teclas)

    fd = None
    while fd is None:
        fd = open_edp_aux()
        if fd is None:
            time.sleep(0.5)

    ema = float(read_int(als_path))
    last_manual = read_int(f"{BL}/brightness")
    manual_pct = last_manual / max_bl * 100.0
    offset = max(-OFFSET_CLAMP, min(OFFSET_CLAMP, manual_pct - curve_pct(ema)))
    panel_pct = manual_pct
    write_panel(fd, panel_pct)   # asentar el panel una vez al arrancar

    while True:
        try:
            if fd is None:
                fd = open_edp_aux()
                if fd is None:
                    time.sleep(0.5)
                    continue

            raw_als = read_int(als_path)
            ema = EMA_ALPHA * raw_als + (1 - EMA_ALPHA) * ema

            # deteccion de ajuste MANUAL (teclas del Touch Bar via Noctalia)
            cur_manual = read_int(f"{BL}/brightness")
            if abs(cur_manual - last_manual) > manual_tol:
                manual_pct = cur_manual / max_bl * 100.0
                offset = max(-OFFSET_CLAMP, min(OFFSET_CLAMP,
                                                manual_pct - curve_pct(ema)))
            last_manual = cur_manual

            target = max(MIN_PCT, min(MAX_PCT, curve_pct(ema) + offset))

            # SOLO escribe si el objetivo supero el deadband -> en reposo CERO AUX
            if abs(target - panel_pct) > DEADBAND_PCT:
                if target > panel_pct:
                    panel_pct = min(target, panel_pct + STEP_PCT)
                else:
                    panel_pct = max(target, panel_pct - STEP_PCT)
                write_panel(fd, panel_pct)
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
