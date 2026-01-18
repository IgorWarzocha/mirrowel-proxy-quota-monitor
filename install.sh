#!/bin/bash
set -e

INSTALL_DIR="$HOME/.local/share/quota-monitor"
CONFIG_DIR="$HOME/.config/quota-monitor"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "Installing Mirrowel Proxy Quota Monitor for Hyprland..."
echo ""

# Check dependencies
missing=""
# Try system python first since it usually has the GI bindings
PYTHON_CMD="python3"
if ! /usr/bin/python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
        missing="$missing python-gobject gtk4"
    fi
else
    PYTHON_CMD="/usr/bin/python3"
fi

if ! $PYTHON_CMD -c "import gi; gi.require_version('Gtk4LayerShell', '1.0')" 2>/dev/null; then
    missing="$missing gtk4-layer-shell"
fi

if [ -n "$missing" ]; then
    echo "Missing dependencies:$missing"
    echo "Install: sudo pacman -S$missing"
    exit 1
fi

mkdir -p "$INSTALL_DIR/src"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$AUTOSTART_DIR"

cp src/__init__.py "$INSTALL_DIR/src/"
cp src/config.py "$INSTALL_DIR/src/"
cp src/ui.py "$INSTALL_DIR/src/"
cp src/data.py "$INSTALL_DIR/src/"
cp src/flash.py "$INSTALL_DIR/src/"
cp src/overlay.py "$INSTALL_DIR/src/"
cp src/tray_manager.py "$INSTALL_DIR/src/"
cp src/main.py "$INSTALL_DIR/src/"
cp src/tray.py "$INSTALL_DIR/src/"

if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    cp config.toml "$CONFIG_DIR/config.toml"
    echo "Created config: $CONFIG_DIR/config.toml"
else
    echo "Config exists: $CONFIG_DIR/config.toml (not overwritten)"
fi

# Update launcher to use the detected python command
cat > "$BIN_DIR/quota-monitor" << LAUNCHER
#!/bin/bash
export LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so
cd "${INSTALL_DIR}"
exec $PYTHON_CMD -m src.main "\$@"
LAUNCHER
chmod +x "$BIN_DIR/quota-monitor"

cat > "$BIN_DIR/quota-monitor-toggle" << 'TOGGLE'
#!/bin/bash
PID=$(pgrep -f "src.main" | head -1)
if [ -n "$PID" ]; then
    kill -USR1 "$PID"
    echo "Toggled click-through mode"
else
    echo "quota-monitor not running"
fi
TOGGLE
chmod +x "$BIN_DIR/quota-monitor-toggle"

cat > "$BIN_DIR/quota-monitor-visibility" << 'VIS'
#!/bin/bash
PID=$(pgrep -f "src.main" | head -1)
if [ -n "$PID" ]; then
    kill -USR2 "$PID"
    echo "Toggled visibility"
else
    echo "quota-monitor not running"
fi
VIS
chmod +x "$BIN_DIR/quota-monitor-visibility"

cat > "$DESKTOP_DIR/quota-monitor.desktop" << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Mirrowel Proxy Quota Monitor
Comment=Transparent Mirrowel proxy quota overlay for Hyprland
Exec=quota-monitor
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;System;
DESKTOP

cp "$DESKTOP_DIR/quota-monitor.desktop" "$AUTOSTART_DIR/"

mkdir -p "$HOME/.config/systemd/user"
cp quota-monitor.service "$HOME/.config/systemd/user/"
systemctl --user daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "Commands:"
echo "  quota-monitor        - Start the overlay"
echo "  quota-monitor-toggle - Toggle click-through mode"
echo "  systemctl --user enable --now quota-monitor.service - Run as systemd service"
echo ""
echo "Config file:"
echo "  $CONFIG_DIR/config.toml"
echo ""
echo "Edit the config to change:"
echo "  - Server address and API key"
echo "  - Transparency and colors"
echo "  - Position (top-right, top-left, etc.)"
echo ""
echo "Add keybind to ~/.config/hypr/hyprland.conf:"
echo ""
echo '  bind = SUPER SHIFT, Q, exec, quota-monitor-toggle'
echo ""
