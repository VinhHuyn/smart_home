from __future__ import annotations

from fastapi import HTTPException, status

from ha_client import HomeAssistantError


def ha_error_response(exc: HomeAssistantError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
        detail={"message": str(exc), "ha_status_code": exc.status_code, "ha_payload": exc.payload},
    )
