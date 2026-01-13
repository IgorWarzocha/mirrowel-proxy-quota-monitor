# AGENTS.md - Mirrowel Proxy Quota Monitor Navigation Guide

## Overview

Transparent GTK4 overlay for monitoring proxy API quota on Hyprland/Wayland. Python 3.11+, uses gtk4-layer-shell for Wayland integration.

**Key characteristics:**
- Single-language Python project
- Configuration via TOML
- Signal-based inter-process communication (USR1/USR2)
- No package manager or test suite

## Project Structure

```
quota-monitor/
├── src/
│   ├── main.py         # Main application (GTK4, Wayland overlay)
│   ├── ui.py           # CSS generation and widget styling
│   ├── config.py       # TOML config loading with defaults
│   ├── tray.py         # System tray icon (GTK3, AyatanaAppIndicator)
│   └── __init__.py
├── config.toml         # User configuration template
├── install.sh          # Installation script
└── README.md           # User documentation
```

## Development Workflow

### Running from Source

```bash
# Manual execution (requires gtk4-layer-shell)
LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so python3 src/main.py

# Toggle click-through mode (sends SIGUSR1)
kill -USR1 $(pgrep -f "src.main")

# Toggle visibility (sends SIGUSR2)
kill -USR2 $(pgrep -f "src.main")
```

### Installation

```bash
./install.sh  # Copies to ~/.local/share/quota-monitor and sets up PATH
```

**Install locations:**
- App: `~/.local/share/quota-monitor/`
- Config: `~/.config/quota-monitor/config.toml`
- Binaries: `~/.local/bin/quota-monitor*`

### Runtime Control

The application responds to UNIX signals:
- `SIGUSR1` → Toggle click-through mode
- `SIGUSR2` → Show/hide overlay
- `SIGTERM` → Graceful shutdown

## Architecture

### Configuration Loading (@src/config.py)

- Uses `tomllib` (Python 3.11+ standard library)
- Search order: `~/.config/quota-monitor/config.toml` → repo root → `src/`
- Deep merge: user config overrides `DEFAULT_CONFIG` dict
- Exported as `CONFIG` singleton

### Main Application (@src/main.py)

**Data flow:**
1. Poll HTTP API every `refresh_interval_ms`
2. Parse JSON response into `Provider` → `Credential` → `QuotaGroup`
3. Update GTK widgets via `GLib.idle_add()`

**Key classes:**
- `QuotaGroup`: Single model/endpoint quota data
- `Credential`: Account credentials with multiple quota groups
- `Provider`: Top-level wrapper (e.g., OpenRouter, OpenAI)

**Wayland integration:**
- `Gtk4LayerShell.LayerShell` for layer surface
- Dynamic input region: calculate bounds of interactive widgets only
- Click-through mode: empty input region = full passthrough

### UI Components (@src/ui.py)

- `get_css()`: Generates CSS from config (colors, opacity, spacing)
- CSS classes: `.overlay-main`, `.quota-label`, `.progress-bar`
- Dynamic widget styling based on quota percentage (ok/warning/critical)

### System Tray (@src/tray.py)

- Runs as separate process (spawned by main.py)
- GTK3 + AyatanaAppIndicator3 (NOT GTK4)
- Parent process monitoring: exits if main.py dies
- Menu items: Show/Hide, Toggle Click-through, Exit

## Code Style Guidelines

### Python Conventions

- **Type hints:** Required for function signatures and dataclass fields
- **Dataclasses:** Use for structured data (QuotaGroup, Credential, Provider)
- **Imports:** Group standard library, third-party (gi), local modules
- **String formatting:** f-strings preferred
- **Error handling:** Print to stderr, continue gracefully where possible

### GTK4 Patterns

```python
# Layer shell initialization
LayerShell.init_for_window(window)
LayerShell.set_layer(window, LayerShell.Layer.OVERLAY)
LayerShell.set_anchor(window, edge, True)

# Dynamic input region (selective click-through)
rect = Gdk.Rectangle()
rect.x, rect.y, rect.width, rect.height = widget_bounds
window.set_input_region([rect])

# Thread-safe UI updates
GLib.idle_add(callback, *args)
```

### Configuration Access

```python
from src.config import CONFIG

host = CONFIG["server"]["host"]
interval = CONFIG["server"]["refresh_interval_ms"]
```

## Common Tasks

### Add New Configuration Option

1. Add key to `DEFAULT_CONFIG` in `src/config.py`
2. Add documentation comment to `config.toml`
3. Use via `CONFIG["section"]["key"]`

### Modify API Response Format

Edit `QuotaGroup`, `Credential`, or `Provider` dataclasses in `src/main.py` to match new JSON structure.

### Change Widget Styling

Modify `get_css()` in `src/ui.py` to add new CSS rules or adjust existing ones.

### Debugging

Run with verbose output: main.py prints to stdout/stderr. Check logs via:
```bash
quota-monitor 2>&1 | tee debug.log
```

## Dependencies

**System packages (Arch/pacman):**
- `python-gobject` (PyGObject bindings)
- `gtk4` (GUI toolkit)
- `gtk4-layer-shell` (Wayland layer shell)
- `libayatana-appindicator` (for tray icon)

**Python standard library only** - no pip packages required.

## Platform Constraints

- **Hyprland/Wayland only** (not X11-compatible)
- Requires wlroots-based compositor
- Uses Python 3.11+ `tomllib` module
