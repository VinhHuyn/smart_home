from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

import ha_client
from core.errors import ha_error_response
from ha_client import HomeAssistantError
from schemas.ha import ServiceCallRequest
from services.ha_service import call_service as call_ha_service

router = APIRouter(prefix="/services", tags=["services"])


@router.get("")
def services() -> list[dict[str, Any]]:
    try:
        return ha_client.get_services()
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc


@router.get("/{domain}")
def services_by_domain(domain: str) -> dict[str, Any]:
    try:
        for item in ha_client.get_services():
            if item.get("domain") == domain:
                return item
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc
    raise HTTPException(status_code=404, detail=f"Service domain not found: {domain}")


@router.post("/{domain}/{service}")
def call_service(domain: str, service: str, request: ServiceCallRequest) -> dict[str, Any]:
    try:
        return call_ha_service(domain, service, request)
    except HomeAssistantError as exc:
        raise ha_error_response(exc) from exc
