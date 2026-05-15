from __future__ import annotations

"""Mock-only action helpers kept separate from live HA execution flow."""

from typing import Any

POWER_SERVICES = {"turn_on", "turn_off", "toggle"}
MOCK_POWER_DOMAINS = {"light", "switch"}


def is_mock_device(before_state: dict[str, Any] | None) -> bool:
    """Return True when an HA state is marked as a backend mock entity."""
    return bool(
        before_state
        and before_state.get("attributes", {}).get("mock_device") is True
    )


def is_mock_power_action(
    before_state: dict[str, Any] | None,
    *,
    domain: str,
    service: str,
    entity_id: str | list[str] | None,
) -> bool:
    """Return True when a power action should update a mock state directly."""
    return bool(
        is_mock_device(before_state)
        and domain in MOCK_POWER_DOMAINS
        and service in POWER_SERVICES
        and isinstance(entity_id, str)
    )


def mock_power_next_state(service: str, before_state: str | None) -> str:
    """Compute the next mock state for turn_on, turn_off, or toggle."""
    if service == "toggle":
        return "off" if before_state == "on" else "on"
    return "on" if service == "turn_on" else "off"
