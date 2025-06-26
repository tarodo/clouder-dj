from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session

from app.core.settings import settings
from app.db.models import Artist, ExternalData, Label, Release, Track
from app.db.models.external_data import ExternalDataProvider, ExternalDataEntityType

log = structlog.get_logger(__name__)


class SyncDataProcessingService:
    """Synchronous version of DataProcessingService for use in taskiq workers."""

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def create(cls) -> "SyncDataProcessingService":
        """Create a sync processing service with its own session."""
        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        return cls(session)

    def close(self):
        """Close the database session."""
        self.db.close()

    def _get_or_create_label(self, beatport_label_data: dict[str, Any]) -> Label:
        label_name = beatport_label_data["name"]
        external_label_id = str(beatport_label_data["id"])

        # Check if label already exists in ExternalData
        external_data = (
            self.db.query(ExternalData)
            .filter(
                ExternalData.provider == ExternalDataProvider.BEATPORT,
                ExternalData.entity_type == ExternalDataEntityType.LABEL,
                ExternalData.external_id == external_label_id,
            )
            .first()
        )

        if external_data and external_data.entity_id:
            # Return existing label
            label = (
                self.db.query(Label).filter(Label.id == external_data.entity_id).first()
            )
            if label:
                return label

        # Check if label exists by name (fallback)
        label = self.db.query(Label).filter(Label.name == label_name).first()

        if not label:
            try:
                label = Label(name=label_name)
                self.db.add(label)
                self.db.flush()
                self.db.refresh(label)
                log.info("Created new label", label_name=label_name)
            except IntegrityError:
                self.db.rollback()
                label = self.db.query(Label).filter(Label.name == label_name).one()

        # Create or update ExternalData record
        if not external_data:
            external_data = ExternalData(
                provider=ExternalDataProvider.BEATPORT,
                entity_type=ExternalDataEntityType.LABEL,
                external_id=external_label_id,
                entity_id=label.id,
                raw_data=beatport_label_data,
            )
            self.db.add(external_data)
            self.db.flush()
        elif external_data.entity_id != label.id:
            # Update existing record
            external_data.entity_id = label.id
            external_data.raw_data = beatport_label_data
            self.db.flush()

        return label

    def _get_or_create_artists(
        self, beatport_artists_data: list[dict[str, Any]]
    ) -> list[Artist]:
        artists = []
        for artist_data in beatport_artists_data:
            artist_name = artist_data["name"]

            artist = self.db.query(Artist).filter(Artist.name == artist_name).first()
            if artist:
                artists.append(artist)
                continue

            try:
                artist = Artist(name=artist_name)
                self.db.add(artist)
                self.db.flush()
                self.db.refresh(artist)
                log.info("Created new artist", artist_name=artist_name)
                artists.append(artist)
            except IntegrityError:
                self.db.rollback()
                artist = self.db.query(Artist).filter(Artist.name == artist_name).one()
                artists.append(artist)
        return artists

    def _get_or_create_release(self, beatport_release_data: dict[str, Any]) -> Release:
        release_name = beatport_release_data["name"]
        label = self._get_or_create_label(beatport_release_data["label"])

        release = (
            self.db.query(Release)
            .filter(Release.name == release_name, Release.label_id == label.id)
            .first()
        )
        if release:
            return release

        try:
            release_date = None
            if "release_date" in beatport_release_data:
                release_date = date.fromisoformat(beatport_release_data["release_date"])
            release = Release(
                name=release_name, label_id=label.id, release_date=release_date
            )
            self.db.add(release)
            self.db.flush()
            self.db.refresh(release)
            log.info("Created new release", release_name=release_name)
            return release
        except IntegrityError:
            self.db.rollback()
            release = (
                self.db.query(Release)
                .filter(Release.name == release_name, Release.label_id == label.id)
                .one()
            )
            return release

    def process_beatport_track_data(self, external_data_record: ExternalData) -> None:
        raw_data = external_data_record.raw_data
        if not raw_data:
            log.warning("ExternalData has no raw_data", id=external_data_record.id)
            return

        try:
            artists = self._get_or_create_artists(raw_data["artists"])
            release = self._get_or_create_release(raw_data["release"])

            track = (
                self.db.query(Track)
                .filter(Track.name == raw_data["name"], Track.release_id == release.id)
                .first()
            )

            if not track:
                track = Track(
                    name=raw_data["name"],
                    duration_ms=raw_data.get("length_ms"),
                    bpm=raw_data.get("bpm"),
                    key=raw_data.get("key", {}).get("name"),
                    release_id=release.id,
                    artists=artists,
                )
                self.db.add(track)
                self.db.flush()
                self.db.refresh(track)

            external_data_record.entity_id = track.id
            self.db.add(external_data_record)
            self.db.commit()
            log.info("Successfully processed track", track_name=raw_data["name"])
        except Exception:
            self.db.rollback()
            log.exception("Failed to process record", id=external_data_record.id)
            raise
