from typing import Any

import httpx
import structlog
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker import broker
from app.clients.beatport import BeatportAPIClient
from app.db.models import ExternalData
from app.db.models.external_data import (
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.db.session import AsyncSessionLocal

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

    _ = await session.execute(upsert_stmt)

    processed_count = len(tracks_data)
    log.info(
        "Bulk upserted external data records",
        provider=provider.value,
        entity_type=entity_type.value,
        processed_count=processed_count,
    )

    return processed_count


@broker.task
async def collect_bp_tracks_task(
    bp_token: str, style_id: int, date_from: str, date_to: str
) -> dict[str, str]:
    """A task to collect tracks from Beatport and store them in the database."""
    log.info(
        "Beatport tracks collection task started",
        style_id=style_id,
        date_from=date_from,
        date_to=date_to,
    )
    total_processed = 0

    async with httpx.AsyncClient() as http_client:
        bp_client = BeatportAPIClient(client=http_client, bp_token=bp_token)

        async with AsyncSessionLocal() as session:
            async for tracks_page in bp_client.get_tracks(
                genre_id=style_id,
                publish_date_start=date_from,
                publish_date_end=date_to,
            ):
                processed_count = await _bulk_upsert_external_data(
                    session,
                    ExternalDataProvider.BEATPORT,
                    ExternalDataEntityType.TRACK,
                    tracks_page,
                )
                total_processed += processed_count
                await session.commit()

    result_message = f"Task finished. Total processed: {total_processed}."
    log.info(result_message)
    return {"status": "ok", "message": result_message}
