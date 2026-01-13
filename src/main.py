#!/usr/bin/env python3
"""
Mirrowel Proxy Quota Monitor - Transparent overlay for Hyprland/Wayland

Config: ~/.config/quota-monitor/config.toml
Toggle click-through: kill -USR1 $(pgrep -f quota-monitor)
"""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, GLib
import os
import signal

from .overlay import QuotaOverlay
from .tray_manager import start_tray_process


_window = None


def toggle_handler(signum, frame):
    global _window
    if _window:
        GLib.idle_add(_window.toggle_input)


def visibility_handler(signum, frame):
    global _window
    if _window:
        GLib.idle_add(_window.toggle_visibility)


def quit_handler(signum, frame):
    GLib.idle_add(Gtk.Application.get_default().quit)


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=None)

    def do_activate(self):
        global _window
        _window = QuotaOverlay(self)
        _window.present()
        start_tray_process(os.getpid())


def main():
    signal.signal(signal.SIGINT, quit_handler)
    signal.signal(signal.SIGTERM, quit_handler)
    signal.signal(signal.SIGUSR1, toggle_handler)
    signal.signal(signal.SIGUSR2, visibility_handler)

    app = App()
    app.run(None)


if __name__ == "__main__":
    main()

