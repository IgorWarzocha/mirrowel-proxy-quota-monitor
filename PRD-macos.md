# PRD: macOS Port (Quota Monitor)

## Goal
Deliver a macOS-native always-on-top, click-through quota overlay with tray controls and parity with Linux feature set.

## Scope
- Always-on-top transparent overlay
- Selective click-through (only interactive widgets receive input)
- Tray/status-bar menu (show/hide, toggle click-through, quit)
- Config loading with macOS paths
- Same HTTP polling and data parsing

## Non-Goals
- Wayland/GTK-specific layer-shell behavior
- Linux-specific tray implementation
- Signal-based controls

## Target Users
macOS developers with Python 3.11+ installed.

## Dependencies
- Python 3.11+
- PyObjC (AppKit, Quartz)
- `pyobjc-framework-Cocoa`
- Optional: `pyobjc-framework-Quartz` (hit-testing / input regions)
- Optional: `pystray` for simplified tray (if not using AppKit status bar)

## Approach
### Windowing
- Replace GTK/LayerShell with AppKit borderless `NSWindow`.
- Use `NSStatusWindowLevel` to keep overlay above other windows.
- Set `ignoresMouseEvents` for click-through; enable mouse only for interactive regions.

### Input Region
- For selective click-through, use a transparent overlay window that captures clicks only on interactive subviews. Alternative: stack two windows (one click-through, one input-only for tabs).

### Tray
- Use AppKit `NSStatusBar` and `NSMenu` for status bar controls.

### IPC/Controls
- Replace UNIX signals with local control API:
  - Local TCP port (localhost) or Unix domain socket
  - Expose commands: `toggle_visibility`, `toggle_click_through`, `quit`

### Config
- Use `~/Library/Application Support/quota-monitor/config.toml`.

## Architecture Changes
- Extract platform-agnostic logic into a shared module (data polling, parsing).
- Introduce `platforms/macos/` with window + tray implementation.

## Tasks
1. Refactor core data model/polling into `core/` module.
2. Implement macOS overlay window with AppKit.
3. Implement status-bar menu actions.
4. Implement local control API and CLI helper.
5. Update config loader for macOS paths.
6. Provide packaging instructions (pyinstaller or .app bundle).

## Code Snippets
### macOS overlay window (AppKit)
```python
from AppKit import NSWindow, NSBorderlessWindowMask, NSStatusWindowLevel
from AppKit import NSColor, NSView

window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
    ((0, 0), (260, 200)), NSBorderlessWindowMask, 2, False
)
window.setBackgroundColor_(NSColor.clearColor())
window.setOpaque_(False)
window.setLevel_(NSStatusWindowLevel)
window.setIgnoresMouseEvents_(True)
```

### Status bar menu
```python
from AppKit import NSStatusBar, NSMenu, NSMenuItem

status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(-1)
status_item.setTitle_("Quota")
menu = NSMenu.alloc().init()
menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
    "Show/Hide", "toggleVisibility:", ""
))
status_item.setMenu_(menu)
```

## Risks
- Precise click-through regions require AppKit hit-testing or multi-window layering.
- PyObjC packaging and code signing for .app distribution.

## Success Criteria
- Overlay renders correctly, updates every N ms, and is controllable via tray.
- Click-through works except for tabs/buttons.
- Config and CLI controls operate without signals.
