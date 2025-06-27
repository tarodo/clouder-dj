from __future__ import annotations

import uuid
from typing import Any, Awaitable, Callable, Dict, List

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.beatport import BeatportAPIClient
from app.clients.spotify import SpotifyAPIClient
from app.core.settings import settings
from app.db.models.external_data import (
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.repositories import ExternalDataRepository, TrackRepository
from app.services.data_processing import DataProcessingService

log = structlog.get_logger(__name__)


class CollectionService:
    """Service for collecting and processing data from external sources."""

    def __init__(
        self,
        db: AsyncSession,
        external_data_repo: ExternalDataRepository,
        data_processing_service: DataProcessingService,
    ):
        self.db = db
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

    async def enrich_tracks_with_spotify_data(
        self,
        progress_callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> Dict[str, Any]:
        """
        Finds tracks with ISRC but no Spotify link, searches for them on Spotify,
        and persists the results (found or not found) as ExternalData records.
        """
        track_repo = TrackRepository(self.db)
        total_tracks = -1
        processed_count = 0
        found_count = 0
        not_found_count = 0

        async with httpx.AsyncClient() as http_client:
            spotify_client = SpotifyAPIClient(client=http_client)

            while True:
                # Fetch a batch of tracks that need a Spotify link.
                # We use offset=0 because each batch processing reduces the total
                # number of remaining tracks, so we always want the next available
                # batch.
                tracks, total = await track_repo.get_tracks_missing_spotify_link(
                    offset=0, limit=settings.SPOTIFY_SEARCH_BATCH_SIZE
                )

                if total_tracks == -1:
                    total_tracks = total
                    log.info("Starting Spotify enrichment", total_tracks=total_tracks)
                    if total_tracks == 0:
                        await progress_callback(
                            {"processed": 0, "total": 0, "found": 0, "not_found": 0}
                        )
                        break

                if not tracks:
                    break

                records_to_upsert: List[Dict[str, Any]] = []
                for track in tracks:
                    if not track.isrc:
                        continue

                    spotify_result = await spotify_client.search_track_by_isrc(
                        track.isrc
                    )

                    # Validate search result by matching at least one artist name
                    is_valid_match = False
                    if spotify_result:
                        local_artists = {
                            artist.name.lower() for artist in track.artists
                        }
                        spotify_artists = {
                            artist["name"].lower()
                            for artist in spotify_result.get("artists", [])
                        }
                        if local_artists.intersection(spotify_artists):
                            is_valid_match = True

                    if spotify_result and is_valid_match:
                        found_count += 1
                        records_to_upsert.append(
                            {
                                "provider": ExternalDataProvider.SPOTIFY,
                                "entity_type": ExternalDataEntityType.TRACK,
                                "entity_id": track.id,
                                "external_id": spotify_result["id"],
                                "raw_data": spotify_result,
                            }
                        )
                    else:
                        not_found_count += 1
                        records_to_upsert.append(
                            {
                                "provider": ExternalDataProvider.SPOTIFY,
                                "entity_type": ExternalDataEntityType.TRACK,
                                "entity_id": track.id,
                                "external_id": f"NOT_FOUND_{track.id}_{uuid.uuid4()}",
                                "raw_data": {"status": "not_found_by_isrc"},
                            }
                        )

                if records_to_upsert:
                    await self.external_data_repo.bulk_upsert(records_to_upsert)

                processed_count += len(tracks)
                await progress_callback(
                    {
                        "processed": processed_count,
                        "total": total_tracks,
                        "found": found_count,
                        "not_found": not_found_count,
                    }
                )

        log.info(
            "Finished Spotify enrichment",
            processed=processed_count,
            found=found_count,
            not_found=not_found_count,
        )
        return {
            "processed": processed_count,
            "total": total_tracks,
            "found": found_count,
            "not_found": not_found_count,
        }
