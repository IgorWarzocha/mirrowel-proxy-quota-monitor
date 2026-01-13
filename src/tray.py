#!/usr/bin/env python3
import os
import sys
import signal

# Use Wayland for GTK3 to avoid initialization issues in some environments
os.environ["GDK_BACKEND"] = "wayland"

import gi
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator, GLib
except Exception as e:
    print(f"Tray import error: {e}")
    sys.exit(1)

def run_tray(parent_pid):
    Gtk.init(None)
    
    # Check if parent exists
    try:
        if parent_pid != 0:
            os.kill(parent_pid, 0)
    except ProcessLookupError:
        print("Tray: Parent process not found, exiting.")
        sys.exit(0)

    indicator = AppIndicator.Indicator.new(
        "quota-monitor-tray",
        "utilities-system-monitor",
        AppIndicator.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    
    menu = Gtk.Menu()
    
    item_toggle = Gtk.MenuItem(label="Show/Hide Overlay")
    item_toggle.connect("activate", lambda _: os.kill(parent_pid, signal.SIGUSR2))
    menu.append(item_toggle)
    
    item_click = Gtk.MenuItem(label="Toggle Click-through")
    item_click.connect("activate", lambda _: os.kill(parent_pid, signal.SIGUSR1))
    menu.append(item_click)
    
    menu.append(Gtk.SeparatorMenuItem())
    
    item_quit = Gtk.MenuItem(label="Exit")
    item_quit.connect("activate", lambda _: (os.kill(parent_pid, signal.SIGTERM), Gtk.main_quit()))
    menu.append(item_quit)
    
    menu.show_all()
    indicator.set_menu(menu)
    
    # Exit if parent dies
    def check_parent():
        try:
            if parent_pid != 0:
                os.kill(parent_pid, 0)
        except ProcessLookupError:
            print("Tray: Parent died, exiting.")
            Gtk.main_quit()
            return False
        return True
    
    GLib.timeout_add(3000, check_parent)
    
    print("Tray: Entering main loop")
    Gtk.main()

if __name__ == "__main__":
    p_pid = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    try:
        run_tray(p_pid)
    except Exception as e:
        print(f"Tray runtime error: {e}")
        sys.exit(1)
