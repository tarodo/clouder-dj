from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator


from app.db.session import AsyncSessionLocal
from app.repositories import (
    ArtistRepository,
    ExternalDataRepository,
    LabelRepository,
    ReleaseRepository,
    TrackRepository,
)
from app.services.collection import CollectionService
from app.services.enrichment import EnrichmentService
from app.services.data_processing import DataProcessingService


@asynccontextmanager
async def get_collection_service() -> AsyncGenerator[CollectionService, None]:
    """
    Provides a CollectionService instance with a managed DB session.
    This acts as a Unit of Work for the collection task.
    """
    async with AsyncSessionLocal() as session:
        try:
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

            collection_service = CollectionService(
                external_data_repo=external_data_repo,
                data_processing_service=data_processing_service,
            )
            yield collection_service
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_enrichment_service() -> AsyncGenerator[EnrichmentService, None]:
    """
    Provides an EnrichmentService instance with a managed DB session.
    This acts as a Unit of Work for enrichment tasks.
    """
    async with AsyncSessionLocal() as session:
        try:
            artist_repo = ArtistRepository(session)
            track_repo = TrackRepository(session)
            external_data_repo = ExternalDataRepository(session)

            enrichment_service = EnrichmentService(
                db=session,
                artist_repo=artist_repo,
                track_repo=track_repo,
                external_data_repo=external_data_repo,
            )
            yield enrichment_service
            await session.commit()
        except Exception:
            await session.rollback()
            raise
