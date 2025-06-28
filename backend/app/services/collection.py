from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

import httpx
import structlog

from app.clients.beatport import BeatportAPIClient
from app.db.models.external_data import (
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.repositories import ExternalDataRepository
from app.services.data_processing import DataProcessingService

log = structlog.get_logger(__name__)


class CollectionService:
    """Service for orchestrating data collection from external sources."""

    def __init__(
        self,
        external_data_repo: ExternalDataRepository,
        data_processing_service: DataProcessingService,
    ):
        self.external_data_repo = external_data_repo
        self.data_processing_service = data_processing_service

    async def collect_beatport_tracks_raw(
        self, bp_token: str, style_id: int, date_from: str, date_to: str
    ) -> None:
        """
        Collect raw track data from Beatport API and store in external_data table.
        This is phase 1 of the collection process.
        """
        log.info(
            "Starting raw tracks data collection",
            style_id=style_id,
            date_from=date_from,
            date_to=date_to,
        )

        async with httpx.AsyncClient() as http_client:
            bp_client = BeatportAPIClient(client=http_client, bp_token=bp_token)
            async for tracks_page in bp_client.get_tracks(
                genre_id=style_id,
                publish_date_start=date_from,
                publish_date_end=date_to,
            ):
                if not tracks_page:
                    continue
                bulk_data = [
                    {
                        "provider": ExternalDataProvider.BEATPORT,
                        "entity_type": ExternalDataEntityType.TRACK,
                        "external_id": str(track["id"]),
                        "raw_data": track,
                    }
                    for track in tracks_page
                ]
                await self.external_data_repo.bulk_upsert(bulk_data)

    async def process_unprocessed_beatport_tracks(
        self,
        batch_progress_callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> Dict[str, Any]:
        """Process all unprocessed Beatport tracks in batches."""
        BATCH_SIZE = 500
        processed_count = 0

        total_to_process = (
            await self.external_data_repo.count_unprocessed_beatport_tracks()
        )
        log.info("Found unprocessed records", count=total_to_process)

        if total_to_process == 0:
            return {"processed": 0, "failed": 0, "total": total_to_process}

        while processed_count < total_to_process:
            records = await self.external_data_repo.get_unprocessed_beatport_tracks(
                limit=BATCH_SIZE
            )
            if not records:
                break

            try:
                await self.data_processing_service.process_batch(records)
                processed_count += len(records)
            except Exception:
                log.exception(
                    "Batch processing failed. Stopping task.",
                    batch_size=len(records),
                )
                failed_count = total_to_process - processed_count
                return {
                    "processed": processed_count,
                    "failed": failed_count,
                    "total": total_to_process,
                }

            await batch_progress_callback(
                {"processed": processed_count, "failed": 0, "total": total_to_process}
            )

        log.info("Finished processing all batches.", processed_count=processed_count)
        return {
            "processed": processed_count,
            "failed": 0,
            "total": total_to_process,
        }
