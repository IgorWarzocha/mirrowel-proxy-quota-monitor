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
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1] + '+00:00'
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
        if minutes > 0:
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
            weights = {"claude": 0, "g3-pro": 1, "g3-flash": 2, "g25-flash": 3, "g25-lite": 4}
            return weights.get(quota_group.name, 10), quota_group.name
        return 10, quota_group.name

    return sort_key


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
            for gname, gdata in pdata.get("quota_groups", {}).items():
                display_name = gname
                if pname.upper() == "GEMINI_CLI" and gname == "pro":
                    display_name = "3-pro"

                provider_quota_groups.append(QuotaGroup(
                    name=display_name,
                    remaining=gdata.get("total_requests_remaining", 0),
                    max_requests=gdata.get("total_requests_max", 0),
                    remaining_pct=gdata.get("total_remaining_pct"),
                    reset_time_iso=gdata.get("reset_time_iso"),
                ))

            credentials = []
            for i, cdata in enumerate(pdata.get("credentials", [])):
                c_quota_groups = []
                worst_pct = 100.0

                mgroups = cdata.get("model_groups", {})
                if not mgroups:
                    mgroups = cdata.get("models", {})

                for mname, mdata in mgroups.items():
                    pct = mdata.get("remaining_pct")
                    if pct is None:
                        fraction = mdata.get("baseline_remaining_fraction")
                        if fraction is not None:
                            pct = int(fraction * 100)
                        else:
                            pct = 0.0

                    if pct < worst_pct:
                        worst_pct = pct

                    rem = mdata.get("requests_remaining")
                    if rem is None:
                        rem = mdata.get("remaining", 0)

                    max_r = mdata.get("requests_max")
                    if max_r is None:
                        max_r = mdata.get("quota_max_requests") or mdata.get("max", 0)

                    display_name = mname
                    if pname.upper() == "GEMINI_CLI" and mname == "pro":
                        display_name = "3-pro"

                    c_quota_groups.append(QuotaGroup(
                        name=display_name,
                        remaining=rem,
                        max_requests=max_r,
                        remaining_pct=float(pct),
                        reset_time_iso=mdata.get("reset_time_iso") or mdata.get("quota_reset_ts"),
                    ))

                c_quota_groups.sort(key=sort_quota_groups(pname))

                tier_val = cdata.get("tier") or "free"
                tier_char = tier_val[0].lower()
                credentials.append(Credential(
                    id=i + 1,
                    name=cdata.get("identifier", "unknown"),
                    tier=tier_char,
                    status=cdata.get("status", "active"),
                    quota_groups=c_quota_groups,
                    worst_pct=float(worst_pct)
                ))

            providers.append(Provider(
                name=pname,
                credential_count=pdata.get("credential_count") or 0,
                approx_cost=pdata.get("approx_cost") or 0,
                quota_groups=provider_quota_groups,
                credentials=credentials
            ))

        summary = data.get("summary", {})
        return QuotaData(
            providers=providers,
            total_credentials=summary.get("total_credentials") or 0,
            total_cost=summary.get("approx_total_cost") or 0
        )
    except Exception as e:
        print(f"Error: {e}")
        return None
