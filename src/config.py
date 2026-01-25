"""
Mirrowel Proxy Quota Monitor - Configuration loading
"""

from pathlib import Path
import tomllib


DEFAULT_CONFIG = {
    "server": {
        "host": "127.0.0.1",
        "port": 8000,
        "api_key": "VerysecretKey",
        "refresh_interval_ms": 5000,
    },
    "appearance": {
        "background_opacity": 0.55,
        "text_opacity": 0.85,
        "width": 340,
        "corner_radius": 10,
    },
    "position": {
        "anchor": "top-right",
        "margin_top": 10,
        "margin_right": 10,
        "margin_bottom": 10,
        "margin_left": 10,
    },
    "behavior": {
        "click_through": True,
    },
    "colors": {
        "ok": "#4caf50",
        "warning": "#ff9800",
        "critical": "#f44336",
        "provider": "#64b5f6",
        "background": "10, 12, 16",
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge dicts."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    """Load config from TOML."""
    config_paths = [
        Path.home() / ".config" / "quota-monitor" / "config.toml",
        Path(__file__).parent.parent / "config.toml",
        Path(__file__).parent / "config.toml",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    user_config = tomllib.load(f)
                return deep_merge(DEFAULT_CONFIG, user_config)
            except Exception as e:
                print(f"Error: {e}")

    return DEFAULT_CONFIG


CONFIG = load_config()
