from __future__ import annotations

from typing import Any

import ha_client
from core.time import utc_now
from schemas.ha import ServiceCallRequest
from services.command_service import expected_state_for_service


def call_service(domain: str, service: str, request: ServiceCallRequest) -> dict[str, Any]:
    service_data = dict(request.service_data)
    if request.entity_id is not None:
        service_data["entity_id"] = request.entity_id

    before = ha_client.get_state(request.entity_id) if isinstance(request.entity_id, str) else None
    result = ha_client.call_service(domain, service, service_data)
    after = ha_client.get_state(request.entity_id) if isinstance(request.entity_id, str) else None

    expected = expected_state_for_service(service, request.expected_state)
    verified = True
    if request.require_verification and expected is not None and after is not None:
        verified = after.get("state") == expected

    return {
        "status": "success" if verified else "verification_failed",
        "ha_call": {"domain": domain, "service": service, "service_data": service_data},
        "ha_response": result,
        "verification": {
            "performed": request.require_verification,
            "state_before": before.get("state") if before else None,
            "state_after": after.get("state") if after else None,
            "expected_state": expected,
            "verified": verified,
            "verified_at": utc_now() if request.require_verification else None,
        },
    }
