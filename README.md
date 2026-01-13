# Mirrowel Proxy Quota Monitor

A transparent, always-on-top, click-through overlay for monitoring Mirrowel's LLM API Key Proxy quota usage on Hyprland/Wayland.

## Features

Built to pair with Mirrowel's LLM API Key Proxy: https://github.com/Mirrowel/LLM-API-Key-Proxy

- **Transparent overlay** - Configurable opacity, sits on top of everything
- **Credential Switching** - Click tab selectors (e.g., `1s`, `2f`) to switch between multiple accounts
- **Selective Click-through** - Window is passthrough except for interactive UI elements
- **Layer-shell** - Proper Wayland overlay using gtk4-layer-shell
- **Real-time updates** - Configurable refresh interval
- **Color-coded** - Green/yellow/red based on remaining quota %
- **Reset timers** - Shows countdown until quota resets
- **Easy config** - Well-commented TOML config file

## Requirements

- Arch Linux with Hyprland (or any wlroots-based compositor)
- Python 3.11+
- GTK4 + gtk4-layer-shell

```bash
sudo pacman -S python-gobject gtk4 gtk4-layer-shell
```

## Platform Notes

I develop and test this on Omarchy (Hyprland/Wayland), so I can only speculate about other platforms. There are PRD docs with approach notes, dependencies, and code snippets to help AI agents (or contributors) port this to other OSes. This overlay is designed to sit alongside Mirrowel's LLM API Key Proxy (https://github.com/Mirrowel/LLM-API-Key-Proxy):

- `PRD-macos.md`
- `PRD-windows.md`
- `PRD-linux-ubuntu.md`

## Installation

```bash
git clone <repo>
cd quota-monitor
chmod +x install.sh
./install.sh
```

## Usage

```bash
quota-monitor              # Start overlay
quota-monitor-toggle       # Toggle click-through mode
```

### Hyprland Keybind

Add to `~/.config/hypr/hyprland.conf`:

```
bind = SUPER SHIFT, Q, exec, quota-monitor-toggle
```

## Configuration

Edit `~/.config/quota-monitor/config.toml`:

```toml
# Server connection
[server]
host = "192.168.0.113"
port = 8000
api_key = "VerysecretKey"
refresh_interval_ms = 5000

# Appearance
[appearance]
background_opacity = 0.55  # 0.0 = invisible, 1.0 = solid
text_opacity = 0.85
width = 210
corner_radius = 10

# Position
[position]
anchor = "top-right"  # top-right, top-left, bottom-right, bottom-left
margin_top = 10
margin_right = 10

# Behavior
[behavior]
click_through = true  # Start in click-through mode

# Colors
[colors]
ok = "#4caf50"        # Green - quota > 30%
warning = "#ff9800"   # Orange - quota 10-30%
critical = "#f44336"  # Red - quota <= 10%
provider = "#64b5f6"  # Provider name color
background = "10, 12, 16"  # RGB values
```

After editing, restart: `pkill -f quota-monitor && quota-monitor &`

## How It Works

Uses `gtk4-layer-shell` to create a proper Wayland layer surface in the OVERLAY layer. 

**Input Handling:**
By default, the overlay is passthrough, but it dynamically calculates the bounds of interactive elements (like the credential tabs) and updates the input region. This allows you to click tabs even when the rest of the window is "invisible" to the mouse.

**Credential Tabs:**
- Labels like `1s`, `2f` reflect the account index and tier (`s`tandard/payg, `f`ree).
- Tab colors reflect the worst-case quota status for that specific account.
- Clicking a tab switches the model list to that account's specific quotas.

## Files

```
~/.config/quota-monitor/config.toml   # Configuration
~/.local/share/quota-monitor/main.py  # Application
~/.local/bin/quota-monitor            # Launcher script
~/.local/bin/quota-monitor-toggle     # Toggle script
```

## Manual Run

```bash
LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so python3 src/main.py
```

## License

MIT
