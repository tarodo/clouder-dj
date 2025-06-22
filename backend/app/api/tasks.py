from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.broker import broker

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/status/{task_id}", response_model=dict, dependencies=[Depends(get_current_user)]
)
async def get_task_status(task_id: str) -> dict[str, Any]:
    """Retrieves the current status, progress, and result of a background task."""
    result = await broker.result_backend.get_result(task_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found.",
        )
    return dict(result)
