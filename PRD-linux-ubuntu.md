# PRD: Linux (Ubuntu/Standard Desktop) Port

## Goal
Run Quota Monitor on mainstream Linux desktops (Ubuntu, Fedora, Debian) without Hyprland/Wayland-specific dependencies while preserving core overlay behavior.

## Scope
- Always-on-top transparent overlay
- Click-through mode (full window)
- Tray menu (show/hide, toggle click-through, quit)
- X11 or Wayland support depending on environment
- Same HTTP polling and data parsing

## Non-Goals
- Hyprland-only layer-shell integration
- Perfect selective input regions on all compositors

## Target Users
Linux developers on Ubuntu/Fedora/Debian with Python 3.11+.

## Dependencies
### Common
- Python 3.11+
- PyGObject (`python3-gi`)
- GTK4 (`libgtk-4-1`, `gir1.2-gtk-4.0`)

### Wayland (GNOME/KDE)
- `gtk4-layer-shell` (if compositor supports layer-shell)
- `libgtk4-layer-shell-dev` (build/runtime)

### X11 fallback
- GTK4 X11 backend (provided by GTK)
- Optional: `python3-xlib` for click-through toggling if needed

### Tray
- `libayatana-appindicator3-1` and GIR bindings
- `gir1.2-ayatanaappindicator3-0.1`

## Approach
### Windowing
- Prefer Wayland layer-shell when available (GNOME/KDE on Wayland may not support it fully).
- Provide X11 fallback using standard GTK window flags:
  - `set_keep_above(True)` for always-on-top
  - Transparent window via RGBA visual

### Click-through
- Baseline: toggle full click-through by setting input shape to empty (X11) or surface input region (Wayland when supported).
- If compositor lacks input region support, fall back to “not click-through” mode.

### Tray
- Use Ayatana AppIndicator where available.
- Fallback to `Gtk.StatusIcon` is deprecated; optionally ship without tray on desktops where appindicator isn’t present.

### IPC/Controls
- Keep UNIX signals for Linux (existing behavior).
- Optional: local socket control API for environments without signals.

### Config
- Use standard XDG path: `~/.config/quota-monitor/config.toml` (current behavior).

## Architecture Changes
- Add backend detection: Wayland vs X11 at runtime.
- Add layer-shell availability check and fallback behavior.
- Make tray optional if appindicator unavailable.

## Tasks
1. Add backend detection and feature flags.
2. Implement X11 overlay setup and transparency.
3. Implement click-through fallback behavior.
4. Make tray optional with graceful degradation.
5. Update docs for Ubuntu/Fedora install steps.

## Code Snippets
### Backend detection
```python
import os

def detect_backend():
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"
```

### X11 always-on-top + transparent window
```python
window.set_keep_above(True)
window.set_app_paintable(True)
```

## Risks
- Wayland layer-shell support is compositor-dependent (GNOME may not support overlay layer).
- AppIndicator availability varies by desktop environment.

## Success Criteria
- App runs on Ubuntu GNOME (Wayland and X11 sessions) with visible overlay.
- Click-through works where supported or degrades gracefully.
- Tray menu available when AppIndicator is installed.
