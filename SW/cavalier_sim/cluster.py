"""
cluster.py - J1850 frames for a Cavalier instrument cluster.

These are the 6-byte J1850 payloads (header + data). The STM32 firmware adds
the CRC, so protocol.build_send_frame() wraps them for the USB link.

    Tach      88 1B 10 10 XX YY       XX = major, YY = minor
    Speedo    88 29 10 02 XX YY       XX = major, YY = minor
    Fuel      8A EA 40 02 80 XX       XX = level 00-FF
    coolant 8A EA 40 02 81 XX XX=00-FF
    Odometer  C8 7B 40 01 AA BB CC DD raw = big-endian 32-bit, miles = raw // 103
"""
from __future__ import annotations

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
    return bytes([0x8A, 0xEA, 0x40, 0x02, 0x81, _byte(level, "Coolant temperature")])

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
