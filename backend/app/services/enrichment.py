from __future__ import annotations

import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
import structlog
from rapidfuzz import fuzz, process
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.spotify import SpotifyAPIClient
from app.core.settings import settings
from app.db.models.artist import Artist
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

log = structlog.get_logger(__name__)


class EnrichmentService:
    """Service for enriching data from external sources like Spotify."""

    def __init__(
        self,
        db: AsyncSession,
        artist_repo: ArtistRepository,
        track_repo: TrackRepository,
        external_data_repo: ExternalDataRepository,
    ):
        self.db = db
        self.artist_repo = artist_repo
        self.track_repo = track_repo
        self.external_data_repo = external_data_repo

    def _validate_spotify_search_result(
        self,
        track: Track,
        spotify_result: Dict[str, Any] | None,
        similarity_threshold: int = 80,
    ) -> bool:
        """
        Validate Spotify search result by matching at least one artist name
        using fuzzy matching.
        """
        if not spotify_result:
            log.warning("No Spotify result found", track_isrc=track.isrc)
            return False

        local_artists_names = [artist.name.lower() for artist in track.artists]
        spotify_artists_names = [
            artist["name"].lower() for artist in spotify_result.get("artists", [])
        ]

        if not spotify_artists_names:
            log.warning(
                "No artists found in Spotify result",
                track_isrc=track.isrc,
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
            "No matching artist found for track",
            track_isrc=track.isrc,
            local_artists=local_artists_names,
            spotify_artists=spotify_artists_names,
        )
        return False

    async def enrich_tracks_with_spotify_data(
        self,
        progress_callback: Callable[[Dict[str, Any]], Awaitable[None]],
        similarity_threshold: int,
    ) -> Dict[str, Any]:
        """
        Finds tracks with ISRC but no Spotify link, searches for them on Spotify,
        and persists the results (found or not found) as ExternalData records.
        """
        total_tracks = -1
        processed_count = 0
        found_count = 0
        not_found_count = 0

        async with httpx.AsyncClient() as http_client:
            spotify_client = SpotifyAPIClient(client=http_client)

            while True:
                tracks, total = await self.track_repo.get_tracks_missing_spotify_link(
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
                        track, spotify_result, similarity_threshold
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

    def _get_spotify_artist_candidates(
        self, artist: Artist, artist_id_to_tracks: Dict[int, List[Track]]
    ) -> Dict[str, str]:
        """Collects potential Spotify artist candidates from an artist's tracks."""
        candidates: Dict[str, str] = {}
        for track in artist_id_to_tracks.get(artist.id, []):
            if hasattr(track, "external_data"):
                for ext_data in track.external_data:  # type: ignore
                    if ext_data.raw_data:
                        for sp_artist in ext_data.raw_data.get("artists", []):
                            if sp_artist.get("id") and sp_artist.get("name"):
                                candidates[sp_artist["id"]] = sp_artist["name"]
        return candidates

    def _find_best_match_artist(
        self, artist_name: str, candidates: Dict[str, str]
    ) -> Optional[str]:
        """Finds the best matching Spotify artist ID using fuzzy matching."""
        if not candidates:
            return None

        best_match = process.extractOne(
            artist_name,
            list(candidates.values()),
            scorer=fuzz.ratio,
            score_cutoff=85,
        )

        if best_match:
            matched_name = best_match[0]
            for sid, sname in candidates.items():
                if sname == matched_name:
                    return sid
        return None

    async def _fetch_spotify_artist_details(
        self, spotify_client: SpotifyAPIClient, artist_ids: List[str]
    ) -> Dict[str, Dict]:
        """Fetches full artist details from Spotify for a list of IDs."""
        if not artist_ids:
            return {}
        details_list = await spotify_client.get_artists_by_ids(artist_ids)
        if not details_list:
            return {}
        return {artist["id"]: artist for artist in details_list}

    async def enrich_artists_with_spotify_data(
        self,
        progress_callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> Dict[str, Any]:
        """
        Finds artists without a Spotify link, matches them using associated track data,
        and persists the results.
        """
        total_artists = -1
        processed_count = 0
        found_count = 0
        not_found_count = 0

        async with httpx.AsyncClient() as http_client:
            spotify_client = SpotifyAPIClient(client=http_client)

            while True:
                artists, total = (
                    await self.artist_repo.get_artists_missing_spotify_link(
                        offset=0, limit=settings.SPOTIFY_SEARCH_BATCH_SIZE
                    )
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
                tracks = (
                    await self.track_repo.get_tracks_by_artist_ids_with_spotify_data(
                        artist_ids=artist_ids
                    )
                )

                artist_id_to_tracks: Dict[int, List[Track]] = {
                    aid: [] for aid in artist_ids
                }
                for track in tracks:
                    for artist in track.artists:
                        if artist.id in artist_id_to_tracks:
                            artist_id_to_tracks[artist.id].append(track)

                artist_match_results: Dict[int, str | None] = {}
                for artist in artists:
                    candidates = self._get_spotify_artist_candidates(
                        artist, artist_id_to_tracks
                    )
                    best_match_id = self._find_best_match_artist(
                        artist.name, candidates
                    )
                    artist_match_results[artist.id] = best_match_id

                matched_ids = [
                    sid for sid in artist_match_results.values() if sid is not None
                ]
                spotify_details = await self._fetch_spotify_artist_details(
                    spotify_client, matched_ids
                )

                records_to_upsert: List[Dict[str, Any]] = []
                for artist in artists:
                    spotify_id = artist_match_results.get(artist.id)
                    if spotify_id and spotify_id in spotify_details:
                        found_count += 1
                        records_to_upsert.append(
                            {
                                "provider": ExternalDataProvider.SPOTIFY,
                                "entity_type": ExternalDataEntityType.ARTIST,
                                "entity_id": artist.id,
                                "external_id": spotify_id,
                                "raw_data": spotify_details[spotify_id],
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
