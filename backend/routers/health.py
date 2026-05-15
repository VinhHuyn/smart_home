from __future__ import annotations
from typing import Any
from fastapi import APIRouter
import ha_client
from core.errors import ha_error_response
from ha_client import HomeAssistantError

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, Any]:
    """Return backend status and advertised capabilities."""
    return {
        "service": "smart-home-ha-backend",
        "status": "running",
        "architecture": "routers + services + schemas + core",
        "capabilities": [
            "/ha/health",
            "/ha/config",
            "/devices",
            "/services",
            "/services/{domain}/{service}",
            "/commands",
            "/mock/devices",
            "/mock/rooms",
        ],
    }


@router.get("/ha/health")
def ha_health() -> dict[str, Any]:
    """Return Home Assistant API connectivity status."""
    try:
        return {
            "status": "connected",
            "home_assistant": ha_client._default_client.health(),
        }
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.get("/ha/config")
def ha_config() -> dict[str, Any]:
    """Return Home Assistant configuration metadata."""
    try:
        return ha_client.get_config()
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc
