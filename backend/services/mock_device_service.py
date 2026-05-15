from __future__ import annotations

from typing import Any, Literal

import ha_client
from schemas.ha import MockDeviceCreate
from services.action_service import ActionRequest, execute_ha_action
from services.mock_catalog import DEFAULT_MOCK_DEVICES


def build_mock_attributes(device: MockDeviceCreate) -> dict[str, Any]:
    """Build marker attributes for backend-managed virtual HA entities."""
    attributes = {
        "friendly_name": device.name,
        "supported_features": 0,
        "mock_device": True,
        "managed_by": "smart-home-ha-backend",
        "room": device.room,
        "domain": device.domain,
    }
    attributes.update(device.attributes)
    return attributes


def create_or_update_mock_device(device: MockDeviceCreate) -> dict[str, Any]:
    """Create or overwrite one virtual entity state in Home Assistant."""
    return ha_client.set_state(
        device.entity_id,
        device.initial_state,
        build_mock_attributes(device),
    )


def seed_default_mock_devices() -> list[dict[str, Any]]:
    """Seed default virtual devices during startup for local demos/tests."""
    seeded: list[dict[str, Any]] = []
    for device in DEFAULT_MOCK_DEVICES:
        seeded.append(create_or_update_mock_device(device))
    return seeded


def default_mock_devices_by_room() -> dict[str, list[dict[str, Any]]]:
    """Group default virtual devices by room for discovery endpoints."""
    rooms: dict[str, list[dict[str, Any]]] = {}
    for device in DEFAULT_MOCK_DEVICES:
        rooms.setdefault(device.room, []).append(device.model_dump())
    return rooms


def list_mock_devices() -> list[dict[str, Any]]:
    """Return HA states that were marked as backend-managed mock devices."""
    states = ha_client.get_states()
    return [
        item
        for item in states
        if item.get("attributes", {}).get("mock_device") is True
    ]


def _entity_domain(entity_id: str) -> str:
    """Extract the HA domain prefix from an entity ID."""
    return entity_id.split(".", 1)[0]


def set_mock_device_power(
    entity_id: str,
    state: Literal["on", "off"],
) -> dict[str, Any]:
    """Set a backend-managed mock device to on or off."""
    result = execute_ha_action(
        ActionRequest(
            domain=_entity_domain(entity_id),
            service="turn_on" if state == "on" else "turn_off",
            entity_id=entity_id,
            require_verification=True,
            require_mock_device=True,
            expected_state=state,
        )
    )
    return result["ha_response"]


def toggle_mock_device(entity_id: str) -> dict[str, Any]:
    """Toggle a backend-managed mock device through the shared action path."""
    result = execute_ha_action(
        ActionRequest(
            domain=_entity_domain(entity_id),
            service="toggle",
            entity_id=entity_id,
            require_verification=True,
            require_mock_device=True,
        )
    )
    return result["ha_response"]
