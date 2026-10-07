"""
Cavalier cluster data simulator (Dear PyGui).

Sliders set the tach / speedo / fuel / odometer values. With "Send on timer"
ticked, a background thread keeps re-sending the frames, because the cluster
resets its gauges if it goes ~1 s without seeing them.

Threading: Dear PyGui is only touched from the main thread. The serial reader
and the TX thread post events to `self.events`; drain_events() applies them.
Slider callbacks (main thread) write to `self.vals` under a lock and the TX
thread reads a snapshot, so slider changes go out on the next cycle.
"""
from __future__ import annotations

import queue
import threading
import time
from collections import deque
from datetime import datetime

import dearpygui.dearpygui as dpg

import cluster as C
import protocol as P
from serial_manager import SerialManager, list_ports

# ---- Colours ------------------------------------------------------------
GRAY = (150, 150, 150, 255)
ORANGE = (255, 165, 0, 255)
GREEN = (144, 238, 144, 255)
RED = (255, 90, 40, 255)
BLUE = (100, 149, 237, 255)
CYAN = (0, 230, 230, 255)
LIME = (50, 205, 50, 255)

MAX_LOG_LINES = 1500
FRAME_GAP_S = 0.010          # pause between back-to-back frames (bus time + firmware ACK)
DEFAULT_PERIOD_MS = 250      # well under the cluster's ~1 s timeout

# gauge name -> list of (value key, label, default)
GAUGES = {
    "tach": ("Tachometer", [("tach_maj", "Major (XX)"), ("tach_min", "Minor (YY)")]),
    "speedo": ("Speedometer", [("spd_maj", "Major (XX)"), ("spd_min", "Minor (YY)")]),
    "fuel": ("Fuel level", [("fuel", "Level (XX)")]),
    "cool": ("Coolant temperature", [("cool", "Temperature (XX)")]),
    "odo": ("Odometer", [("odo", "Value (raw // 103)")]),
}
ORDER = ("tach", "speedo", "fuel", "cool", "odo")


class SimApp:
    def __init__(self):
        self.events: queue.Queue = queue.Queue()
        self.serial = SerialManager(
            on_frame=lambda f: self.events.put(("frame", f)),
            on_log=lambda m: self.log(m, GRAY),
            on_disconnect=lambda: self.events.put(("disconnected",)),
        )
        self._lock = threading.Lock()
        self.vals = {"tach_maj": 0, "tach_min": 0, "spd_maj": 0, "spd_min": 0,
                     "fuel": 0, "cool": 0, "odo": 0}
        self.enabled = {g: True for g in ORDER}
        self.period_ms = DEFAULT_PERIOD_MS
        # Keep-alive: placeholder until the real frame is known
        self.ka_frame = None
        self.ka_on = False
        self.ka_period_ms = 500

        self._tx_stop = threading.Event()
        self._tx_thread = None
        self._log_items: deque = deque()
        self._acks = 0
        self._nacks = 0

    # ==================================================================
    # Logging
    # ==================================================================
    def log(self, msg: str, color=GRAY):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.events.put(("log", f"[{ts}] {msg}", color))

    def _add_log_line(self, text, color):
        item = dpg.add_text(text, parent="log_win", color=color, wrap=0)
        self._log_items.append(item)
        while len(self._log_items) > MAX_LOG_LINES:
            dpg.delete_item(self._log_items.popleft())
        if dpg.get_value("autoscroll"):
            dpg.set_y_scroll("log_win", -1.0)

    def _clear_log(self, *_):
        dpg.delete_item("log_win", children_only=True)
        self._log_items.clear()

    # ==================================================================
    # Event pump
    # ==================================================================
    def drain_events(self):
        for _ in range(500):
            try:
                ev = self.events.get_nowait()
            except queue.Empty:
                return
            kind = ev[0]
            if kind == "log":
                self._add_log_line(ev[1], ev[2])
            elif kind == "frame":
                self._on_frame(ev[1])
            elif kind == "cycle":
                dpg.set_value("tx_status", f"Sending: cycle {ev[1]}")
            elif kind == "tx_stopped":
                dpg.set_value("tx_on", False)
                dpg.set_value("tx_status", "Stopped")
            elif kind == "disconnected":
                self.log("Device disconnected.", ORANGE)
                self._set_connected_ui(False)
                self._stop_tx()

    # ==================================================================
    # Connection
    # ==================================================================
    def _refresh_ports(self, *_):
        ports = list_ports()
        current = dpg.get_value("port_combo")
        dpg.configure_item("port_combo", items=ports)
        dpg.set_value("port_combo", current if current in ports else (ports[0] if ports else ""))

    def _set_connected_ui(self, connected: bool):
        dpg.set_item_label("connect_btn", "Disconnect" if connected else "Connect")
        dpg.configure_item("port_combo", enabled=not connected)
        dpg.configure_item("refresh_btn", enabled=not connected)

    def _on_connect(self, *_):
        if self.serial.is_connected:
            self._stop_tx()
            self.serial.disconnect()
            self._set_connected_ui(False)
            return
        port = dpg.get_value("port_combo")
        if not port:
            self.log("Please select a port.", ORANGE)
            return
        if self.serial.connect(port):
            self._set_connected_ui(True)
            self.serial.send_frame(P.build_identify_frame())

    def _on_rx_mode(self, sender, enabled):
        self.serial.send_frame(P.build_rx_mode_frame(enabled))
        self.log(f"RX mode {'ENABLED' if enabled else 'DISABLED'} sent.", BLUE)

    def _on_trim_crc(self, sender, enabled):
        self.serial.trim_crc = enabled

    def _on_frame(self, frame: P.Frame):
        if frame.kind == "ACK":
            self._acks += 1
            if not self._tx_running():          # avoid flooding the log while sending
                self.log(" ACK", LIME)
        elif frame.kind == "NACK":
            self._nacks += 1
            self.log(" NACK", RED)
        elif frame.kind == "IDENTIFY":
            self.log(f" Device identified: 0x{P.ID_J1850VPW:02X}", LIME)
        elif frame.kind == "RX":
            self.log(f" RX: {P.to_hex(frame.data)}", CYAN)
        dpg.set_value("ack_status", f"ACK {self._acks}   NACK {self._nacks}")

    # ==================================================================
    # Values -> frames
    # ==================================================================
    def _snapshot_frames(self, only_enabled=True):
        with self._lock:
            v = dict(self.vals)
            en = dict(self.enabled)
        frames = {
            "tach": C.tach_frame(v["tach_maj"], v["tach_min"]),
            "speedo": C.speedo_frame(v["spd_maj"], v["spd_min"]),
            "fuel": C.fuel_frame(v["fuel"]),
            "cool": C.coolant_frame(v["cool"]),
            "odo": C.odo_frame(v["odo"]),
        }
        return [(g, frames[g]) for g in ORDER if en[g] or not only_enabled]

    def _refresh_previews(self):
        for g, frame in self._snapshot_frames(only_enabled=False):
            dpg.set_value(f"pv_{g}", P.to_hex(frame))

    def _on_slider(self, sender, value, key):
        if key == "odo":
            value = max(0, min(C.ODO_MAX, value))
            dpg.set_value("odo", value)
        with self._lock:
            self.vals[key] = int(value)
        self._refresh_previews()

    def _on_gauge_enable(self, sender, on, gauge):
        with self._lock:
            self.enabled[gauge] = bool(on)

    def _on_period(self, sender, value):
        with self._lock:
            self.period_ms = int(value)
        dpg.configure_item("period_warn", show=value >= 900)

    # ---- keep-alive (placeholder) -------------------------------------
    def _on_ka_hex(self, sender, text):
        frame = P.parse_hex(text)
        if frame is not None and len(frame) > P.MAX_J1850_PAYLOAD:
            frame = None
        with self._lock:
            self.ka_frame = frame
        dpg.set_value("ka_status", f"{len(frame)} bytes" if frame else "(not set / invalid)")

    def _on_ka_toggle(self, sender, on):
        with self._lock:
            if on and self.ka_frame is None:
                self.log("Enter a valid keep-alive frame first.", ORANGE)
                dpg.set_value("ka_on", False)
                return
            self.ka_on = bool(on)

    def _on_ka_period(self, sender, value):
        with self._lock:
            self.ka_period_ms = int(value)

    # ==================================================================
    # Transmit
    # ==================================================================
    def _tx_running(self) -> bool:
        return self._tx_thread is not None and self._tx_thread.is_alive() \
            and not self._tx_stop.is_set()

    def _on_tx_toggle(self, sender, on):
        if on:
            if not self.serial.is_connected:
                self.log("Not connected - cannot start sending.", ORANGE)
                dpg.set_value("tx_on", False)
                return
            self._tx_stop = threading.Event()
            self._tx_thread = threading.Thread(target=self._tx_loop, args=(self._tx_stop,),
                                               name="cluster-tx", daemon=True)
            self._tx_thread.start()
            self.log(f"Timer started ({self.period_ms} ms).", BLUE)
        else:
            self._stop_tx()

    def _stop_tx(self):
        if self._tx_thread is not None:
            self._tx_stop.set()
            self.log("Timer stopped.", BLUE)
        self._tx_thread = None
        dpg.set_value("tx_on", False)
        dpg.set_value("tx_status", "Stopped")

    def _send(self, payload: bytes) -> bool:
        return self.serial.send_frame(P.build_send_frame(payload), log=False)

    def _tx_loop(self, stop: threading.Event):
        cycle = 0
        next_ka = time.monotonic()

        def keepalive_if_due() -> bool:
            nonlocal next_ka
            with self._lock:
                frame, on, period = self.ka_frame, self.ka_on, self.ka_period_ms
            now = time.monotonic()
            if on and frame and now >= next_ka:
                next_ka = now + period / 1000.0
                return self._send(frame)
            return True

        while not stop.is_set():
            t0 = time.monotonic()
            for _, frame in self._snapshot_frames():
                if not (self._send(frame) and keepalive_if_due()):
                    self.log("Timer stopped: send failed.", ORANGE)
                    self.events.put(("tx_stopped",))
                    return
                if stop.wait(FRAME_GAP_S):
                    return
            cycle += 1
            self.events.put(("cycle", cycle))
            with self._lock:
                period = self.period_ms / 1000.0
            if stop.wait(max(0.0, period - (time.monotonic() - t0))):
                return

    def _on_send_once(self, *_):
        if not self.serial.is_connected:
            self.log("Not connected.", ORANGE)
            return

        def run():
            for g, frame in self._snapshot_frames():
                if not self._send(frame):
                    return
                self.log(f"-> {g}: {P.to_hex(frame)}", GREEN)
                time.sleep(FRAME_GAP_S)
        threading.Thread(target=run, name="send-once", daemon=True).start()

    # ==================================================================
    # UI
    # ==================================================================
    def build_ui(self):
        with dpg.window(tag="main"):
            # ---- connection
            with dpg.group(horizontal=True):
                dpg.add_text("Port:")
                dpg.add_combo([], tag="port_combo", width=200)
                dpg.add_button(label="Refresh", tag="refresh_btn", callback=self._refresh_ports)
                dpg.add_button(label="Connect", tag="connect_btn", width=90, callback=self._on_connect)
                dpg.add_checkbox(label="RX Mode", callback=self._on_rx_mode)
                dpg.add_checkbox(label="Trim CRC", callback=self._on_trim_crc)

            dpg.add_spacer(height=6)

            # ---- timer controls
            with dpg.child_window(height=92, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="Send on timer", tag="tx_on", callback=self._on_tx_toggle)
                    dpg.add_button(label="Send once", callback=self._on_send_once)
                    dpg.add_text("Stopped", tag="tx_status", color=GRAY)
                    dpg.add_text("", tag="ack_status", color=GRAY)
                dpg.add_slider_int(label="Interval (ms)", tag="period", width=360,
                                   default_value=DEFAULT_PERIOD_MS, min_value=20, max_value=900,
                                   clamped=True, callback=self._on_period)
                dpg.add_text("Cluster resets gauges if frames stop for ~1 s - keep the interval well below that.",
                             tag="period_warn", color=ORANGE, show=False)
                dpg.add_text("Ctrl+click any slider to type an exact value.", color=GRAY)

            dpg.add_spacer(height=6)

            # ---- gauges
            for g in ORDER:
                title, sliders = GAUGES[g]
                with dpg.child_window(height=40 + 28 * len(sliders), border=True):
                    with dpg.group(horizontal=True):
                        dpg.add_text(title)
                        dpg.add_checkbox(label="send", default_value=True,
                                         callback=self._on_gauge_enable, user_data=g)
                        dpg.add_text("frame:", color=GRAY)
                        dpg.add_text("", tag=f"pv_{g}", color=CYAN)
                    for key, label in sliders:
                        if key == "odo":
                            dpg.add_slider_int(label=label, tag=key, width=420, default_value=0,
                                               min_value=0, max_value=999_999, clamped=False,
                                               callback=self._on_slider, user_data=key)
                        else:
                            dpg.add_slider_int(label=label, tag=key, width=420, default_value=0,
                                               min_value=0, max_value=255, clamped=True,
                                               callback=self._on_slider, user_data=key)

            dpg.add_spacer(height=6)

            # ---- keep-alive placeholder
            with dpg.child_window(height=92, border=True):
                dpg.add_text("Keep-alive frame (fill in once known)")
                with dpg.group(horizontal=True):
                    dpg.add_input_text(tag="ka_hex", width=360, hint="J1850 bytes in hex, no CRC",
                                       callback=self._on_ka_hex)
                    dpg.add_text("(not set / invalid)", tag="ka_status", color=GRAY)
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="Send keep-alive", tag="ka_on", callback=self._on_ka_toggle)
                    dpg.add_slider_int(label="every (ms)", width=240, default_value=500,
                                       min_value=20, max_value=900, clamped=True,
                                       callback=self._on_ka_period)

            dpg.add_spacer(height=6)

            # ---- log
            with dpg.group(horizontal=True):
                dpg.add_text("Log:")
                dpg.add_button(label="Clear", callback=self._clear_log)
                dpg.add_checkbox(label="Autoscroll", tag="autoscroll", default_value=True)
            dpg.add_child_window(tag="log_win", height=-1, border=True)

    def run(self):
        dpg.create_context()
        self.build_ui()
        self._refresh_ports()
        self._refresh_previews()
        dpg.create_viewport(title="Cluster Simulator - J1850VPW", width=700, height=950)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        try:
            while dpg.is_dearpygui_running():
                self.drain_events()
                dpg.render_dearpygui_frame()
        finally:
            self._tx_stop.set()
            self.serial.disconnect()
            dpg.destroy_context()


if __name__ == "__main__":
    SimApp().run()
