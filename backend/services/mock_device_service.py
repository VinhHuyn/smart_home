from __future__ import annotations

from typing import Any, Literal

import ha_client
from schemas.ha import MockDeviceCreate
from services.action_service import ActionRequest, execute_ha_action
from services.default_devices import DEFAULT_MOCK_DEVICES


def build_mock_attributes(device: MockDeviceCreate) -> dict[str, Any]:
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
    return ha_client.set_state(device.entity_id, device.initial_state, build_mock_attributes(device))


def seed_default_mock_devices() -> list[dict[str, Any]]:
    seeded: list[dict[str, Any]] = []
    for device in DEFAULT_MOCK_DEVICES:
        seeded.append(create_or_update_mock_device(device))
    return seeded


def default_mock_devices_by_room() -> dict[str, list[dict[str, Any]]]:
    rooms: dict[str, list[dict[str, Any]]] = {}
    for device in DEFAULT_MOCK_DEVICES:
        rooms.setdefault(device.room, []).append(device.model_dump())
    return rooms


def list_mock_devices() -> list[dict[str, Any]]:
    states = ha_client.get_states()
    return [item for item in states if item.get("attributes", {}).get("mock_device") is True]


def _entity_domain(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def set_mock_device_power(entity_id: str, state: Literal["on", "off"]) -> dict[str, Any]:
    """Compatibility wrapper for mock power endpoints.

    The actual turn_on/turn_off + verification behavior now runs through the
    canonical action executor used by /commands and /services.
    """

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
