from typing import Any
import time
import httpx
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
from app.services.data_processing import SyncDataProcessingService

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


def _process_record_sync(record_id: int) -> bool:
    """Process a single record synchronously to avoid greenlet issues."""
    processing_service = None
    try:
        processing_service = SyncDataProcessingService.create()

        # Get the record
        record = processing_service.db.get(ExternalData, record_id)
        if not record:
            log.warning("Record not found", record_id=record_id)
            return False

        # Process the record
        processing_service.process_beatport_track_data(record)
        return True

    except Exception as e:
        log.exception(
            "Failed to process record sync", record_id=record_id, error=str(e)
        )
        return False
    finally:
        if processing_service:
            processing_service.close()


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
    """Phase 2: Process collected data."""
    log.info("Starting collected tracks data processing")

    processed_count = 0
    failed_count = 0

    async with AsyncSessionLocal() as session:
        stmt = select(ExternalData.id).where(
            ExternalData.provider == ExternalDataProvider.BEATPORT,
            ExternalData.entity_type == ExternalDataEntityType.TRACK,
            ExternalData.entity_id.is_(None),
        )
        result = await session.execute(stmt)
        record_ids = [row[0] for row in result.fetchall()]
        total_to_process = len(record_ids)
        log.info("Found unprocessed records", count=total_to_process)

    # Process records synchronously
    for record_id in record_ids:
        if _process_record_sync(record_id):
            processed_count += 1
        else:
            failed_count += 1

        # Log progress periodically
        progress = {
            "phase": phase,
            "processed": processed_count,
            "failed": failed_count,
            "total": total_to_process,
        }
        elapsed_time = time.perf_counter() - start_time
        await _set_result(task_id, progress, elapsed_time)

    return {
        "phase": phase,
        "processed": processed_count,
        "failed": failed_count,
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
    """A task to collect and process tracks from Beatport."""
    task_id = context.message.task_id
    log.info(
        "Beatport tracks collection task started",
        style_id=style_id,
        date_from=date_from,
        date_to=date_to,
        task_id=task_id,
    )
    start_time = time.perf_counter()
    await _set_result(
        task_id, {"phase": "collecting", "processed": 0, "failed": 0, "total": 0}, 0
    )
    # Phase 1: Collect all raw data
    await _collect_raw_tracks_data(bp_token, style_id, date_from, date_to)

    # Phase 2: Process collected data
    processing_results = await _process_collected_tracks_data(
        task_id, start_time, "processing"
    )

    finished_results = processing_results.copy()
    finished_results["phase"] = "finished"

    log.info("Task finished", **finished_results)
    return finished_results
