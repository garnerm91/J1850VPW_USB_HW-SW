"""
serial_manager.py - cross-platform serial transport (pyserial).

Port of the connection/thread half of SerialManager.cs. A background thread
reads bytes, feeds them to protocol.FrameParser and calls on_frame(Frame).

All callbacks run on the reader thread. Do NOT touch Dear PyGui from them;
push onto a queue and drain it in the render loop (see main.py).
"""
from __future__ import annotations

import sys
import threading
from typing import Callable, Optional

import serial
import serial.tools.list_ports

import protocol as P


def list_ports() -> list[str]:
    """COM3 on Windows, /dev/ttyACM0 etc. on Linux, /dev/cu.usbmodem* on macOS."""
    return sorted(p.device for p in serial.tools.list_ports.comports())


class SerialManager:
    def __init__(
        self,
        on_frame: Callable[[P.Frame], None],
        on_log: Optional[Callable[[str], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
    ):
        self._on_frame = on_frame
        self._on_log = on_log or (lambda msg: None)
        self._on_disconnect = on_disconnect or (lambda: None)

        self.parser = P.FrameParser(log=self._log)
        self._port: Optional[serial.SerialBase] = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._write_lock = threading.Lock()

    # ---- properties ------------------------------------------------------
    @property
    def is_connected(self) -> bool:
        port = self._port
        return port is not None and port.is_open

    @property
    def trim_crc(self) -> bool:
        return self.parser.trim_crc

    @trim_crc.setter
    def trim_crc(self, value: bool):
        self.parser.trim_crc = bool(value)

    # ---- connect / disconnect -------------------------------------------
    def connect(self, port_name: str, baud: int = 115200) -> bool:
        if self.is_connected:
            self.disconnect()
        try:
            # serial_for_url accepts real device names and pyserial URLs
            # (e.g. "loop://"), which is handy for testing without hardware.
            port = serial.serial_for_url(
                port_name, baudrate=baud, bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                timeout=0.1, write_timeout=0.5,
            )
        except (serial.SerialException, OSError, ValueError) as ex:
            self._log(f"Connect failed: {ex}")
            if sys.platform.startswith("linux") and "ermission" in str(ex):
                self._log("Linux: add your user to the 'dialout' group "
                          "(sudo usermod -aG dialout $USER), then log out and back in.")
            return False

        self.parser._reset()
        self._port = port
        self._running.set()
        self._thread = threading.Thread(target=self._rx_loop, args=(port,),
                                        name="J1850-RX", daemon=True)
        self._thread.start()
        self._log(f"Connected to {port_name} at {baud} baud.")
        return True

    def disconnect(self):
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(1.0)
        port, self._port, self._thread = self._port, None, None
        if port is not None:
            try:
                port.close()
            except Exception:
                pass
        self.parser._reset()
        self._log("Disconnected.")

    # ---- transmit --------------------------------------------------------
    def send_frame(self, frame: bytes, log: bool = True) -> bool:
        with self._write_lock:
            port = self._port
            if port is None or not port.is_open:
                self._log("Not connected.")
                return False
            try:
                port.write(frame)
            except (serial.SerialException, OSError) as ex:
                self._log(f"Send failed: {ex}")
                return False
        if log:
            self._log(f"TX: {P.to_hex(frame)}")
        return True

    # ---- reader thread ---------------------------------------------------
    def _rx_loop(self, port):
        while self._running.is_set():
            try:
                data = port.read(port.in_waiting or 1)   # returns b"" on timeout
            except (serial.SerialException, OSError, TypeError) as ex:
                # Device unplugged, or closed underneath us
                if self._running.is_set():
                    self._running.clear()
                    self._log(f"RX error: {ex}")
                    try:
                        port.close()
                    except Exception:
                        pass
                    self._port = None
                    self._on_disconnect()
                return
            if data:
                for frame in self.parser.feed(data):
                    self._on_frame(frame)

    def _log(self, msg: str):
        self._on_log(msg)
