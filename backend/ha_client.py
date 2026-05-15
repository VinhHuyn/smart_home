"""Home Assistant REST API client used by the FastAPI backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_HA_URL = "http://localhost:8123"
DEFAULT_HA_TIMEOUT_SEC = "10"


class HomeAssistantError(RuntimeError):
    """Raised when Home Assistant returns an error or cannot be reached."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
    ):
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
        """Load HA settings while keeping legacy HASS_* fallback keys."""
        url = os.getenv("HA_URL") or os.getenv("HASS_URL", DEFAULT_HA_URL)
        token = os.getenv("HA_TOKEN") or os.getenv("HASS_TOKEN", "")
        timeout_sec = float(
            os.getenv("HA_TIMEOUT_SEC")
            or os.getenv("HASS_TIMEOUT_SEC", DEFAULT_HA_TIMEOUT_SEC)
        )
        return cls(url=url.rstrip("/"), token=token, timeout_sec=timeout_sec)


class HomeAssistantClient:
    def __init__(self, settings: HomeAssistantSettings | None = None):
        self.settings = settings or HomeAssistantSettings.from_env()

    @property
    def headers(self) -> dict[str, str]:
        """Build JSON headers with optional bearer auth."""
        headers = {"Content-Type": "application/json"}
        if self.settings.token:
            headers["Authorization"] = f"Bearer {self.settings.token}"
        return headers

    def _url(self, path: str) -> str:
        """Build an absolute HA API URL from a path."""
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.settings.url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send one HA REST request and return parsed response content."""
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
        """Return HA API health response."""
        response = self._request("GET", "/api/")
        if isinstance(response, dict):
            return response
        return {"message": response}

    def get_config(self) -> dict[str, Any]:
        """Return Home Assistant configuration metadata."""
        return self._request("GET", "/api/config")

    def get_states(self) -> list[dict[str, Any]]:
        """Return all Home Assistant entity states."""
        return self._request("GET", "/api/states")

    def get_state(self, entity_id: str) -> dict[str, Any]:
        """Return one Home Assistant entity state."""
        return self._request("GET", f"/api/states/{entity_id}")

    def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Set one Home Assistant entity state."""
        return self._request(
            "POST",
            f"/api/states/{entity_id}",
            json={"state": state, "attributes": attributes or {}},
        )

    def delete_state(self, entity_id: str) -> bool:
        """Delete one Home Assistant entity state."""
        self._request("DELETE", f"/api/states/{entity_id}")
        return True

    def get_services(self) -> list[dict[str, Any]]:
        """Return Home Assistant service domains."""
        return self._request("GET", "/api/services")

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
    ) -> Any:
        """Call one Home Assistant service endpoint."""
        return self._request(
            "POST",
            f"/api/services/{domain}/{service}",
            json=service_data or {},
        )


_default_client = HomeAssistantClient()


# Older router code imports module functions, so keep these thin wrappers.
def get_states() -> list[dict[str, Any]]:
    """Return all Home Assistant entity states."""
    return _default_client.get_states()


def get_state(entity_id: str) -> dict[str, Any]:
    """Return one Home Assistant entity state."""
    return _default_client.get_state(entity_id)


def set_state(
    entity_id: str,
    state: str,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Set one Home Assistant entity state."""
    return _default_client.set_state(entity_id, state, attributes)


def delete_state(entity_id: str) -> bool:
    """Delete one Home Assistant entity state."""
    return _default_client.delete_state(entity_id)


def get_config() -> dict[str, Any]:
    """Return Home Assistant configuration metadata."""
    return _default_client.get_config()


def get_services() -> list[dict[str, Any]]:
    """Return Home Assistant service domains."""
    return _default_client.get_services()


def call_service(
    domain: str,
    service: str,
    service_data: dict[str, Any] | None = None,
) -> Any:
    """Call one Home Assistant service endpoint."""
    return _default_client.call_service(domain, service, service_data)
