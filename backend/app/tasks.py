import structlog
from typing import Any, Dict

from taskiq import TaskiqContext, TaskiqDepends

from app.broker import broker
from app.db.session import AsyncSessionLocal
from app.db.uow import SqlAlchemyUnitOfWork
from app.repositories import (
    ArtistRepository,
    ExternalDataRepository,
    LabelRepository,
    ReleaseRepository,
    TrackRepository,
)
from app.services.collection import CollectionService
from app.services.data_processing import DataProcessingService
from app.services.enrichment import EnrichmentService

log = structlog.get_logger()


async def _report_progress(task_id: str, progress: Dict[str, Any]) -> None:
    """Safely report task progress to result backend."""
    try:
        await broker.result_backend.report_progress(task_id, progress)
    except Exception:
        log.exception("Failed to report task progress", task_id=task_id, progress=progress)


async def _set_result(task_id: str, result: Dict[str, Any]) -> None:
    """Safely set final task result to result backend."""
    try:
        await broker.result_backend.set_result(task_id, result)
    except Exception:
        log.exception("Failed to set task result", task_id=task_id, result=result)


@broker.task
async def collect_bp_tracks_task(
    *,
    bp_token: str,
    style_id: int,
    date_from: str,
    date_to: str,
    ctx: TaskiqContext = TaskiqDepends(),
) -> Dict[str, Any]:
    """
    Task: Collect Beatport tracks and process them into normalized entities.
    """
    task_id = ctx.task_id
    await _report_progress(task_id, {"phase": "start", "processed": 0, "failed": 0, "total": 0})

    try:
        uow = SqlAlchemyUnitOfWork(AsyncSessionLocal)
        async with uow:
            # Initialize services with repositories from UoW
            external_data_repo: ExternalDataRepository = uow.external_data
            data_processing_service = DataProcessingService(
                db=uow.session,
                artist_repo=ArtistRepository(uow.session),
                label_repo=LabelRepository(uow.session),
                release_repo=ReleaseRepository(uow.session),
                track_repo=TrackRepository(uow.session),
                external_data_repo=external_data_repo,
            )
            collection_service = CollectionService(
                external_data_repo=external_data_repo,
                data_processing_service=data_processing_service,
            )

            log.info(
                "Starting Beatport collection task",
                style_id=style_id,
                date_from=date_from,
                date_to=date_to,
                task_id=task_id,
            )
            # Phase 1: Collect raw data into external_data
            await collection_service.collect_beatport_tracks_raw(
                bp_token=bp_token,
                style_id=style_id,
                date_from=date_from,
                date_to=date_to,
            )
            await _report_progress(task_id, {"phase": "collect_raw_done"})

            # Phase 2: Process unprocessed records in batches, reporting progress
            async def progress_cb(progress: Dict[str, Any]) -> None:
                await _report_progress(task_id, {"phase": "processing", **progress})

            summary = await collection_service.process_unprocessed_beatport_tracks(
                batch_progress_callback=progress_cb
            )

        result: Dict[str, Any] = {
            "status": "success",
            "task": "collect_bp_tracks",
            "summary": summary,
        }
        await _set_result(task_id, result)
        return result

    except Exception as exc:
        log.exception("Beatport collection task failed", task_id=task_id)
        result = {
            "status": "failure",
            "task": "collect_bp_tracks",
            "error": str(exc),
        }
        await _set_result(task_id, result)
        return result


@broker.task
async def enrich_spotify_data_task(
    *,
    similarity_threshold: int = 80,
    ctx: TaskiqContext = TaskiqDepends(),
) -> Dict[str, Any]:
    """
    Task: Enrich tracks with Spotify data using ISRC and fuzzy artist matching.
    """
    task_id = ctx.task_id
    await _report_progress(task_id, {"phase": "start", "processed": 0, "total": 0, "found": 0, "not_found": 0})

    try:
        uow = SqlAlchemyUnitOfWork(AsyncSessionLocal)
        async with uow:
            enrichment_service = EnrichmentService(
                db=uow.session,
                artist_repo=ArtistRepository(uow.session),
                track_repo=TrackRepository(uow.session),
                external_data_repo=ExternalDataRepository(uow.session),
            )

            async def progress_cb(progress: Dict[str, Any]) -> None:
                await _report_progress(task_id, {"phase": "enrich_tracks", **progress})

            log.info(
                "Starting Spotify track enrichment",
                similarity_threshold=similarity_threshold,
                task_id=task_id,
            )
            summary = await enrichment_service.enrich_tracks_with_spotify_data(
                progress_callback=progress_cb,
                similarity_threshold=similarity_threshold,
            )

        result: Dict[str, Any] = {
            "status": "success",
            "task": "enrich_spotify_tracks",
            "summary": summary,
        }
        await _set_result(task_id, result)
        return result

    except Exception as exc:
        log.exception("Spotify track enrichment task failed", task_id=task_id)
        result = {
            "status": "failure",
            "task": "enrich_spotify_tracks",
            "error": str(exc),
        }
        await _set_result(task_id, result)
        return result


@broker.task
async def enrich_spotify_artist_data_task(
    *,
    ctx: TaskiqContext = TaskiqDepends(),
) -> Dict[str, Any]:
    """
    Task: Enrich artists with Spotify data using fuzzy matching via track data.
    """
    task_id = ctx.task_id
    await _report_progress(task_id, {"phase": "start", "processed": 0, "total": 0, "found": 0, "not_found": 0})

    try:
        uow = SqlAlchemyUnitOfWork(AsyncSessionLocal)
        async with uow:
            enrichment_service = EnrichmentService(
                db=uow.session,
                artist_repo=ArtistRepository(uow.session),
                track_repo=TrackRepository(uow.session),
                external_data_repo=ExternalDataRepository(uow.session),
            )

            async def progress_cb(progress: Dict[str, Any]) -> None:
                await _report_progress(task_id, {"phase": "enrich_artists", **progress})

            log.info("Starting Spotify artist enrichment", task_id=task_id)
            summary = await enrichment_service.enrich_artists_with_spotify_data(
                progress_callback=progress_cb,
            )

        result: Dict[str, Any] = {
            "status": "success",
            "task": "enrich_spotify_artists",
            "summary": summary,
        }
        await _set_result(task_id, result)
        return result

    except Exception as exc:
        log.exception("Spotify artist enrichment task failed", task_id=task_id)
        result = {
            "status": "failure",
            "task": "enrich_spotify_artists",
            "error": str(exc),
        }
        await _set_result(task_id, result)
        return result