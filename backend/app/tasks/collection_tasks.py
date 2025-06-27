from typing import Any
import time
import httpx
from app.repositories import (
    ArtistRepository,
    LabelRepository,
    ReleaseRepository,
    TrackRepository,
    ExternalDataRepository,
)
import structlog
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import Context, TaskiqDepends, TaskiqResult

from app.broker import broker
from app.clients.beatport import BeatportAPIClient
from app.db.models import ExternalData
from app.db.models.external_data import (
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.db.session import AsyncSessionLocal
from app.services.data_processing import DataProcessingService
from app.services.collection import CollectionService

log = structlog.get_logger(__name__)


async def _bulk_upsert_external_data(
    session: AsyncSession,
    provider: ExternalDataProvider,
    entity_type: ExternalDataEntityType,
    tracks_data: list[dict[str, Any]],
) -> int:
    """Bulk upsert external data records. Returns the number of processed records."""
    if not tracks_data:
        return 0

    # Prepare data for bulk insert
    bulk_data = [
        {
            "provider": provider,
            "entity_type": entity_type,
            "entity_id": None,
            "external_id": str(track["id"]),
            "raw_data": track,
        }
        for track in tracks_data
    ]

    # Use PostgreSQL's ON CONFLICT for upsert
    stmt = insert(ExternalData).values(bulk_data)
    upsert_stmt = stmt.on_conflict_do_update(
        constraint="uq_external_data_provider_entity_external_id",
        set_=dict(
            raw_data=stmt.excluded.raw_data,
            updated_at=func.now(),
        ),
    )

    await session.execute(upsert_stmt)

    log.info(
        "Bulk upserted external data records",
        provider=provider.value,
        entity_type=entity_type.value,
        processed_count=len(tracks_data),
    )

    return len(tracks_data)


async def _collect_raw_tracks_data(
    bp_token: str, style_id: int, date_from: str, date_to: str
) -> None:
    """Phase 1: Collect all raw data from Beatport."""
    log.info(
        "Starting raw tracks data collection",
        style_id=style_id,
        date_from=date_from,
        date_to=date_to,
    )

    async with httpx.AsyncClient() as http_client:
        bp_client = BeatportAPIClient(client=http_client, bp_token=bp_token)
        async with AsyncSessionLocal() as session:
            async for tracks_page in bp_client.get_tracks(
                genre_id=style_id,
                publish_date_start=date_from,
                publish_date_end=date_to,
            ):
                await _bulk_upsert_external_data(
                    session,
                    ExternalDataProvider.BEATPORT,
                    ExternalDataEntityType.TRACK,
                    tracks_page,
                )
            await session.commit()


async def _set_result(
    task_id: str, progress: dict[str, Any], elapsed_time: float
) -> None:
    await broker.result_backend.set_result(
        task_id,
        TaskiqResult(
            is_err=False,
            execution_time=elapsed_time,
            return_value=progress,
        ),
    )


async def _process_collected_tracks_data(
    task_id: str, start_time: float, phase: str
) -> dict[str, Any]:
    """Phase 2: Process collected data in batches."""
    log.info("Starting collected tracks data processing")
    BATCH_SIZE = 500
    processed_count = 0
    total_to_process = 0

    # First, get total count
    async with AsyncSessionLocal() as session:
        stmt = select(func.count(ExternalData.id)).where(
            ExternalData.provider == ExternalDataProvider.BEATPORT,
            ExternalData.entity_type == ExternalDataEntityType.TRACK,
            ExternalData.entity_id.is_(None),
        )
        result = await session.execute(stmt)
        total_to_process = result.scalar_one()
        log.info("Found unprocessed records", count=total_to_process)

    if total_to_process == 0:
        return {"phase": phase, "processed": 0, "failed": 0, "total": 0}

    # Process in batches
    while True:
        async with AsyncSessionLocal() as session:
            # Init repos and service for this batch
            artist_repo = ArtistRepository(session)
            label_repo = LabelRepository(session)
            release_repo = ReleaseRepository(session)
            track_repo = TrackRepository(session)
            external_data_repo = ExternalDataRepository(session)

            data_processing_service = DataProcessingService(
                db=session,
                artist_repo=artist_repo,
                label_repo=label_repo,
                release_repo=release_repo,
                track_repo=track_repo,
                external_data_repo=external_data_repo,
            )

            # Fetch a batch of records
            records = await external_data_repo.get_unprocessed_beatport_tracks(
                limit=BATCH_SIZE
            )
            if not records:
                break  # No more records to process

            try:
                await data_processing_service.process_batch(records)
                processed_count += len(records)
            except Exception:
                log.error(
                    "Batch processing failed. Stopping task.", batch_size=len(records)
                )
                progress = {
                    "phase": "failed",
                    "processed": processed_count,
                    "failed": total_to_process - processed_count,
                    "total": total_to_process,
                }
                elapsed_time = time.perf_counter() - start_time
                await _set_result(task_id, progress, elapsed_time)
                return progress

            # Log progress
            progress = {
                "phase": phase,
                "processed": processed_count,
                "failed": 0,  # We stop on first failure
                "total": total_to_process,
            }
            elapsed_time = time.perf_counter() - start_time
            await _set_result(task_id, progress, elapsed_time)

    log.info("Finished processing all batches.", processed_count=processed_count)
    return {
        "phase": phase,
        "processed": processed_count,
        "failed": 0,
        "total": total_to_process,
    }


@broker.task
async def collect_bp_tracks_task(
    bp_token: str,
    style_id: int,
    date_from: str,
    date_to: str,
    context: Context = TaskiqDepends(),
) -> dict[str, Any]:
    """
    Collect Beatport tracks for a given style and date range.

    This task has two phases:
    1. Collect raw data from Beatport API
    2. Process collected data into structured entities
    """
    task_id = context.message.task_id
    log.info(
        "Starting Beatport tracks collection task",
        style_id=style_id,
        date_from=date_from,
        date_to=date_to,
        task_id=task_id,
    )
    start_time = time.perf_counter()
    collection_service = CollectionService()

    async def _update_task_progress(phase: str, progress_data: dict[str, Any]) -> None:
        progress = {"phase": phase, **progress_data}
        elapsed_time = time.perf_counter() - start_time
        await broker.result_backend.set_result(
            task_id,
            TaskiqResult(
                is_err=False,
                execution_time=elapsed_time,
                return_value=progress,
            ),
        )

    await _update_task_progress("collecting", {"processed": 0, "failed": 0, "total": 0})

    # Phase 1: Collect all raw data
    await collection_service.collect_beatport_tracks_raw(
        bp_token=bp_token, style_id=style_id, date_from=date_from, date_to=date_to
    )

    # Phase 2: Process collected data
    async def batch_progress_callback(progress_data: dict[str, Any]) -> None:
        await _update_task_progress("processing", progress_data)

    processing_results = await collection_service.process_unprocessed_beatport_tracks(
        batch_progress_callback=batch_progress_callback
    )

    if processing_results.get("failed", 0) > 0:
        finished_results = {"phase": "failed", **processing_results}
    else:
        finished_results = {"phase": "finished", **processing_results}

    log.info("Task finished", **finished_results)

    # Final update to task result
    await _update_task_progress(finished_results["phase"], processing_results)

    return finished_results
