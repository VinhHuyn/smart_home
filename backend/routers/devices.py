from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response, status

import ha_client
from core.errors import ha_error_response
from ha_client import HomeAssistantError
from schemas.ha import StateUpdate

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("")
def devices() -> list[dict[str, Any]]:
    try:
        return ha_client.get_states()
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.get("/{entity_id}")
def device(entity_id: str) -> dict[str, Any]:
    try:
        return ha_client.get_state(entity_id)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.put("/{entity_id}")
def update_device_legacy(entity_id: str, state: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return ha_client.set_state(entity_id, state, attributes)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.post("/{entity_id}/state")
def update_device_state(entity_id: str, request: StateUpdate) -> dict[str, Any]:
    try:
        return ha_client.set_state(entity_id, request.state, request.attributes)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(entity_id: str) -> Response:
    try:
        ha_client.delete_state(entity_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc
