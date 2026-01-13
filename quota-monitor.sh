#!/bin/bash
# Quota Monitor - Launcher with proper layer-shell preload
export LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so
exec python3 "${HOME}/.local/share/quota-monitor/main.py" "$@"
