import uuid

from backend.core import errors
from backend.core.exceptions import AppException
from backend.db.uow import UnitOfWork
from backend.models.track_artist import TrackArtist
from backend.repositories.track_artist import TrackArtistRepository
from backend.schemas.track_artist import (
    TrackArtistCreate,
    TrackArtistRead,
    TrackArtistUpdate,
)
from backend.services.base import GenericService


class TrackArtistService(
    GenericService[TrackArtist, TrackArtistCreate, TrackArtistUpdate, TrackArtistRead]
):
    def __init__(self):
        super().__init__(
            model=TrackArtist,
            repository=TrackArtistRepository,
            read_schema=TrackArtistRead,
            not_found_error_code=errors.TRACK_ARTIST_NOT_FOUND,
        )

    async def _pre_create(
        self, uow: UnitOfWork, obj_in: TrackArtistCreate, creator_id: uuid.UUID | None
    ) -> None:
        if not await uow.artists.get(obj_in.artist_id):
            raise AppException(errors.ARTIST_NOT_FOUND)
        if not await uow.tracks.get(obj_in.track_id):
            raise AppException(errors.TRACK_NOT_FOUND)

        if await uow.track_artists.get_by_pair(obj_in.artist_id, obj_in.track_id):
            raise AppException(errors.TRACK_ARTIST_ALREADY_EXISTS)

