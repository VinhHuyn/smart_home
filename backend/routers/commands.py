from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from schemas.ha import CommandRequest
from services.command_service import execute_command

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("")
def command(request: CommandRequest) -> dict[str, Any]:
    return execute_command(request)
