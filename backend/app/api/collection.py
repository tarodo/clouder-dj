from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.collection import BeatportCollectionRequest
from app.tasks import collect_bp_tracks_task

router = APIRouter(prefix="/collect", tags=["collection"])


@router.post("/beatport", status_code=202, dependencies=[Depends(get_current_user)])
async def run_beatport_collection_task(params: BeatportCollectionRequest):
    """Endpoint to start a beatport collection task."""
    task = await collect_bp_tracks_task.kiq(
        bp_token=params.bp_token,
        style_id=params.style_id,
        date_from=params.date_from.isoformat(),
        date_to=params.date_to.isoformat(),
    )
    return {"task_id": task.task_id}
