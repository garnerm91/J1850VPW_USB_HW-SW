"""
Instrument cluster display (Dear PyGui) driven by live J1850 frames.

Connect to the USB interface, enable RX mode, and the gauges follow the
tach / speedo / fuel / coolant / odometer frames seen on the bus (for example
from cluster_sim.py running on a second interface).

Threading: Dear PyGui is only touched from the main thread. The serial reader
thread just puts events on a queue; drain_events() applies them once per frame.
"""
from __future__ import annotations

import math
import queue

import dearpygui.dearpygui as dpg

import cluster as C
import protocol as P
from serial_manager import SerialManager, list_ports

GRAY = (150, 150, 150, 255)
ORANGE = (255, 165, 0, 255)

ODO_DIVISOR = C.ODO_DIVISOR

# (key, gauge label, units, minimum, maximum)
ROWS = (
    ("speed", "Speed", "MPH"),
    ("rpm", "RPM", "RPM"),
    ("fuel", "Fuel", "%"),
    ("coolant", "Coolant", "F"),
    ("odo", "Odometer", ""),
)


# ============================================================
# GAUGE DRAWING (unchanged from the original demo)
# ============================================================

def polar_to_xy(cx, cy, radius, angle):
    """Dear PyGui's Y axis points down, so the Y calculation is inverted."""
    return cx + radius * math.cos(angle), cy - radius * math.sin(angle)


def draw_gauge(drawlist, cx, cy, radius, value, minimum, maximum, label, units,
               start_angle, end_angle, major_ticks=8, ticks=None):
    """
    `ticks` is optional: [(value, fraction_of_sweep), ...] for a dial whose
    marks are not evenly spaced in value (the needle then follows the same
    table). Without it the dial is linear from `minimum` to `maximum`.
    """
    if ticks is None:
        ticks = [(minimum + (maximum - minimum) * i / major_ticks, i / major_ticks)
                 for i in range(major_ticks + 1)]

    # Background
    dpg.draw_circle((cx, cy), radius, color=(180, 180, 180, 255),
                    fill=(15, 15, 15, 255), thickness=3, parent=drawlist)
    dpg.draw_circle((cx, cy), radius - 10, color=(50, 50, 50, 255),
                    thickness=2, parent=drawlist)

    # Tick marks and numbers
    for tick_value, fraction in ticks:
        angle = start_angle + (end_angle - start_angle) * fraction
        outer = polar_to_xy(cx, cy, radius - 15, angle)
        inner = polar_to_xy(cx, cy, radius - 30, angle)
        dpg.draw_line(outer, inner, color=(220, 220, 220, 255), thickness=3, parent=drawlist)

        text = f"{tick_value:.0f}"
        tx, ty = polar_to_xy(cx, cy, radius - 48, angle)
        dpg.draw_text((tx - len(text) * 4, ty - 7), text,
                      color=(220, 220, 220, 255), size=14, parent=drawlist)

    # Needle
    fraction = C.piecewise(value, [(t, f) for t, f in ticks], extrapolate=False)
    needle_angle = start_angle + (end_angle - start_angle) * fraction
    needle_end = polar_to_xy(cx, cy, radius - 35, needle_angle)
    dpg.draw_line((cx, cy), needle_end, color=(230, 40, 40, 255), thickness=4, parent=drawlist)
    dpg.draw_circle((cx, cy), 8, color=(220, 220, 220, 255),
                    fill=(40, 40, 40, 255), parent=drawlist)

    # Digital value, units, label
    value_text = f"{value:.0f}"
    dpg.draw_text((cx - len(value_text) * 7, cy + radius * 0.35), value_text,
                  color=(240, 240, 240, 255), size=22, parent=drawlist)
    dpg.draw_text((cx - len(units) * 4, cy + radius * 0.35 + 27), units,
                  color=(160, 160, 160, 255), size=13, parent=drawlist)
    dpg.draw_text((cx - len(label) * 4, cy - radius * 0.55), label,
                  color=(20, 220, 220, 255), size=16, parent=drawlist)


def draw_odometer(drawlist, cx, cy, value):
    text = f"{value:06d}"
    w, h = 220, 46
    dpg.draw_rectangle((cx - w / 2, cy - h / 2), (cx + w / 2, cy + h / 2),
                       color=(180, 180, 180, 255), fill=(15, 15, 15, 255),
                       thickness=2, rounding=6, parent=drawlist)
    dpg.draw_text((cx - len(text) * 8, cy - 13), text,
                  color=(240, 240, 240, 255), size=26, parent=drawlist)
    dpg.draw_text((cx - w / 2 + 8, cy - 22), "ODO", color=(20, 220, 220, 255),
                  size=12, parent=drawlist)


class DisplayApp:
    def __init__(self):
        self.events: queue.Queue = queue.Queue()
        self.serial = SerialManager(
            on_frame=lambda f: self.events.put(("frame", f)),
            on_log=lambda m: self.events.put(("status", m)),
            on_disconnect=lambda: self.events.put(("disconnected",)),
        )
        # Engineering values shown on the gauges
        self.values = {"speed": 0.0, "rpm": 0.0, "fuel": 0.0, "coolant": 0.0, "odo": 0}
        self.raw = {k: None for k, *_ in ROWS}
        self.counts = {k: 0 for k, *_ in ROWS}
        self.scaling = {k: C.Scaling(s.scale, s.offset) for k, s in C.DEFAULT_SCALING.items()}
        self.coolant_points = list(C.DEFAULT_COOLANT_POINTS)     # [(raw, degF)]
        self.dirty = True

    # ==================================================================
    # Events (main thread)
    # ==================================================================
    def drain_events(self):
        for _ in range(500):
            try:
                ev = self.events.get_nowait()
            except queue.Empty:
                break
            kind = ev[0]
            if kind == "frame":
                self._on_frame(ev[1])
            elif kind == "status":
                dpg.set_value("status", ev[1])
            elif kind == "disconnected":
                dpg.set_value("status", "Device disconnected.")
                self._set_connected_ui(False)
        if self.dirty:
            self.draw_cluster()
            self.dirty = False

    def _on_frame(self, frame: P.Frame):
        if frame.kind == "IDENTIFY":
            dpg.set_value("status", f"Device identified: 0x{P.ID_J1850VPW:02X}")
        elif frame.kind == "NACK":
            dpg.set_value("status", "NACK from interface")
        elif frame.kind == "RX":
            decoded = C.decode_frame(frame.data)
            if decoded:
                key, raw = decoded
                self.raw[key] = raw
                self.counts[key] += 1
                self._update_value(key)

    def _update_value(self, key):
        raw = self.raw[key]
        if raw is None:
            return
        if key == "odo":
            self.values["odo"] = raw // ODO_DIVISOR
            val_text = str(self.values["odo"])
            raw_text = f"{raw} (0x{raw:08X})"
        elif key == "coolant":
            self.values[key] = C.piecewise(raw, self.coolant_points)
            val_text = f"{self.values[key]:.1f}"
            raw_text = f"{raw} (0x{raw:02X})"
        else:
            self.values[key] = self.scaling[key].apply(raw)
            val_text = f"{self.values[key]:.1f}"
            width = 4 if key in ("speed", "rpm") else 2
            raw_text = f"{raw} (0x{raw:0{width}X})"
        dpg.set_value(f"raw_{key}", raw_text)
        dpg.set_value(f"cnt_{key}", str(self.counts[key]))
        dpg.set_value(f"val_{key}", val_text)
        self.dirty = True

    def _on_coolant_point(self, *_):
        points = [(dpg.get_value(f"cool_raw_{i}"), dpg.get_value(f"cool_f_{i}"))
                  for i in range(len(self.coolant_points))]
        ok = C.points_valid(points) and all(
            C.COOLANT_DIAL_MIN_F < t < C.COOLANT_DIAL_MAX_F for _, t in points)
        dpg.configure_item("cool_warn", show=not ok)
        if ok:                       # ignore half-typed / non-monotonic edits
            self.coolant_points = points
            self._update_value("coolant")
            self.dirty = True

    def _on_scaling(self, sender, value, user_data):
        key, field = user_data
        setattr(self.scaling[key], field, float(value))
        self._update_value(key)

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
            self.serial.disconnect()
            self._set_connected_ui(False)
            return
        port = dpg.get_value("port_combo")
        if not port:
            dpg.set_value("status", "Please select a port.")
            return
        if self.serial.connect(port):
            self._set_connected_ui(True)
            self.serial.send_frame(P.build_identify_frame(), log=False)
            if dpg.get_value("rx_mode"):
                self.serial.send_frame(P.build_rx_mode_frame(True), log=False)

    def _on_rx_mode(self, sender, enabled):
        if self.serial.is_connected:
            self.serial.send_frame(P.build_rx_mode_frame(enabled), log=False)
            dpg.set_value("status", f"RX mode {'enabled' if enabled else 'disabled'}.")

    # ==================================================================
    # Drawing
    # ==================================================================
    def draw_cluster(self):
        v = self.values
        dpg.delete_item("cluster", children_only=True)
        start, end = math.radians(225), math.radians(-45)
        draw_gauge("cluster", 230, 220, 180, v["speed"], 0, 160, "SPEED", "MPH", start, end, 8)
        draw_gauge("cluster", 670, 220, 180, v["rpm"], 0, 8000, "RPM", "RPM", start, end, 8)
        draw_gauge("cluster", 230, 600, 150, v["fuel"], 0, 100, "FUEL", "%", start, end, 10)
        draw_gauge("cluster", 670, 600, 150, v["coolant"], 100, 260, "COOLANT", "\u00b0F", start, end,
                   ticks=C.coolant_dial_ticks(self.coolant_points))
        draw_odometer("cluster", 450, 785, v["odo"])

    # ==================================================================
    # UI
    # ==================================================================
    def build_ui(self):
        with dpg.window(tag="main"):
            with dpg.group(horizontal=True):
                dpg.add_text("Port:")
                dpg.add_combo([], tag="port_combo", width=200)
                dpg.add_button(label="Refresh", tag="refresh_btn", callback=self._refresh_ports)
                dpg.add_button(label="Connect", tag="connect_btn", width=90, callback=self._on_connect)
                dpg.add_checkbox(label="RX Mode", tag="rx_mode", default_value=True,
                                 callback=self._on_rx_mode)
            dpg.add_text("Not connected.", tag="status", color=GRAY)

            with dpg.collapsing_header(label="Calibration / raw values", default_open=False):
                dpg.add_text("Scalings are ASSUMPTIONS: value = raw * scale + offset. "
                             "Edit live to match the real cluster.", color=ORANGE)
                with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit,
                               borders_innerH=True):
                    for h in ("Gauge", "Raw", "Frames", "Scale", "Offset", "Value"):
                        dpg.add_table_column(label=h)
                    for key, name, _units in ROWS:
                        with dpg.table_row():
                            dpg.add_text(name)
                            dpg.add_text("-", tag=f"raw_{key}")
                            dpg.add_text("0", tag=f"cnt_{key}")
                            if key == "odo":
                                dpg.add_text(f"raw // {ODO_DIVISOR}")
                                dpg.add_text("")
                            elif key == "coolant":
                                dpg.add_text("piecewise (below)")
                                dpg.add_text("")
                            else:
                                s = self.scaling[key]
                                dpg.add_input_float(default_value=s.scale, width=120, step=0,
                                                    step_fast=0, format="%.6f",
                                                    callback=self._on_scaling,
                                                    user_data=(key, "scale"))
                                dpg.add_input_float(default_value=s.offset, width=100, step=0,
                                                    step_fast=0, format="%.3f",
                                                    callback=self._on_scaling,
                                                    user_data=(key, "offset"))
                            dpg.add_text("-", tag=f"val_{key}")

                dpg.add_spacer(height=4)
                dpg.add_text("Coolant points (raw byte -> degF). They sit at 25 / 50 / 75 % of "
                             "the dial; values between points are interpolated.")
                for i, (raw, temp) in enumerate(self.coolant_points):
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"Point {i + 1}:")
                        dpg.add_input_int(tag=f"cool_raw_{i}", default_value=raw, width=90,
                                          step=0, step_fast=0, min_value=0, max_value=255,
                                          min_clamped=True, max_clamped=True,
                                          callback=self._on_coolant_point)
                        dpg.add_text("->")
                        dpg.add_input_float(tag=f"cool_f_{i}", default_value=temp, width=90,
                                            step=0, step_fast=0, format="%.1f",
                                            callback=self._on_coolant_point)
                dpg.add_text("Points must increase in both raw and degF, and stay between 100 and 260 "
                             "degF - edit ignored until valid.", tag="cool_warn",
                             color=ORANGE, show=False)

            dpg.add_separator()
            dpg.add_drawlist(width=900, height=830, tag="cluster")

    def run(self):
        dpg.create_context()
        self.build_ui()
        self._refresh_ports()
        dpg.create_viewport(title="Instrument Cluster Display", width=940, height=1000)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        self.draw_cluster()
        try:
            while dpg.is_dearpygui_running():
                self.drain_events()
                dpg.render_dearpygui_frame()
        finally:
            self.serial.disconnect()
            dpg.destroy_context()


if __name__ == "__main__":
    DisplayApp().run()
