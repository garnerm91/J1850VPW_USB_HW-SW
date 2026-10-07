"""
protocol.py - STX/ETX framing for the J1850VPW USB bridge.

Pure Python, no GUI or serial imports, so it is easy to unit-test.
Port of ProtocolHelper.cs plus the parser half of SerialManager.cs.

Host -> STM32 frame:  [ STX | LEN | CMD | data... | ETX ]
    LEN = 1 (CMD) + len(data)
STM32 -> host:
    ACK / NACK:   [ STX | 0x01 | 0x06 or 0x15 | ETX ]
    Identify:     [ STX | 0x02 | 0x06 | 0x4A  | ETX ]
    J1850 RX:     [ STX | LEN  | 0x10 | payload... (incl. CRC) | ETX ]
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from typing import Callable, Optional

# ---- Constants (must match firmware protocol.h) -------------------------
STX = 0x02
ETX = 0x03
ACK = 0x06
NACK = 0x15

CMD_RX_MODE = 0x01
CMD_SEND = 0x02
CMD_IDENTIFY = 0x49        # what the original app actually sends on connect
ID_J1850VPW = 0x4A         # 'J' - device ID byte returned after the ACK
RX_HEADER = 0x10           # first body byte of a forwarded J1850 frame

MAX_J1850_PAYLOAD = 11     # bytes, CRC is added by the firmware

# ---- Canned commands ----------------------------------------------------
CMD_MUTE = "6C FE F0 28 00 F0"
CMD_MAGIC = "99 01 43 41 4C 31"
CMD_SAVE_RAM = "99 99 43 41 4C 31"


# ---- Frame building -----------------------------------------------------
def build_frame(cmd: int, data: bytes = b"") -> bytes:
    data = bytes(data or b"")
    return bytes([STX, len(data) + 1, cmd]) + data + bytes([ETX])


def build_rx_mode_frame(enable: bool) -> bytes:
    return build_frame(CMD_RX_MODE, bytes([1 if enable else 0]))


def build_send_frame(j1850_data: bytes) -> bytes:
    """The firmware appends the CRC itself - do not include it."""
    return build_frame(CMD_SEND, j1850_data)


def build_identify_frame() -> bytes:
    return build_frame(CMD_IDENTIFY)


# ---- Hex helpers --------------------------------------------------------
def to_hex(data: bytes, start: int = 0) -> str:
    return " ".join(f"{b:02X}" for b in data[start:])


def parse_hex(text: Optional[str]) -> Optional[bytes]:
    """'68 6A F1', '686AF1', '0x68,0x6A' -> bytes. None if invalid."""
    if not text or not text.strip():
        return None
    cleaned = re.sub(r"0[xX]", "", text)
    cleaned = re.sub(r"[\s,]", "", cleaned)
    if len(cleaned) % 2 != 0 or not re.fullmatch(r"[0-9A-Fa-f]*", cleaned):
        return None
    return bytes.fromhex(cleaned) or None


# ---- Receive parser -----------------------------------------------------
@dataclass
class Frame:
    kind: str          # "ACK" | "NACK" | "IDENTIFY" | "RX"
    data: bytes


class FrameParser:
    """
    Incremental STX/LEN/body/ETX parser. Feed it whatever chunks the serial
    port returns; it yields complete Frames.

    Unlike the C# version this is purely LEN-driven, so the identify reply
    (ACK + 0x4A, LEN=2) is decoded correctly.
    """

    _WAIT_STX, _WAIT_LEN, _WAIT_BODY, _WAIT_ETX = range(4)

    def __init__(self, log: Optional[Callable[[str], None]] = None):
        self.trim_crc = False
        self._log = log or (lambda msg: None)
        self._reset()

    def _reset(self):
        self._state = self._WAIT_STX
        self._len = 0
        self._body = bytearray()

    def feed(self, chunk: bytes) -> list[Frame]:
        out: list[Frame] = []
        for b in chunk:
            if self._state == self._WAIT_STX:
                if b == STX:
                    self._state = self._WAIT_LEN

            elif self._state == self._WAIT_LEN:
                if b == 0:
                    self._log("Frame with LEN=0 dropped.")
                    self._reset()
                else:
                    self._len = b
                    self._body = bytearray()
                    self._state = self._WAIT_BODY

            elif self._state == self._WAIT_BODY:
                self._body.append(b)
                if len(self._body) >= self._len:
                    self._state = self._WAIT_ETX

            elif self._state == self._WAIT_ETX:
                if b == ETX:
                    frame = self._dispatch(bytes(self._body))
                    if frame:
                        out.append(frame)
                    self._reset()
                else:
                    self._log(f"Bad ETX: 0x{b:02X} - frame dropped.")
                    # If the stray byte is a new STX, resync on it immediately
                    self._reset()
                    if b == STX:
                        self._state = self._WAIT_LEN
        return out

    def _dispatch(self, body: bytes) -> Optional[Frame]:
        cmd = body[0]
        if cmd in (ACK, NACK):
            kind = "ACK" if cmd == ACK else "NACK"
            if cmd == ACK and len(body) > 1 and body[1] == ID_J1850VPW:
                kind = "IDENTIFY"
            return Frame(kind, body)

        if cmd == RX_HEADER:
            payload = body[1:]
            if self.trim_crc:
                if len(payload) <= 1:
                    self._log("RX frame too short after CRC strip - ignored.")
                    return None
                payload = payload[:-1]
            return Frame("RX", payload)

        self._log(f"Unknown CMD byte: 0x{cmd:02X} - frame dropped.")
        return None


# ---- Swap-box data points ----------------------------------------------
@dataclass(frozen=True)
class DataPoint:
    id: int
    name: str
    kind: str              # "float" or "uint32"
    writable: bool = True


SWAP_DATAPOINTS = (
    DataPoint(0x02, "Battery Cal", "float"),
    DataPoint(0x03, "Oil Cal", "float"),
    DataPoint(0x05, "Alpha", "float"),
    DataPoint(0x04, "Options", "uint32"),
    DataPoint(0x06, "SN", "uint32"),
    DataPoint(0x07, "FW VER", "uint32", writable=False),
)
DATAPOINTS_BY_ID = {dp.id: dp for dp in SWAP_DATAPOINTS}

# Option-bit labels (bit 0 first)
OPTION_BITS = ("99 Airbag", "Driver 1", "reserved", "reserved",
               "reserved", "reserved", "reserved", "reserved")


def build_read_query(dp_id: int) -> bytes:
    return bytes([0x98, dp_id])


def encode_value(dp: DataPoint, text: str) -> bytes:
    """Text -> 4 little-endian bytes. Raises ValueError with a UI-ready message."""
    text = text.strip()
    if dp.kind == "float":
        try:
            return struct.pack("<f", float(text))
        except (ValueError, OverflowError):
            raise ValueError(f"Invalid float for {dp.name}.")
    try:
        v = int(text)
    except ValueError:
        v = -1
    if not 0 <= v <= 0xFFFFFFFF:
        raise ValueError(f"Invalid value for {dp.name} - must be a whole number (0 to 4294967295).")
    return struct.pack("<I", v)


def build_write(dp: DataPoint, value_bytes: bytes) -> bytes:
    return bytes([0x99, dp.id]) + value_bytes


def decode_value(dp: DataPoint, raw4: bytes) -> str:
    if dp.kind == "float":
        return f"{struct.unpack('<f', raw4)[0]:.4f}"
    return str(struct.unpack("<I", raw4)[0])


# ---- Playback file ------------------------------------------------------
@dataclass
class PlaybackFrame:
    data: bytes
    delay_ms: int          # delay AFTER sending this frame


@dataclass
class PlaybackFile:
    frames: list
    skipped: int
    notes: list            # [(level, message)] level: "dim" | "warn"


def parse_playback(lines, default_delay_ms: int = 500) -> PlaybackFile:
    """
    One frame per line as hex. '#' or '//' = comment.
    '*500' sets the delay (ms) used after every following frame.
    """
    frames, notes, skipped = [], [], 0
    delay = default_delay_ms
    for num, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if line.startswith("*"):
            try:
                ms = int(line[1:].strip())
                if ms < 0:
                    raise ValueError
                delay = ms
                notes.append(("dim", f"Playback: line {num} - delay set to {ms} ms"))
            except ValueError:
                notes.append(("warn", f'Playback: line {num} invalid delay directive "{line}" - ignored.'))
            continue

        data = parse_hex(line)
        if not data:
            notes.append(("warn", f'Playback: line {num} skipped (bad hex): "{line}"'))
            skipped += 1
            continue
        if len(data) > MAX_J1850_PAYLOAD:
            notes.append(("warn", f'Playback: line {num} skipped (>{MAX_J1850_PAYLOAD} bytes): "{line}"'))
            skipped += 1
            continue
        frames.append(PlaybackFrame(data, delay))
    return PlaybackFile(frames, skipped, notes)
