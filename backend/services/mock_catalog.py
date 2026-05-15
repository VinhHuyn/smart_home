from __future__ import annotations

"""Mock device catalog used for dev/staging seed and docs examples."""

from schemas.ha import MockDeviceCreate


DEFAULT_MOCK_DEVICES: tuple[MockDeviceCreate, ...] = (
    MockDeviceCreate(
        entity_id="light.mock_bedroom_lamp",
        name="Mock Bedroom Lamp",
        domain="light",
        room="bedroom",
        initial_state="off",
        attributes={"room": "bedroom", "device_type": "lamp"},
    ),
    MockDeviceCreate(
        entity_id="light.mock_living_room_lamp",
        name="Mock Living Room Lamp",
        domain="light",
        room="living_room",
        initial_state="off",
        attributes={"room": "living_room", "device_type": "lamp"},
    ),
    MockDeviceCreate(
        entity_id="switch.mock_kitchen_plug",
        name="Mock Kitchen Plug",
        domain="switch",
        room="kitchen",
        initial_state="off",
        attributes={"room": "kitchen", "device_type": "plug"},
    ),
    MockDeviceCreate(
        entity_id="light.mock_bathroom_light",
        name="Mock Bathroom Light",
        domain="light",
        room="bathroom",
        initial_state="off",
        attributes={"room": "bathroom", "device_type": "ceiling_light"},
    ),
)
