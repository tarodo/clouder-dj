from __future__ import annotations

from typing import Any, Dict, List, Tuple, cast

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artist, ExternalData, Label, Release, Track
from app.db.models.external_data import ExternalDataEntityType, ExternalDataProvider
from app.repositories import (
    ArtistRepository,
    ExternalDataRepository,
    LabelRepository,
    ReleaseRepository,
    TrackRepository,
)

log = structlog.get_logger(__name__)


class DataProcessingService:
    """Service to process external data in batches and create DB entities."""

    def __init__(
        self,
        db: AsyncSession,
        artist_repo: ArtistRepository,
        label_repo: LabelRepository,
        release_repo: ReleaseRepository,
        track_repo: TrackRepository,
        external_data_repo: ExternalDataRepository,
    ):
        self.db = db
        self.artist_repo = artist_repo
        self.label_repo = label_repo
        self.release_repo = release_repo
        self.track_repo = track_repo
        self.external_data_repo = external_data_repo

    async def _process_labels(
        self, records: List[ExternalData]
    ) -> Tuple[Dict[str, Label], List[Dict[str, Any]]]:
        label_data_map = {}
        for r in records:
            if (
                r.raw_data
                and (release_data := r.raw_data.get("release"))
                and (label_info := release_data.get("label"))
            ):
                label_name = label_info["name"]
                if label_name not in label_data_map:
                    label_data_map[label_name] = label_info

        if not label_data_map:
            return {}, []

        labels_map = await self.label_repo.bulk_get_or_create_by_name(
            list(label_data_map.keys())
        )

        external_data_for_labels = []
        for name, label in labels_map.items():
            label_info = label_data_map[name]
            external_data_for_labels.append(
                {
                    "provider": ExternalDataProvider.BEATPORT,
                    "entity_type": ExternalDataEntityType.LABEL,
                    "entity_id": label.id,
                    "external_id": str(label_info["id"]),
                    "raw_data": label_info,
                }
            )
        return labels_map, external_data_for_labels

    async def _process_artists(
        self, records: List[ExternalData]
    ) -> Tuple[Dict[str, Artist], List[Dict[str, Any]]]:
        artist_data_map = {}
        for r in records:
            if r.raw_data and (artists_info := r.raw_data.get("artists")):
                for artist_info in artists_info:
                    artist_name = artist_info["name"]
                    if artist_name not in artist_data_map:
                        artist_data_map[artist_name] = artist_info

        if not artist_data_map:
            return {}, []

        artists_map = await self.artist_repo.bulk_get_or_create_by_name(
            list(artist_data_map.keys())
        )

        external_data_for_artists = []
        for name, artist in artists_map.items():
            artist_info = artist_data_map[name]
            external_data_for_artists.append(
                {
                    "provider": ExternalDataProvider.BEATPORT,
                    "entity_type": ExternalDataEntityType.ARTIST,
                    "entity_id": artist.id,
                    "external_id": str(artist_info["id"]),
                    "raw_data": artist_info,
                }
            )
        return artists_map, external_data_for_artists

    async def _process_releases(
        self, records: List[ExternalData], labels_map: Dict[str, Label]
    ) -> Tuple[Dict[Tuple[str, int], Release], List[Dict[str, Any]]]:
        releases_to_create = []
        release_data_map = {}

        for r in records:
            if not (r.raw_data and (release_data := r.raw_data.get("release"))):
                continue
            if not (label_data := release_data.get("label")):
                continue
            label = labels_map.get(label_data["name"])
            if not label:
                continue

            release_key = (release_data["name"], label.id)
            if release_key not in release_data_map:
                release_data_map[release_key] = release_data
                releases_to_create.append(
                    {
                        "name": release_data["name"],
                        "label_id": label.id,
                    }
                )

        if not releases_to_create:
            return {}, []

        releases_map_from_repo = await self.release_repo.bulk_get_or_create(
            releases_to_create
        )
        releases_map = cast(Dict[Tuple[str, int], Release], releases_map_from_repo)

        external_data_for_releases = []
        for key, release in releases_map.items():
            release_info = release_data_map[key]
            external_data_for_releases.append(
                {
                    "provider": ExternalDataProvider.BEATPORT,
                    "entity_type": ExternalDataEntityType.RELEASE,
                    "entity_id": release.id,
                    "external_id": str(release_info["id"]),
                    "raw_data": release_info,
                }
            )
        return releases_map, external_data_for_releases

    async def _process_tracks(
        self,
        records: List[ExternalData],
        artists_map: Dict[str, Artist],
        labels_map: Dict[str, Label],
        releases_map: Dict[Tuple[str, int], Release],
    ) -> List[Dict[str, Any]]:
        tracks_to_create = []
        external_id_to_raw_data = {r.external_id: r.raw_data for r in records}

        for r in records:
            if not r.raw_data:
                continue

            release_data = r.raw_data.get("release")
            if not release_data or not release_data.get("label"):
                continue

            label = labels_map.get(release_data["label"]["name"])
            if not label:
                continue

            release_key = (release_data["name"], label.id)
            release = releases_map.get(release_key)
            if not release:
                continue

            artist_ids = [
                artists_map[artist["name"]].id
                for artist in r.raw_data.get("artists", [])
                if artist["name"] in artists_map
            ]

            tracks_to_create.append(
                {
                    "name": r.raw_data["name"],
                    "duration_ms": r.raw_data.get("length_ms"),
                    "bpm": r.raw_data.get("bpm"),
                    "key": r.raw_data.get("key", {}).get("name"),
                    "isrc": r.raw_data.get("isrc"),
                    "release_id": release.id,
                    "artist_ids": artist_ids,
                    "external_id": r.external_id,
                }
            )

        if not tracks_to_create:
            return []

        tracks_map: Dict[Tuple[str, int, str | None], Track] = (
            await self.track_repo.bulk_get_or_create_with_relations(tracks_to_create)
        )

        external_data_for_tracks = []
        for track_data in tracks_to_create:
            track_key = (
                track_data["name"],
                track_data["release_id"],
                track_data["isrc"],
            )
            fetched_track = tracks_map.get(track_key)
            if not fetched_track:
                log.warning(
                    "Could not find track in map after get_or_create", key=track_key
                )
                continue

            external_id = track_data["external_id"]
            external_data_for_tracks.append(
                {
                    "provider": ExternalDataProvider.BEATPORT,
                    "entity_type": ExternalDataEntityType.TRACK,
                    "entity_id": fetched_track.id,
                    "external_id": external_id,
                    "raw_data": external_id_to_raw_data[external_id],
                }
            )

        return external_data_for_tracks

    async def process_batch(self, records: List[ExternalData]) -> None:
        if not records:
            return

        try:
            all_external_data_to_upsert = []

            labels_map, ext_data_labels = await self._process_labels(records)
            all_external_data_to_upsert.extend(ext_data_labels)

            artists_map, ext_data_artists = await self._process_artists(records)
            all_external_data_to_upsert.extend(ext_data_artists)

            releases_map, ext_data_releases = await self._process_releases(
                records, labels_map
            )
            all_external_data_to_upsert.extend(ext_data_releases)

            ext_data_tracks = await self._process_tracks(
                records, artists_map, labels_map, releases_map
            )
            all_external_data_to_upsert.extend(ext_data_tracks)

            if all_external_data_to_upsert:
                await self.external_data_repo.bulk_upsert(all_external_data_to_upsert)

            log.info("Successfully processed batch of tracks", count=len(records))

        except Exception as e:
            log.error("Failed to process batch", error=str(e), count=len(records))
            raise
