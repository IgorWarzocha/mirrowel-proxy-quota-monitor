"""Tray process launcher."""

from __future__ import annotations

import os
import subprocess
import sys


def start_tray_process(parent_pid: int) -> None:
    src_dir = os.path.dirname(os.path.abspath(__file__))
    tray_script = os.path.join(src_dir, "tray.py")

    if not os.path.exists(tray_script):
        return

    env = os.environ.copy()
    for key in ["LD_PRELOAD", "GTK_MODULES", "GDK_BACKEND"]:
        if key in env:
            del env[key]

    env["GDK_BACKEND"] = "wayland"

    subprocess.Popen(
        [sys.executable, tray_script, str(parent_pid)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=env
    )
