from __future__ import annotations

import uuid
from typing import Any, Awaitable, Callable, Dict, List

import httpx
import structlog
from rapidfuzz import fuzz, process
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.beatport import BeatportAPIClient
from app.clients.spotify import SpotifyAPIClient
from app.core.settings import settings
from app.db.models.external_data import (
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.db.models.track import Track
from app.repositories import (
    ArtistRepository,
    ExternalDataRepository,
    TrackRepository,
)
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

    @staticmethod
    def _validate_spotify_search_result(
        track: Track,
        spotify_result: Dict[str, Any] | None,
        similarity_threshold: int = 80,
    ) -> bool:
        """
        Validate Spotify search result by matching at least one artist name
        using fuzzy matching with rapidfuzz.process.extractOne.

        Args:
            track: Local track object with artists relationship
            spotify_result: Spotify API search result
            similarity_threshold: Minimum allowed similarity ratio (0-100) for a match.

        Returns:
            True if the search result is valid (has a sufficiently matching artist),
            False otherwise
        """
        if not spotify_result:
            log.warning("No Spotify result found", track=track.isrc)
            return False

        local_artists_names = [artist.name.lower() for artist in track.artists]
        spotify_artists_names = [
            artist["name"].lower() for artist in spotify_result.get("artists", [])
        ]

        if not spotify_artists_names:
            log.warning(
                "No artists found in Spotify result",
                track=track.isrc,
                spotify_result=spotify_result,
            )
            return False

        for local_artist in local_artists_names:
            best_match = process.extractOne(
                local_artist,
                spotify_artists_names,
                scorer=fuzz.ratio,
                score_cutoff=similarity_threshold,
            )

            if best_match:
                return True

        log.warning(
            "No matching artist found",
            track=track.isrc,
            local_artists_names=local_artists_names,
            spotify_artists_names=spotify_artists_names,
            spotify_result=spotify_result,
        )
        return False

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

                    is_valid_match = self._validate_spotify_search_result(
                        track, spotify_result
                    )

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

    async def enrich_artists_with_spotify_data(
        self,
        progress_callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> Dict[str, Any]:
        """
        Finds artists without a Spotify link, matches them using associated track data,
        and persists the results (found or not found) as ExternalData records.
        """
        artist_repo = ArtistRepository(self.db)
        track_repo = TrackRepository(self.db)
        total_artists = -1
        processed_count = 0
        found_count = 0
        not_found_count = 0

        async with httpx.AsyncClient() as http_client:
            spotify_client = SpotifyAPIClient(client=http_client)

            while True:
                artists, total = await artist_repo.get_artists_missing_spotify_link(
                    offset=0, limit=settings.SPOTIFY_SEARCH_BATCH_SIZE
                )

                if total_artists == -1:
                    total_artists = total
                    log.info(
                        "Starting Spotify artist enrichment",
                        total_artists=total_artists,
                    )
                    if total_artists == 0:
                        await progress_callback(
                            {"processed": 0, "total": 0, "found": 0, "not_found": 0}
                        )
                        break

                if not artists:
                    break

                artist_ids = [artist.id for artist in artists]
                tracks_with_spotify_data = (
                    await track_repo.get_tracks_by_artist_ids_with_spotify_data(
                        artist_ids=artist_ids
                    )
                )

                artist_id_to_tracks: Dict[int, List[Track]] = {
                    artist_id: [] for artist_id in artist_ids
                }
                for track in tracks_with_spotify_data:
                    for artist in track.artists:
                        if artist.id in artist_id_to_tracks:
                            artist_id_to_tracks[artist.id].append(track)

                artist_match_results: Dict[int, str | None] = {}
                matched_spotify_artist_ids = set()

                for artist in artists:
                    spotify_artist_candidates: Dict[str, str] = {}
                    for track in artist_id_to_tracks[artist.id]:
                        if hasattr(track, "external_data"):
                            for ext_data in track.external_data:  # type: ignore
                                if ext_data.raw_data:
                                    for sp_artist in ext_data.raw_data.get(
                                        "artists", []
                                    ):
                                        if sp_artist.get("id") and sp_artist.get(
                                            "name"
                                        ):
                                            spotify_artist_candidates[
                                                sp_artist["id"]
                                            ] = sp_artist["name"]

                    if not spotify_artist_candidates:
                        artist_match_results[artist.id] = None
                        continue

                    best_match = process.extractOne(
                        artist.name,
                        list(spotify_artist_candidates.values()),
                        scorer=fuzz.ratio,
                        score_cutoff=85,
                    )

                    if best_match:
                        matched_name = best_match[0]
                        for sid, sname in spotify_artist_candidates.items():
                            if sname == matched_name:
                                artist_match_results[artist.id] = sid
                                matched_spotify_artist_ids.add(sid)
                                break
                    else:
                        artist_match_results[artist.id] = None

                spotify_artist_details = {}
                if matched_spotify_artist_ids:
                    details_list = await spotify_client.get_artists_by_ids(
                        list(matched_spotify_artist_ids)
                    )
                    if details_list:
                        spotify_artist_details = {
                            artist["id"]: artist for artist in details_list
                        }

                records_to_upsert: List[Dict[str, Any]] = []
                for artist in artists:
                    spotify_id = artist_match_results.get(artist.id)
                    if spotify_id and spotify_id in spotify_artist_details:
                        found_count += 1
                        records_to_upsert.append(
                            {
                                "provider": ExternalDataProvider.SPOTIFY,
                                "entity_type": ExternalDataEntityType.ARTIST,
                                "entity_id": artist.id,
                                "external_id": spotify_id,
                                "raw_data": spotify_artist_details[spotify_id],
                            }
                        )
                    else:
                        not_found_count += 1
                        records_to_upsert.append(
                            {
                                "provider": ExternalDataProvider.SPOTIFY,
                                "entity_type": ExternalDataEntityType.ARTIST,
                                "entity_id": artist.id,
                                "external_id": f"NOT_FOUND_{artist.id}_{uuid.uuid4()}",
                                "raw_data": {"status": "not_found_by_fuzzy_match"},
                            }
                        )

                if records_to_upsert:
                    await self.external_data_repo.bulk_upsert(records_to_upsert)

                processed_count += len(artists)
                await progress_callback(
                    {
                        "processed": processed_count,
                        "total": total_artists,
                        "found": found_count,
                        "not_found": not_found_count,
                    }
                )

        log.info(
            "Finished Spotify artist enrichment",
            processed=processed_count,
            found=found_count,
            not_found=not_found_count,
        )
        return {
            "processed": processed_count,
            "total": total_artists,
            "found": found_count,
            "not_found": not_found_count,
        }
