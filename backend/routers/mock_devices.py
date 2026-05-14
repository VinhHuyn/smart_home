from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status

from core.errors import ha_error_response
from ha_client import HomeAssistantError
from schemas.ha import MockDeviceCreate
from services.mock_device_service import (
    create_or_update_mock_device,
    default_mock_devices_by_room,
    list_mock_devices,
    set_mock_device_power,
    toggle_mock_device,
)

router = APIRouter(prefix="/mock", tags=["mock devices"])


@router.get("/rooms")
def mock_rooms() -> dict[str, list[dict[str, Any]]]:
    return default_mock_devices_by_room()


@router.get("/devices")
def mock_devices() -> list[dict[str, Any]]:
    try:
        return list_mock_devices()
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.post("/devices", status_code=status.HTTP_201_CREATED)
def register_mock_device(device: MockDeviceCreate) -> dict[str, Any]:
    try:
        return create_or_update_mock_device(device)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.post("/devices/{entity_id}/turn_on")
def turn_on_mock_device(entity_id: str) -> dict[str, Any]:
    try:
        return set_mock_device_power(entity_id, "on")
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.post("/devices/{entity_id}/turn_off")
def turn_off_mock_device(entity_id: str) -> dict[str, Any]:
    try:
        return set_mock_device_power(entity_id, "off")
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.post("/devices/{entity_id}/toggle")
def toggle_mock_device_route(entity_id: str) -> dict[str, Any]:
    try:
        return toggle_mock_device(entity_id)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc
