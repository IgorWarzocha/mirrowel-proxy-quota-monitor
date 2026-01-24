"""Quota data models and API fetching."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .config import CONFIG


@dataclass
class QuotaGroup:
    name: str
    remaining: int
    max_requests: int
    remaining_pct: Optional[float]
    reset_time_iso: Optional[str]


@dataclass
class Credential:
    id: int
    name: str
    tier: str
    status: str
    quota_groups: list[QuotaGroup]
    worst_pct: float


@dataclass
class Provider:
    name: str
    credential_count: int
    approx_cost: float
    quota_groups: list[QuotaGroup]
    credentials: list[Credential]


@dataclass
class QuotaData:
    providers: list[Provider]
    total_credentials: int
    total_cost: float


def format_countdown(iso_str: Optional[str]) -> str:
    """Convert ISO timestamp to countdown string like '2h30m'."""
    if not iso_str or iso_str == "null":
        return ""
    try:
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        reset_time = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        diff = (reset_time - now).total_seconds()
        if diff <= 0:
            return "now"

        days = int(diff // 86400)
        hours = int((diff % 86400) // 3600)
        minutes = int((diff % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 and days == 0:
            parts.append(f"{minutes}m")
        if not parts:
            parts.append(f"{int(diff % 60)}s")
        return "".join(parts)
    except Exception:
        return ""


def sort_quota_groups(provider: str):
    p_upper = provider.upper()

    def sort_key(quota_group: QuotaGroup):
        if p_upper == "GEMINI_CLI":
            weights = {"3-pro": 0, "3-flash": 1, "25-flash": 2}
            return weights.get(quota_group.name, 10), quota_group.name
        if p_upper == "ANTIGRAVITY":
            weights = {
                "claude": 0,
                "g3-pro": 1,
                "g3-flash": 2,
                "g25-flash": 3,
                "g25-lite": 4,
            }
            return weights.get(quota_group.name, 10), quota_group.name
        return 10, quota_group.name

    return sort_key


def unix_to_iso(unix_ts: Optional[float]) -> Optional[str]:
    """Convert Unix timestamp to ISO string."""
    if unix_ts is None or unix_ts == 0:
        return None
    try:
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def fetch_quota_data() -> Optional[QuotaData]:
    """Fetch data from the proxy API."""
    server = CONFIG["server"]
    url = f"http://{server['host']}:{server['port']}/v1/quota-stats"

    try:
        req = urllib.request.Request(url)
        if server["api_key"]:
            req.add_header("Authorization", f"Bearer {server['api_key']}")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        providers = []
        for pname, pdata in data.get("providers", {}).items():
            provider_quota_groups = []

            p_quota_groups = pdata.get("quota_groups", {})
            for gname, gdata in p_quota_groups.items():
                display_name = gname
                if pname.upper() == "GEMINI_CLI" and gname == "pro":
                    display_name = "3-pro"

                remaining = 0
                max_requests = 0
                remaining_pct = None
                reset_at = None

                windows = gdata.get("windows", {})
                for window_name, window_data in windows.items():
                    remaining = window_data.get("total_remaining", 0)
                    max_requests = window_data.get("total_max", 0)
                    remaining_pct = window_data.get("remaining_pct")

                    if remaining_pct is None and max_requests > 0:
                        remaining_pct = (remaining / max_requests) * 100

                provider_quota_groups.append(
                    QuotaGroup(
                        name=display_name,
                        remaining=remaining,
                        max_requests=max_requests,
                        remaining_pct=remaining_pct,
                        reset_time_iso=None,
                    )
                )

            credentials = []
            creds_data = pdata.get("credentials", {})

            cred_items = creds_data.items() if isinstance(creds_data, dict) else []

            for i, (ckey, cdata) in enumerate(cred_items):
                if not isinstance(cdata, dict):
                    continue

                c_quota_groups = []
                worst_pct = 100.0

                group_usage = cdata.get("group_usage", {})
                if not group_usage:
                    group_usage = cdata.get("model_groups", {})
                if not group_usage:
                    group_usage = cdata.get("models", {})

                for gname, gdata in group_usage.items():
                    if not isinstance(gdata, dict):
                        continue

                    windows = gdata.get("windows", {})
                    window_data = next(iter(windows.values())) if windows else {}

                    remaining = window_data.get("remaining", 0)
                    limit = window_data.get("limit", 0)

                    pct = window_data.get("remaining_pct")
                    if pct is None and limit > 0:
                        pct = (remaining / limit) * 100
                    if pct is None:
                        pct = 0.0

                    if pct < worst_pct:
                        worst_pct = pct

                    display_name = gname
                    if pname.upper() == "GEMINI_CLI" and gname == "pro":
                        display_name = "3-pro"

                    reset_at = window_data.get("reset_at")
                    reset_iso = unix_to_iso(reset_at)

                    c_quota_groups.append(
                        QuotaGroup(
                            name=display_name,
                            remaining=remaining,
                            max_requests=limit,
                            remaining_pct=float(pct),
                            reset_time_iso=reset_iso,
                        )
                    )

                c_quota_groups.sort(key=sort_quota_groups(pname))

                tier_val = cdata.get("tier") or "free"
                tier_char = tier_val[0].lower()

                identifier = cdata.get("identifier", "unknown")
                if identifier == "unknown":
                    identifier = ckey

                credentials.append(
                    Credential(
                        id=i + 1,
                        name=identifier,
                        tier=tier_char,
                        status=cdata.get("status", "active"),
                        quota_groups=c_quota_groups,
                        worst_pct=float(worst_pct),
                    )
                )

            providers.append(
                Provider(
                    name=pname,
                    credential_count=pdata.get("credential_count") or 0,
                    approx_cost=pdata.get("approx_cost") or 0,
                    quota_groups=provider_quota_groups,
                    credentials=credentials,
                )
            )

        summary = data.get("summary", {})
        return QuotaData(
            providers=providers,
            total_credentials=summary.get("total_credentials") or 0,
            total_cost=summary.get("approx_total_cost") or 0,
        )
    except Exception as e:
        print(f"Error: {e}")
        return None
