"""Credential tab flash state tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from .data import Credential


@dataclass
class FlashState:
    last_statuses: dict[str, dict[str, str]]
    flash_until: dict[str, tuple[str, float]]


def status_for_pct(pct: float) -> str:
    if pct <= 10:
        return "critical"
    if pct < 30:
        return "warn"
    return "ok"


def compute_flash_statuses(
    provider_name: str,
    credentials: Sequence[Credential],
    state: FlashState,
    now: Optional[float] = None,
) -> dict[int, str]:
    if now is None:
        now = time.monotonic()

    flash_statuses: dict[int, str] = {}
    severity_rank = {"ok": 0, "warn": 1, "critical": 2}

    for cred in credentials:
        cred_key = f"{provider_name}:{cred.id}"
        current_statuses = {
            group.name: status_for_pct(float(group.remaining_pct or 0))
            for group in cred.quota_groups
        }
        prev_statuses = state.last_statuses.get(cred_key)
        changed_statuses: list[str] = []

        if prev_statuses is not None:
            changed_statuses = [
                current_statuses[name]
                for name in current_statuses
                if prev_statuses.get(name) != current_statuses[name]
            ]

        if changed_statuses:
            flash_status = max(changed_statuses, key=lambda s: severity_rank.get(s, 0))
            state.flash_until[cred_key] = (flash_status, now + 5.0)

        state.last_statuses[cred_key] = current_statuses

        if cred_key in state.flash_until:
            status, until = state.flash_until[cred_key]
            if now <= until:
                flash_statuses[cred.id] = status
            else:
                del state.flash_until[cred_key]

    return flash_statuses
