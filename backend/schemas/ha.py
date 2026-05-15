from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

DEFAULT_MOCK_DEVICE_ID = "light.mock_bedroom_lamp"


class StateUpdate(BaseModel):
    """Request body for setting one HA entity state."""

    state: str = Field(..., examples=["on", "off"])
    attributes: dict[str, Any] = Field(default_factory=dict)


class ServiceCallRequest(BaseModel):
    """Request body for direct HA service calls."""

    entity_id: str | list[str] | None = None
    service_data: dict[str, Any] = Field(default_factory=dict)
    require_verification: bool = False
    expected_state: str | None = None


class MockDeviceCreate(BaseModel):
    """Request body for creating a backend-managed mock device."""

    entity_id: str = Field(..., examples=[DEFAULT_MOCK_DEVICE_ID])
    name: str = Field(..., examples=["Mock Bedroom Lamp"])
    domain: str = Field(default="light", examples=["light"])
    room: str = Field(default="unassigned", examples=["bedroom"])
    initial_state: str = Field(default="off", examples=["off"])
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entity_id")
    @classmethod
    def validate_entity_id(cls, value: str) -> str:
        """Require Home Assistant-style domain.entity IDs."""
        if "." not in value:
            raise ValueError(
                "entity_id must include a Home Assistant domain, "
                "e.g. light.mock_lamp"
            )
        return value


class CommandIntent(BaseModel):
    """Action target extracted from a command request."""

    domain: str = Field(..., examples=["light"])
    service: str = Field(..., examples=["turn_off"])
    entity_id: str | list[str] | None = Field(
        default=None,
        examples=[DEFAULT_MOCK_DEVICE_ID],
    )
    area_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    service_data: dict[str, Any] = Field(default_factory=dict)


class ExecutionPolicy(BaseModel):
    """Execution controls for dry runs and verification."""

    dry_run: bool = False
    require_verification: bool = True
    verify_timeout_sec: int = 10
    max_retries: int = 0
    idempotency_key: str | None = None
    expected_state: str | None = None


class CommandRequest(BaseModel):
    """Command envelope accepted by the backend command endpoint."""

    schema_version: str = "ha-bridge.v1"
    message_type: Literal["ha.command.request"] = "ha.command.request"
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex}")
    timestamp: str | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    target: dict[str, Any] = Field(default_factory=dict)
    user_context: dict[str, Any] = Field(default_factory=dict)
    intent: CommandIntent
    execution_policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    safety: dict[str, Any] = Field(default_factory=dict)
