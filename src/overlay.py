"""GTK overlay window and UI refresh logic."""

from __future__ import annotations

import time
import threading
from typing import Optional

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, GLib, Gtk4LayerShell as LayerShell

from .config import CONFIG
from . import ui
from . import flash
from . import data


class QuotaOverlay(Gtk.Window):
    def __init__(self, app):
        super().__init__(application=app)

        self.click_through = CONFIG["behavior"]["click_through"]
        self.selected_creds = {}  # provider_name -> cred_id
        self.interactive_widgets = []
        self._flash_state = flash.FlashState(last_statuses={}, flash_until={})

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        LayerShell.set_namespace(self, "quota-monitor")
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)
        self._setup_position()

        self.set_decorated(False)
        width = CONFIG["appearance"]["width"]
        self.set_size_request(width, -1)

        ui.load_css()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.add_css_class("overlay-main")
        self.set_child(self.main_box)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.content_box.add_css_class("overlay-content")
        self.main_box.append(self.content_box)

        self.connect("realize", self.on_realize)

        self.refresh_data()
        GLib.timeout_add(CONFIG["server"]["refresh_interval_ms"], self.refresh_data)

    def _setup_position(self):
        pos = CONFIG["position"]
        anchor = pos["anchor"]

        for edge in [
            LayerShell.Edge.TOP,
            LayerShell.Edge.BOTTOM,
            LayerShell.Edge.LEFT,
            LayerShell.Edge.RIGHT,
        ]:
            LayerShell.set_anchor(self, edge, False)

        if "top" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.TOP, True)
            LayerShell.set_margin(self, LayerShell.Edge.TOP, pos["margin_top"])
        if "bottom" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
            LayerShell.set_margin(self, LayerShell.Edge.BOTTOM, pos["margin_bottom"])
        if "left" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
            LayerShell.set_margin(self, LayerShell.Edge.LEFT, pos["margin_left"])
        if "right" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.RIGHT, True)
            LayerShell.set_margin(self, LayerShell.Edge.RIGHT, pos["margin_right"])

    def on_realize(self, widget):
        if self.click_through:
            self.set_input_passthrough(True)

    def set_input_passthrough(self, passthrough: bool):
        self.click_through = passthrough
        self.update_input_region()

    def update_input_region(self):
        native = self.get_native()
        if not native:
            return
        surface = native.get_surface()
        if not surface:
            return

        if not self.click_through:
            surface.set_input_region(None)
            return

        region = cairo.Region()

        for widget in self.interactive_widgets:
            success, rect = widget.compute_bounds(self)
            if success:
                region.union(
                    cairo.Region(
                        cairo.RectangleInt(
                            int(rect.origin.x),
                            int(rect.origin.y),
                            int(rect.size.width),
                            int(rect.size.height),
                        )
                    )
                )

        surface.set_input_region(region)

    def toggle_input(self):
        self.set_input_passthrough(not self.click_through)

    def toggle_visibility(self):
        if self.get_visible():
            self.hide()
        else:
            self.show()
            self.present()
            GLib.idle_add(self.update_input_region)

    def on_cred_switch(self, provider_name, cred_id):
        self.selected_creds[provider_name] = cred_id
        if hasattr(self, "_last_data"):
            self.update_ui(self._last_data)

    def refresh_data(self) -> bool:
        def fetch():
            data_response = data.fetch_quota_data()
            self._last_data = data_response
            GLib.idle_add(self.update_ui, data_response)

        threading.Thread(target=fetch, daemon=True).start()
        return True

    def update_ui(self, data_response: Optional[data.QuotaData]):
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        self.interactive_widgets = []

        if not data_response:
            lbl = Gtk.Label(label="offline")
            lbl.add_css_class("quota-critical")
            self.content_box.append(lbl)
            return

        colors = CONFIG["colors"]

        for provider in data_response.providers:
            sel_id = self.selected_creds.get(provider.name, 1)
            flash_statuses = flash.compute_flash_statuses(
                provider.name,
                provider.credentials,
                self._flash_state,
                time.monotonic(),
            )

            header, interactive = ui.make_provider_header(
                provider.name,
                provider.credential_count,
                provider.credentials,
                sel_id,
                self.on_cred_switch,
                flash_statuses,
            )
            self.content_box.append(header)
            self.interactive_widgets.extend(interactive)

            active_creds = [c for c in provider.credentials if c.id == sel_id]
            if active_creds:
                display_groups = active_creds[0].quota_groups
            else:
                display_groups = provider.quota_groups

            if not active_creds:
                display_groups = sorted(
                    display_groups, key=data.sort_quota_groups(provider.name)
                )

            for quota_group in display_groups:
                countdown = data.format_countdown(quota_group.reset_time_iso)
                row = ui.make_quota_row(
                    quota_group.name,
                    quota_group.remaining,
                    quota_group.max_requests,
                    quota_group.remaining_pct or 0,
                    countdown,
                    colors,
                )
                self.content_box.append(row)

        GLib.idle_add(self.update_input_region)
