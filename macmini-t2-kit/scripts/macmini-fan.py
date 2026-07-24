#!/usr/bin/env python3
# Control de ventilador para Macmini8,1 (chip T2) en Linux.
#
# Por que existe: el SMC del T2 deja el ventilador en su MINIMO (1700 RPM) bajo Linux
# porque no recibe las temperaturas que le daria macOS -> la CPU llega a 94-100 C y hace
# THROTTLING. t2fanrd no sirve aqui: busca /sys/devices/pci*/.../APP0001:00/fan*_manual|_output
# y este kernel expone el SMC por ACPI con el driver macsmc_hwmon (fan1_target).
#
# Requiere: macsmc_hwmon cargado con fan_control=1 (/etc/modprobe.d/99-macsmc-fan.conf).
# Curva equivalente a la de mbpfan del MacBook (low 50 / high 55 / max 68).

import glob
import os
import signal
import sys
import time

# --- rutas ---
HWMON_GLOB = "/sys/class/hwmon/hwmon*"
CORETEMP = "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp1_input"  # Package id 0

# --- curva temperatura(C) -> RPM ; interpolacion lineal ---
# Perfil FRESCO (elegido por el usuario): misma filosofia que el mbpfan 50/55/68 del MacBook,
# pero estirada al rango real de este equipo. El i7 del Mac mini 2018 vive entre 70 y 92 C en uso
# normal; con la curva del MacBook el ventilador quedaba CLAVADO en 4400 RPM todo el tiempo.
# Para mas silencio: subir los grados. Para mas frio: bajarlos. Luego:
#   sudo systemctl restart macmini-fan
CURVE = [
    (50, 1700),
    (60, 2600),
    (70, 3400),
    (80, 4100),
    (88, 4400),
]

POLL = 2.0          # segundos entre lecturas
EMA_ALPHA = 0.4     # suavizado de la temperatura (evita subir/bajar por picos de 1 s)
DEADBAND = 60       # RPM: no reescribir por cambios menores (menos trafico al SMC)
STEP_UP = 400       # rampa de subida (RPM por ciclo)
STEP_DOWN = 120     # rampa de bajada, mas lenta = menos "bombeo" de ruido
SAFE_RPM = 2600     # al salir se deja aqui (nunca al minimo, por si el daemon muere caliente)


def find_fan():
    for d in sorted(glob.glob(HWMON_GLOB)):
        try:
            if open(f"{d}/name").read().strip() == "macsmc_hwmon":
                if os.path.exists(f"{d}/fan1_target"):
                    return d
        except OSError:
            continue
    return None


def read_int(path):
    with open(path) as f:
        return int(f.read().strip())


def cpu_temp():
    for p in glob.glob(CORETEMP):
        try:
            return read_int(p) / 1000.0
        except OSError:
            continue
    return None


def curve_rpm(temp):
    pts = CURVE
    if temp <= pts[0][0]:
        return pts[0][1]
    if temp >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= temp <= x1:
            t = (temp - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return pts[-1][1]


def main():
    hw = find_fan()
    if hw is None:
        sys.exit("macsmc_hwmon con fan1_target no encontrado "
                 "(falta fan_control=1 en /etc/modprobe.d/99-macsmc-fan.conf?)")

    fan_min = read_int(f"{hw}/fan1_min")
    fan_max = read_int(f"{hw}/fan1_max")
    target_path = f"{hw}/fan1_target"

    def write_rpm(rpm):
        rpm = int(max(fan_min, min(fan_max, rpm)))
        with open(target_path, "w") as f:
            f.write(str(rpm))
        return rpm

    def on_exit(signum, frame):
        # nunca dejar el ventilador al minimo: si el daemon se cae, el SMC no lo sube solo
        try:
            write_rpm(SAFE_RPM)
        except OSError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, on_exit)
    signal.signal(signal.SIGINT, on_exit)

    t = cpu_temp()
    if t is None:
        sys.exit("sensor coretemp no encontrado")
    ema = t
    current = write_rpm(curve_rpm(ema))

    while True:
        try:
            t = cpu_temp()
            if t is not None:
                ema = EMA_ALPHA * t + (1 - EMA_ALPHA) * ema
            target = curve_rpm(ema)

            if abs(target - current) > DEADBAND:
                if target > current:
                    current = write_rpm(min(target, current + STEP_UP))
                else:
                    current = write_rpm(max(target, current - STEP_DOWN))
        except OSError:
            time.sleep(1)
        time.sleep(POLL)


if __name__ == "__main__":
    main()
