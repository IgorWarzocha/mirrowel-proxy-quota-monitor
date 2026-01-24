"""
Mirrowel Proxy Quota Monitor - UI Components
"""

from gi.repository import Gtk, Gdk
from .config import CONFIG


def get_css() -> bytes:
    """Generate CSS from config."""

    appearance = CONFIG["appearance"]
    colors = CONFIG["colors"]

    bg_opacity = appearance["background_opacity"]
    text_opacity = appearance["text_opacity"]
    radius = appearance["corner_radius"]
    bg_rgb = colors["background"]

    return f"""
    window {{
        background: transparent;
    }}
    
    .overlay-main {{
        background: rgba({bg_rgb}, {bg_opacity});
        border-radius: {radius}px;
        border: 1px solid rgba(100, 140, 180, 0.15);
    }}
    
    .overlay-content {{
        padding: 10px;
    }}
    
    .overlay-status {{
        padding: 3px 10px 5px 10px;
        font-size: 0.65em;
        color: rgba(255, 255, 255, 0.25);
    }}
    
    /* Provider name header */
    .provider-name {{
        font-weight: bold;
        font-size: 0.78em;
        color: {colors["provider"]};
        opacity: {text_opacity};
        margin-top: 1px;
        margin-bottom: 1px;
    }}
    
    /* Quota row text */
    .quota-line {{
        font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
        font-size: 0.72em;
        opacity: {text_opacity};
    }}
    
    /* Quota status colors */
    .quota-ok {{ color: {colors["ok"]}; }}
    .quota-warn {{ color: {colors["warning"]}; }}
    .quota-critical {{ color: {colors["critical"]}; }}
    
    .reset-time {{
        font-family: "JetBrains Mono", "Fira Code", monospace;
        font-size: 0.72em;
        color: rgba(255, 200, 100, 0.9);
        font-weight: bold;
    }}
    
    /* Cost per provider */
    .provider-cost {{
        font-size: 0.62em;
        color: rgba(255, 255, 255, 0.35);
        margin-bottom: 2px;
    }}
    
    /* Bottom summary bar */
    .summary-box {{
        padding-top: 4px;
        margin-top: 2px;
        border-top: 1px solid rgba(100, 120, 140, 0.12);
    }}
    
    .summary-text {{
        font-size: 0.7em;
        color: rgba(255, 255, 255, 0.6);
    }}

    /* Credential tabs */
    .cred-tab {{
        font-family: "JetBrains Mono", monospace;
        font-size: 0.65em;
        padding: 1px 4px;
        border-radius: 3px;
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.9);
        font-weight: bold;
    }}
    
    .cred-tab-active {{
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}

    @keyframes tab-flash-ok {{
        0% {{ background: rgba(76, 175, 80, 0.0); }}
        50% {{ background: rgba(76, 175, 80, 0.7); }}
        100% {{ background: rgba(76, 175, 80, 0.0); }}
    }}

    @keyframes tab-flash-warn {{
        0% {{ background: rgba(255, 152, 0, 0.0); }}
        50% {{ background: rgba(255, 152, 0, 0.7); }}
        100% {{ background: rgba(255, 152, 0, 0.0); }}
    }}

    @keyframes tab-flash-critical {{
        0% {{ background: rgba(244, 67, 54, 0.0); }}
        50% {{ background: rgba(244, 67, 54, 0.7); }}
        100% {{ background: rgba(244, 67, 54, 0.0); }}
    }}

    .cred-tab-flash-ok {{
        animation: tab-flash-ok 0.5s ease-in-out 10;
    }}

    .cred-tab-flash-warn {{
        animation: tab-flash-warn 0.5s ease-in-out 10;
    }}

    .cred-tab-flash-critical {{
        animation: tab-flash-critical 0.5s ease-in-out 10;
    }}
    
    .credential-tabs {{
        margin-bottom: 2px;
    }}
    """.encode()


def load_css():
    """Load CSS into GTK."""
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(get_css())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def make_provider_header(
    name: str,
    cred_count: int,
    credentials: list | None = None,
    selected_id: int = 1,
    on_click=None,
    flash_statuses: dict[int, str] | None = None,
) -> tuple[Gtk.Box, list[Gtk.Widget]]:
    """Create provider name header with credential tabs."""
    main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

    # Tab row (on top)
    interactive = []
    if credentials and len(credentials) > 1:
        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tabs.add_css_class("credential-tabs")
        for c in credentials:
            tab = Gtk.Label()
            tab.set_markup(f"<tt>{c.id}{c.tier}</tt>")
            tab.add_css_class("cred-tab")

            if flash_statuses and c.id in flash_statuses:
                status = flash_statuses[c.id]
                tab.add_css_class(f"cred-tab-flash-{status}")

            if c.id == selected_id:
                tab.add_css_class("cred-tab-active")

            if on_click:
                gesture = Gtk.GestureClick()
                gesture.connect(
                    "released", lambda g, n, x, y, cid=c.id: on_click(name, cid)
                )
                tab.add_controller(gesture)
                interactive.append(tab)

            tabs.append(tab)
        main_vbox.append(tabs)

    # Provider name row
    header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    lbl = Gtk.Label()
    lbl.set_markup(
        f"<b>{name.upper()}</b> <span size='small' color='#555'>({cred_count})</span>"
    )
    lbl.set_halign(Gtk.Align.START)
    lbl.add_css_class("provider-name")
    header_box.append(lbl)
    main_vbox.append(header_box)

    return main_vbox, interactive


def make_provider_cost(cost: float) -> Gtk.Label:
    """Create cost label for provider."""
    lbl = Gtk.Label()
    lbl.set_markup(f"${cost:.2f}")
    lbl.set_halign(Gtk.Align.START)
    lbl.add_css_class("provider-cost")
    return lbl


def make_quota_row(
    name: str,
    remaining: int,
    max_req: int,
    pct: float,
    reset_countdown: str,
    colors: dict,
) -> Gtk.Box:
    """
    Create a single quota row.

    Layout: [name  remaining/max  pct%] [reset_time]
    """
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    # Pick color based on percentage
    if pct <= 10:
        color = colors["critical"]
    elif pct < 30:
        color = colors["warning"]
    else:
        color = colors["ok"]

    # Quota info
    name_short = name[:10]
    info = Gtk.Label()
    info.set_markup(
        f"<tt><span color='{color}'>{name_short:10s}</span> "
        f"{remaining:>5}/{max_req:<5} "
        f"<span color='{color}'>{int(pct):>3}%</span></tt>"
    )
    info.set_halign(Gtk.Align.START)
    info.add_css_class("quota-line")
    row.append(info)

    # Reset time (prominent)
    if reset_countdown:
        rt = Gtk.Label()
        rt.set_markup(f"<tt>{reset_countdown}</tt>")
        rt.set_halign(Gtk.Align.START)
        rt.add_css_class("reset-time")
        row.append(rt)

    return row


def make_summary(total_creds: int, total_cost: float, ok_color: str) -> Gtk.Box:
    """Create bottom summary bar."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.add_css_class("summary-box")

    lbl = Gtk.Label()
    lbl.set_markup(
        f"<span color='#666'>{total_creds} creds</span>  "
        f"<span color='{ok_color}'>$ {total_cost:.2f}</span>"
    )
    lbl.add_css_class("summary-text")
    box.append(lbl)

    return box
