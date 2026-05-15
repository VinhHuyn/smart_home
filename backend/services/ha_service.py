from __future__ import annotations
from typing import Any
from schemas.ha import ServiceCallRequest
from services.action_service import ActionRequest, execute_ha_action


def call_service(
    domain: str,
    service: str,
    request: ServiceCallRequest,
) -> dict[str, Any]:
    """Execute a direct HA service call through the shared action path."""
    return execute_ha_action(
        ActionRequest(
            domain=domain,
            service=service,
            entity_id=request.entity_id,
            service_data=request.service_data,
            require_verification=request.require_verification,
            expected_state=request.expected_state,
        )
    )
