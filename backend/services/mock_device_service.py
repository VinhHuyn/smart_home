from __future__ import annotations

from typing import Any, Literal

import ha_client
from schemas.ha import MockDeviceCreate
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


def set_mock_device_power(entity_id: str, state: Literal["on", "off"]) -> dict[str, Any]:
    name = entity_id.split(".", 1)[1].replace("_", " ").title()
    domain = entity_id.split(".", 1)[0]
    return ha_client.set_state(
        entity_id,
        state,
        {
            "friendly_name": name,
            "supported_features": 0,
            "mock_device": True,
            "managed_by": "smart-home-ha-backend",
            "domain": domain,
        },
    )


def toggle_mock_device(entity_id: str) -> dict[str, Any]:
    current = ha_client.get_state(entity_id)
    next_state: Literal["on", "off"] = "off" if current.get("state") == "on" else "on"
    return set_mock_device_power(entity_id, next_state)
