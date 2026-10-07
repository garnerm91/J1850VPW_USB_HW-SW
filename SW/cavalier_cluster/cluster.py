"""
cluster.py - J1850 frames for a Cavalier instrument cluster.

These are the 6-byte J1850 payloads (header + data). The STM32 firmware adds
the CRC, so protocol.build_send_frame() wraps them for the USB link.

    Tach      88 1B 10 10 XX YY       XX = major, YY = minor
    Speedo    88 29 10 02 XX YY       XX = major, YY = minor
    Fuel      8A EA 40 02 80 XX       XX = level 00-FF
    Odometer  C8 7B 40 01 AA BB CC DD raw = big-endian 32-bit, miles = raw // 103
    Coolant   8A EA 40 02 81 XX       XX = temp 00-FF
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

ODO_DIVISOR = 103
ODO_MAX = 0xFFFFFFFF // ODO_DIVISOR      # largest value that fits in 32 bits


def _byte(value: int, name: str) -> int:
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must be 0-255, got {value}")
    return value


def tach_frame(major: int, minor: int) -> bytes:
    return bytes([0x88, 0x1B, 0x10, 0x10, _byte(major, "major"), _byte(minor, "minor")])


def speedo_frame(major: int, minor: int) -> bytes:
    return bytes([0x88, 0x29, 0x10, 0x02, _byte(major, "major"), _byte(minor, "minor")])


def fuel_frame(level: int) -> bytes:
    return bytes([0x8A, 0xEA, 0x40, 0x02, 0x80, _byte(level, "fuel level")])


def coolant_frame(level: int) -> bytes:
    return bytes([0x8A, 0xEA, 0x40, 0x02, 0x81, _byte(level, "coolant")])


def odo_frame(value: int) -> bytes:
    """`value` is what the cluster should display (raw // 103)."""
    if not 0 <= value <= ODO_MAX:
        raise ValueError(f"odometer must be 0-{ODO_MAX}, got {value}")
    raw = value * ODO_DIVISOR
    return bytes([0xC8, 0x7B, 0x40, 0x01]) + raw.to_bytes(4, "big")


def decode_odo(frame: bytes) -> int:
    """Inverse of odo_frame (useful for checking sniffed frames)."""
    raw = int.from_bytes(frame[4:8], "big")
    return raw // ODO_DIVISOR


# ======================================================================
# Decoding (receive side)
# ======================================================================
@dataclass
class Scaling:
    """engineering value = raw * scale + offset"""
    scale: float
    offset: float = 0.0

    def apply(self, raw: int) -> float:
        return raw * self.scale + self.offset


def piecewise(x: float, points, extrapolate: bool = True) -> float:
    """
    Piecewise-linear interpolation through `points` [(x, y), ...] (x strictly
    increasing, at least 2 points). Outside the range it either continues the
    nearest segment's slope (extrapolate=True) or clamps to the end value.
    """
    if x <= points[0][0] or x >= points[-1][0]:
        if not extrapolate:
            return points[0][1] if x <= points[0][0] else points[-1][1]
        seg = (points[0], points[1]) if x <= points[0][0] else (points[-2], points[-1])
    else:
        seg = next((a, b) for a, b in zip(points, points[1:]) if a[0] <= x <= b[0])
    (x0, y0), (x1, y1) = seg
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def points_valid(points) -> bool:
    """True if x and y are both strictly increasing (so the mapping is invertible)."""
    return len(points) >= 2 and all(a[0] < b[0] and a[1] < b[1] for a, b in zip(points, points[1:]))


# !!! ASSUMED scalings - the frame layouts are known, the units are not. !!!
# Tune these (or edit them live in the display app's Calibration panel) by
# sending known raw values to the real cluster and comparing what it shows.
#   speed   : raw16 = (major << 8) | minor, assumed 1/128 km/h per count -> mph
#   rpm     : raw16 = (major << 8) | minor, assumed 1/4 rpm per count
#   fuel    : raw 0-255 -> 0-100 %
DEFAULT_SCALING = {
    "speed": Scaling(0.621371 / 128.0, 0.0),
    "rpm": Scaling(0.25, 0.0),
    "fuel": Scaling(100.0 / 255.0, 0.0),
}

# Coolant is NOT linear on the real cluster. Measured needle positions
# (raw byte -> degF), where the dial's middle ticks are:
#   raw  69 -> halfway between 100 and 195  (147.5)
#   raw 128 -> 195 (dial centre)
#   raw 201 -> halfway between 195 and 260  (227.5)
# Values outside this range are extrapolated along the nearest segment.
DEFAULT_COOLANT_POINTS = [(69, 147.5), (128, 195.0), (201, 227.5)]
COOLANT_DIAL_MIN_F = 100.0
COOLANT_DIAL_MAX_F = 260.0


def coolant_dial_ticks(points):
    """
    Dial tick marks for the coolant gauge as [(degF, fraction_of_sweep)].
    The three calibration points sit at 25 %, 50 % and 75 % of the sweep, with
    the dial ends at 100 and 260 degF - this matches the real cluster's face.
    """
    temps = [COOLANT_DIAL_MIN_F] + [p[1] for p in points] + [COOLANT_DIAL_MAX_F]
    fractions = [0.0, 0.25, 0.5, 0.75, 1.0]
    return list(zip(temps, fractions))


# key -> (header bytes that identify the frame, number of data bytes after it)
_SIGNATURES = (
    ("rpm", bytes([0x88, 0x1B, 0x10, 0x10]), 2),
    ("speed", bytes([0x88, 0x29, 0x10, 0x02]), 2),
    ("fuel", bytes([0x8A, 0xEA, 0x40, 0x02, 0x80]), 1),
    ("coolant", bytes([0x8A, 0xEA, 0x40, 0x02, 0x81]), 1),
    ("odo", bytes([0xC8, 0x7B, 0x40, 0x01]), 4),
)


def decode_frame(payload: bytes) -> Optional[tuple]:
    """
    Identify a received J1850 payload.

    Returns (key, raw) or None. `raw` is the unscaled integer: 16-bit for
    rpm/speed (major<<8 | minor), 8-bit for fuel/coolant, 32-bit for odo.
    Anything after the data bytes (the CRC, when "Trim CRC" is off) is ignored,
    so this works either way.
    """
    for key, header, n in _SIGNATURES:
        if payload.startswith(header) and len(payload) >= len(header) + n:
            raw = int.from_bytes(payload[len(header):len(header) + n], "big")
            return key, raw
    return None
