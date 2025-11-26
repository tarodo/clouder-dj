from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_uow
from app.db.uow import AbstractUnitOfWork
from app.schemas.collection import BeatportCollectionRequest
from app.services.collection import CollectionService
from app.services.data_processing import DataProcessingService
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
        bp_token=params.bp_token,
        style_id=params.style_id,
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


class CollectionStatsStyle(BaseModel):
    id: int
    name: str
    track_count: int


class CollectionStats(BaseModel):
    total_artists: int
    total_releases: int
    styles: List[CollectionStatsStyle]


@router.get(
    "/stats", response_model=CollectionStats, dependencies=[Depends(get_current_user)]
)
async def get_stats(uow: AbstractUnitOfWork = Depends(get_uow)):
    """Get database statistics."""
    data_processing = DataProcessingService(
        db=uow.session,
        artist_repo=uow.artists,
        label_repo=uow.labels,
        release_repo=uow.releases,
        track_repo=uow.tracks,
        external_data_repo=uow.external_data,
    )

    service = CollectionService(
        external_data_repo=uow.external_data,
        data_processing_service=data_processing,
        style_repo=uow.styles,
        artist_repo=uow.artists,
        release_repo=uow.releases,
    )
    return await service.get_database_stats()
