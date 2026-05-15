from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


AUTH_ENV_VAR = "SMART_HOME_API_KEY"


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = os.getenv(AUTH_ENV_VAR)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "API authentication is not configured. "
                f"Set {AUTH_ENV_VAR} before exposing protected endpoints."
            ),
        )

    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
