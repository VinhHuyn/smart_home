"""Home Assistant REST API client used by the FastAPI backend.

The backend intentionally talks to Home Assistant through its official REST API:
- GET /api/
- GET /api/config
- GET/POST/DELETE /api/states/{entity_id}
- GET /api/services
- POST /api/services/{domain}/{service}

Virtual/mock devices are represented as HA entity states created through
/api/states/{entity_id}. This is enough for backend testing without physical
hardware. Real devices can later use the same command API but point to their
actual entity_id values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class HomeAssistantError(RuntimeError):
    """Raised when Home Assistant returns an error or cannot be reached."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(frozen=True)
class HomeAssistantSettings:
    url: str
    token: str
    timeout_sec: float = 10.0

    @classmethod
    def from_env(cls) -> "HomeAssistantSettings":
        # Prefer HA_* for this backend. HASS_* remains a backwards-compatible
        # fallback for older Orin cutover configs, but commented-out HASS_* keys
        # should not override the active HA_* target/token pair.
        url = os.getenv("HA_URL") or os.getenv("HASS_URL", "http://localhost:8123")
        token = os.getenv("HA_TOKEN") or os.getenv("HASS_TOKEN", "")
        timeout_sec = float(os.getenv("HA_TIMEOUT_SEC") or os.getenv("HASS_TIMEOUT_SEC", "10"))
        return cls(url=url.rstrip("/"), token=token, timeout_sec=timeout_sec)


class HomeAssistantClient:
    def __init__(self, settings: HomeAssistantSettings | None = None):
        self.settings = settings or HomeAssistantSettings.from_env()

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.token:
            headers["Authorization"] = f"Bearer {self.settings.token}"
        return headers

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.settings.url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = requests.request(
                method,
                self._url(path),
                headers=self.headers,
                timeout=self.settings.timeout_sec,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise HomeAssistantError(f"Could not reach Home Assistant: {exc}") from exc

        payload: Any
        if response.content:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
        else:
            payload = None

        if response.status_code >= 400:
            raise HomeAssistantError(
                f"Home Assistant API error {response.status_code}",
                status_code=response.status_code,
                payload=payload,
            )
        return payload

    def health(self) -> dict[str, Any]:
        response = self._request("GET", "/api/")
        if isinstance(response, dict):
            return response
        return {"message": response}

    def get_config(self) -> dict[str, Any]:
        return self._request("GET", "/api/config")

    def get_states(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/states")

    def get_state(self, entity_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/states/{entity_id}")

    def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/states/{entity_id}",
            json={"state": state, "attributes": attributes or {}},
        )

    def delete_state(self, entity_id: str) -> bool:
        self._request("DELETE", f"/api/states/{entity_id}")
        return True

    def get_services(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/services")

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
    ) -> Any:
        return self._request(
            "POST",
            f"/api/services/{domain}/{service}",
            json=service_data or {},
        )


_default_client = HomeAssistantClient()


# Backwards-compatible function API used by earlier main.py versions.
def get_states() -> list[dict[str, Any]]:
    return _default_client.get_states()


def get_state(entity_id: str) -> dict[str, Any]:
    return _default_client.get_state(entity_id)


def set_state(entity_id: str, state: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
    return _default_client.set_state(entity_id, state, attributes)


def delete_state(entity_id: str) -> bool:
    return _default_client.delete_state(entity_id)


def get_config() -> dict[str, Any]:
    return _default_client.get_config()


def get_services() -> list[dict[str, Any]]:
    return _default_client.get_services()


def call_service(domain: str, service: str, service_data: dict[str, Any] | None = None) -> Any:
    return _default_client.call_service(domain, service, service_data)
