from __future__ import annotations

from datetime import date
from typing import Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.models.external_data import (
    ExternalData,
    ExternalDataEntityType,
    ExternalDataProvider,
)
from app.db.models.raw_layer import RawLayerBlock
from app.db.models.track import Track
from app.repositories.base import BaseRepository


class RawLayerRepository(BaseRepository[RawLayerBlock]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=RawLayerBlock, db=db)

    async def get_by_user_style_and_name(
        self, *, user_id: int, style_id: int, name: str
    ) -> RawLayerBlock | None:
        stmt = select(RawLayerBlock).where(
            RawLayerBlock.user_id == user_id,
            RawLayerBlock.style_id == style_id,
            RawLayerBlock.name == name,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def select_tracks_for_block(
        self, *, start_date: date, end_date: date
    ) -> List[Track]:
        """
        Selects tracks that have a Beatport release within the date range
        and also have a corresponding Spotify link.
        """
        # Create an alias for the ExternalData table to use in the subquery
        # to prevent SQLAlchemy from auto-correlating and removing the FROM clause.
        spotify_ext_data = aliased(ExternalData)

        # Subquery to check for Spotify external data
        spotify_exists_subquery = (
            select(spotify_ext_data.id)
            .where(
                spotify_ext_data.entity_id == Track.id,
                spotify_ext_data.entity_type == ExternalDataEntityType.TRACK,
                spotify_ext_data.provider == ExternalDataProvider.SPOTIFY,
            )
            .exists()
        )

        # Subquery to get the IDs of tracks that meet the criteria.
        track_ids_subquery = (
            select(Track.id)
            .join(
                ExternalData,
                and_(
                    ExternalData.entity_id == Track.id,
                    ExternalData.entity_type == ExternalDataEntityType.TRACK,
                    ExternalData.provider == ExternalDataProvider.BEATPORT,
                ),
            )
            .where(
                ExternalData.raw_data["publish_date"]
                .as_string()
                .between(str(start_date), str(end_date)),
                spotify_exists_subquery,
            )
            .distinct()
            .subquery()
        )

        # Now, fetch the full Track objects and all their associated ExternalData
        # to prevent N+1 queries in the service layer.
        stmt = (
            select(Track, ExternalData)
            .join(
                ExternalData,
                and_(
                    ExternalData.entity_id == Track.id,
                    ExternalData.entity_type == ExternalDataEntityType.TRACK,
                ),
            )
            .where(Track.id.in_(select(track_ids_subquery)))
        )

        result = await self.db.execute(stmt)

        # Manually construct the track list with external_data attached,
        # following the pattern used elsewhere in the codebase.
        track_map: Dict[int, Track] = {}
        for track, ext_data in result.all():
            if track.id not in track_map:
                track.external_data = []  # type: ignore
                track_map[track.id] = track
            track_map[track.id].external_data.append(ext_data)  # type: ignore

        return list(track_map.values())
