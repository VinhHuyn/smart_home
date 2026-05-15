from __future__ import annotations

from fastapi import Depends, FastAPI

from core.auth import require_api_key
from routers import commands, devices, health, mock_devices, services
from services.mock_device_service import seed_default_mock_devices

app = FastAPI(
    title="Smart Home Home Assistant Backend",
    description=(
        "FastAPI bridge for Home Assistant states, services, commands, "
        "and mock devices."
    ),
    version="1.1.0",
)

app.include_router(health.router)
app.include_router(devices.router, dependencies=[Depends(require_api_key)])
app.include_router(services.router, dependencies=[Depends(require_api_key)])
app.include_router(commands.router, dependencies=[Depends(require_api_key)])
app.include_router(mock_devices.router, dependencies=[Depends(require_api_key)])


@app.on_event("startup")
def seed_mock_devices_on_startup() -> None:
    """Seed mock devices without blocking startup when HA is unavailable."""
    try:
        seed_default_mock_devices()
    except Exception:
        pass
