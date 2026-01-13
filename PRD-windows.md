# PRD: Windows Port (Quota Monitor)

## Goal
Deliver a Windows-native always-on-top, click-through quota overlay with tray controls and parity with Linux feature set.

## Scope
- Always-on-top transparent overlay
- Selective click-through (only interactive widgets receive input)
- System tray menu (show/hide, toggle click-through, quit)
- Config loading with Windows paths
- Same HTTP polling and data parsing

## Non-Goals
- Wayland/GTK-specific layer-shell behavior
- Linux-specific tray implementation
- UNIX signals

## Target Users
Windows developers with Python 3.11+ installed.

## Dependencies
- Python 3.11+
- `pywin32` (Win32 window APIs, tray)
- `ctypes` (optional) for lightweight Win32 calls
- Optional: `pystray` for tray menu abstraction

## Approach
### Windowing
- Replace GTK/LayerShell with a borderless layered window using Win32 APIs.
- Use `WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT` for overlay and click-through.
- Use `SetLayeredWindowAttributes` for transparency.

### Input Region
- Toggle between full click-through and interactive-only mode by adjusting the extended window style:
  - Click-through on: `WS_EX_TRANSPARENT`
  - Click-through off: remove `WS_EX_TRANSPARENT`
- If selective regions are needed, use a separate input-only overlay window for interactive areas.

### Tray
- Use `Shell_NotifyIcon` via `pywin32` or `pystray` for tray icon and menu.

### IPC/Controls
- Replace signals with local control API:
  - Local TCP port (localhost) or named pipe
  - Commands: `toggle_visibility`, `toggle_click_through`, `quit`

### Config
- Use `%APPDATA%\quota-monitor\config.toml`.

## Architecture Changes
- Extract platform-agnostic logic into a shared module (data polling, parsing).
- Introduce `platforms/windows/` with window + tray implementation.

## Tasks
1. Refactor core data model/polling into `core/` module.
2. Implement Win32 overlay window with layered styles.
3. Implement tray icon and menu actions.
4. Implement local control API and CLI helper.
5. Update config loader for Windows paths.
6. Provide packaging instructions (pyinstaller + installer).

## Code Snippets
### Win32 overlay window (pywin32)
```python
import win32con
import win32gui

ex_style = win32con.WS_EX_TOPMOST | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
style = win32con.WS_POPUP
hwnd = win32gui.CreateWindowEx(
    ex_style, "STATIC", "QuotaOverlay", style,
    0, 0, 260, 200, 0, 0, 0, None
)
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 200, win32con.LWA_ALPHA)
win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
```

### Toggle click-through
```python
def set_click_through(hwnd, enabled):
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if enabled:
        ex_style |= win32con.WS_EX_TRANSPARENT
    else:
        ex_style &= ~win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
```

## Risks
- Implementing GTK-like layout requires custom drawing or a different GUI toolkit.
- Handling per-widget hit-testing on Windows may need separate windows or a GUI toolkit layer.

## Success Criteria
- Overlay renders correctly, updates every N ms, and is controllable via tray.
- Click-through works except for tabs/buttons.
- Config and CLI controls operate without signals.
