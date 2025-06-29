from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.collection import BeatportCollectionRequest
from app.tasks import (
    collect_bp_tracks_task,
    enrich_spotify_artist_data_task,
    enrich_spotify_data_task,
)

router = APIRouter(prefix="/collect", tags=["collection"])


@router.post(
    "/beatport/collect", status_code=202, dependencies=[Depends(get_current_user)]
)
async def run_beatport_collection_task(params: BeatportCollectionRequest):
    """Endpoint to start a Beatport collection task."""
    task = await collect_bp_tracks_task.kiq(
        date_from=params.date_from.isoformat(),
        date_to=params.date_to.isoformat(),
    )
    return {"task_id": task.task_id}


@router.post(
    "/spotify/enrich", status_code=202, dependencies=[Depends(get_current_user)]
)
async def run_spotify_enrichment_task(similarity_threshold: int = 80):
    """Endpoint to start a Spotify enrichment task for all tracks."""
    task = await enrich_spotify_data_task.kiq(similarity_threshold=similarity_threshold)
    return {"task_id": task.task_id}


@router.post(
    "/spotify/enrich-artists",
    status_code=202,
    dependencies=[Depends(get_current_user)],
)
async def run_spotify_artist_enrichment_task():
    """Endpoint to start a Spotify enrichment task for all artists."""
    task = await enrich_spotify_artist_data_task.kiq()
    return {"task_id": task.task_id}
