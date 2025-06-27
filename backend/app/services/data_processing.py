from __future__ import annotations

from datetime import date
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExternalData, Track
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

    async def process_batch(self, records: List[ExternalData]) -> None:
        if not records:
            return

        try:
            # 1. Extract and bulk get/create labels
            label_names = {
                r.raw_data["release"]["label"]["name"]
                for r in records
                if r.raw_data
                and "release" in r.raw_data
                and "label" in r.raw_data["release"]
            }
            labels_map = await self.label_repo.bulk_get_or_create_by_name(
                list(label_names)
            )

            # 2. Extract and bulk get/create artists
            artist_names = {
                artist["name"]
                for r in records
                if r.raw_data and "artists" in r.raw_data
                for artist in r.raw_data["artists"]
            }
            artists_map = await self.artist_repo.bulk_get_or_create_by_name(
                list(artist_names)
            )

            # 3. Extract and bulk get/create releases
            releases_to_create = []
            for r in records:
                if not (r.raw_data and "release" in r.raw_data):
                    continue
                release_data = r.raw_data["release"]
                label_data = release_data.get("label")
                if not label_data:
                    continue
                label = labels_map.get(label_data["name"])
                if not label:
                    continue

                release_date = None
                if release_data.get("publish_date"):
                    release_date = date.fromisoformat(release_data["publish_date"])

                releases_to_create.append(
                    {
                        "name": release_data["name"],
                        "label_id": label.id,
                        "release_date": release_date,
                    }
                )

            unique_releases_to_create = [
                dict(t) for t in {tuple(d.items()) for d in releases_to_create}
            ]
            releases_map = await self.release_repo.bulk_get_or_create(
                unique_releases_to_create
            )

            # 4. Prepare and bulk create tracks
            tracks_to_create = []
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
                        "release_id": release.id,
                        "artist_ids": artist_ids,
                        "external_id": r.external_id,
                    }
                )

            created_tracks: List[Track] = (
                await self.track_repo.bulk_create_with_relations(tracks_to_create)
            )

            # 5. Prepare and bulk update ExternalData records
            updates_for_external_data = {
                track_data["external_id"]: created_track.id
                for track_data, created_track in zip(tracks_to_create, created_tracks)
            }
            await self.external_data_repo.bulk_update_entity_ids(
                updates_for_external_data
            )

            await self.db.commit()
            log.info("Successfully processed batch of tracks", count=len(records))
        except Exception:
            await self.db.rollback()
            log.exception(
                "Failed to process batch of tracks", record_count=len(records)
            )
            raise
