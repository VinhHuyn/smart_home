from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import ha_client
from core.time import utc_now
from ha_client import HomeAssistantError
from services.mock_action_helpers import (
    is_mock_device,
    is_mock_power_action,
    mock_power_next_state,
)


@dataclass(frozen=True)
class ActionRequest:
    """Describe one HA action before transport-specific execution."""

    domain: str
    service: str
    entity_id: str | list[str] | None = None
    service_data: dict[str, Any] = field(default_factory=dict)
    require_verification: bool = True
    expected_state: str | None = None
    dry_run: bool = False
    require_mock_device: bool = False


def expected_state_for_service(
    service: str,
    explicit_expected_state: str | None = None,
) -> str | None:
    """Infer the expected state for common power services."""
    if explicit_expected_state:
        return explicit_expected_state
    if service == "turn_on":
        return "on"
    if service == "turn_off":
        return "off"
    return None


def build_service_data(
    *,
    entity_id: str | list[str] | None = None,
    area_id: str | None = None,
    service_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge entity, area, and caller-provided service payload fields."""
    payload = dict(service_data or {})
    if entity_id is not None:
        payload["entity_id"] = entity_id
    if area_id is not None and "area_id" not in payload:
        payload["area_id"] = area_id
    return payload


def _single_entity_id(entity_id: str | list[str] | None) -> str | None:
    """Return the entity ID only when verification can target one entity."""
    return entity_id if isinstance(entity_id, str) else None


def execute_ha_action(request: ActionRequest) -> dict[str, Any]:
    """Execute one HA action and return HA call plus verification metadata."""
    entity_id = _single_entity_id(request.entity_id)
    service_data = build_service_data(
        entity_id=request.entity_id,
        service_data=request.service_data,
    )
    expected = expected_state_for_service(request.service, request.expected_state)

    if request.dry_run:
        return {
            "status": "dry_run",
            "ha_call": {
                "domain": request.domain,
                "service": request.service,
                "service_data": service_data,
            },
            "ha_response": None,
            "verification": {"performed": False, "verified": None},
        }

    before = ha_client.get_state(entity_id) if entity_id else None
    if request.require_mock_device and not is_mock_device(before):
        raise HomeAssistantError(
            f"Mock device not found or not managed by this backend: {entity_id}",
            status_code=404,
            payload={"entity_id": entity_id},
        )

    if expected is None and request.service == "toggle" and before is not None:
        expected = mock_power_next_state(request.service, before.get("state"))

    if (
        is_mock_power_action(
            before,
            domain=request.domain,
            service=request.service,
            entity_id=request.entity_id,
        )
        and entity_id is not None
        and before is not None
    ):
        next_state = mock_power_next_state(request.service, before.get("state"))
        ha_response = ha_client.set_state(
            entity_id,
            next_state,
            {
                **before.get("attributes", {}),
                "mock_device": True,
                "managed_by": "smart-home-ha-backend",
            },
        )
        after = ha_response
    else:
        ha_response = ha_client.call_service(
            request.domain,
            request.service,
            service_data,
        )
        after = ha_client.get_state(entity_id) if entity_id else None

    verification_performed = (
        request.require_verification and expected is not None and after is not None
    )
    verified: bool | None = None
    if verification_performed and after is not None:
        verified = after.get("state") == expected

    return {
        "status": "verification_failed" if verified is False else "success",
        "ha_call": {
            "domain": request.domain,
            "service": request.service,
            "entity_id": request.entity_id,
            "service_data": service_data,
        },
        "ha_response": ha_response,
        "verification": {
            "performed": verification_performed,
            "state_before": before.get("state") if before else None,
            "state_after": after.get("state") if after else None,
            "expected_state": expected,
            "verified": verified,
            "verified_at": utc_now() if verification_performed else None,
        },
    }
