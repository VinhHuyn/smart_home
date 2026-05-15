from __future__ import annotations

from typing import Any

from core.time import utc_now
from ha_client import HomeAssistantError
from schemas.ha import CommandRequest
from services.action_service import ActionRequest, build_service_data, execute_ha_action


def command_service_data(intent) -> dict[str, Any]:
    return build_service_data(entity_id=intent.entity_id, area_id=intent.area_id, service_data=intent.service_data)


def _failed_command_response(request: CommandRequest, exc: HomeAssistantError) -> dict[str, Any]:
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


def execute_command(request: CommandRequest) -> dict[str, Any]:
    service_data = command_service_data(request.intent)
    action_request = ActionRequest(
        domain=request.intent.domain,
        service=request.intent.service,
        entity_id=request.intent.entity_id,
        service_data=service_data,
        require_verification=request.execution_policy.require_verification,
        expected_state=request.execution_policy.expected_state,
        dry_run=request.execution_policy.dry_run,
    )

    try:
        action_result = execute_ha_action(action_request)
    except HomeAssistantError as exc:
        return _failed_command_response(request, exc)

    return {
        "schema_version": request.schema_version,
        "message_type": "ha.command.result",
        "request_id": request.request_id,
        "timestamp": utc_now(),
        "executor": {"agent": "smart-home-ha-backend"},
        **action_result,
    }
