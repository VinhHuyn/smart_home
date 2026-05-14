from __future__ import annotations

from fastapi import FastAPI

from routers import commands, devices, health, mock_devices, services
from services.mock_device_service import seed_default_mock_devices

app = FastAPI(
    title="Smart Home Home Assistant Backend",
    description="FastAPI bridge for Home Assistant states, services, commands, and mock devices.",
    version="1.1.0",
)

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(services.router)
app.include_router(commands.router)
app.include_router(mock_devices.router)


@app.on_event("startup")
def seed_mock_devices_on_startup() -> None:
    try:
        seed_default_mock_devices()
    except Exception:
        # Startup must not fail when HA is offline; /ha/health exposes connectivity.
        pass
