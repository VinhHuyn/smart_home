from __future__ import annotations

from typing import Any

import ha_client
from core.time import utc_now
from ha_client import HomeAssistantError
from schemas.ha import CommandIntent, CommandRequest


def expected_state_for_service(service: str, explicit_expected_state: str | None = None) -> str | None:
    if explicit_expected_state:
        return explicit_expected_state
    if service == "turn_on":
        return "on"
    if service == "turn_off":
        return "off"
    return None


def command_service_data(intent: CommandIntent) -> dict[str, Any]:
    payload = dict(intent.service_data)
    if intent.entity_id is not None:
        payload["entity_id"] = intent.entity_id
    if intent.area_id is not None and "area_id" not in payload:
        payload["area_id"] = intent.area_id
    return payload


def _is_mock_power_command(before: dict[str, Any] | None, request: CommandRequest, entity_id: str | None) -> bool:
    return bool(
        before
        and before.get("attributes", {}).get("mock_device") is True
        and request.intent.domain in {"light", "switch"}
        and request.intent.service in {"turn_on", "turn_off", "toggle"}
        and entity_id is not None
    )


def execute_command(request: CommandRequest) -> dict[str, Any]:
    expected = expected_state_for_service(request.intent.service, request.execution_policy.expected_state)
    service_data = command_service_data(request.intent)
    entity_id = request.intent.entity_id if isinstance(request.intent.entity_id, str) else None

    if request.execution_policy.dry_run:
        return {
            "schema_version": request.schema_version,
            "message_type": "ha.command.result",
            "request_id": request.request_id,
            "timestamp": utc_now(),
            "status": "dry_run",
            "ha_call": {
                "domain": request.intent.domain,
                "service": request.intent.service,
                "service_data": service_data,
            },
            "verification": {"performed": False, "verified": None},
        }

    before = None
    after = None
    try:
        if entity_id:
            before = ha_client.get_state(entity_id)

        if _is_mock_power_command(before, request, entity_id) and entity_id is not None and before is not None:
            if request.intent.service == "toggle":
                next_state = "off" if before.get("state") == "on" else "on"
            else:
                next_state = "on" if request.intent.service == "turn_on" else "off"
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
            ha_response = ha_client.call_service(request.intent.domain, request.intent.service, service_data)
            if entity_id:
                after = ha_client.get_state(entity_id)
    except HomeAssistantError as exc:
        return {
            "schema_version": request.schema_version,
            "message_type": "ha.command.result",
            "request_id": request.request_id,
            "timestamp": utc_now(),
            "status": "failed",
            "error": {
                "code": "HOME_ASSISTANT_API_ERROR",
                "message": str(exc),
                "ha_status_code": exc.status_code,
                "retryable": exc.status_code is None or exc.status_code >= 500,
                "payload": exc.payload,
            },
            "verification": {"performed": False, "verified": False},
        }

    verification_required = request.execution_policy.require_verification
    verified = True
    if verification_required and expected is not None and after is not None:
        verified = after.get("state") == expected

    return {
        "schema_version": request.schema_version,
        "message_type": "ha.command.result",
        "request_id": request.request_id,
        "timestamp": utc_now(),
        "executor": {"agent": "smart-home-ha-backend"},
        "status": "success" if verified else "verification_failed",
        "ha_call": {
            "domain": request.intent.domain,
            "service": request.intent.service,
            "entity_id": request.intent.entity_id,
            "service_data": service_data,
        },
        "ha_response": ha_response,
        "verification": {
            "performed": verification_required,
            "state_before": before.get("state") if before else None,
            "state_after": after.get("state") if after else None,
            "expected_state": expected,
            "verified": verified,
            "verified_at": utc_now() if verification_required else None,
        },
    }
