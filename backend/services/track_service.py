import uuid

from backend.core import errors
from backend.core.exceptions import AppException
from backend.db.uow import UnitOfWork
from backend.models.track import Track
from backend.repositories.track import TrackRepository
from backend.schemas.track import TrackCreate, TrackRead, TrackUpdate
from backend.services.base import GenericService


class TrackService(GenericService[Track, TrackCreate, TrackUpdate, TrackRead]):
    def __init__(self):
        super().__init__(
            model=Track,
            repository=TrackRepository,
            read_schema=TrackRead,
            not_found_error_code=errors.TRACK_NOT_FOUND,
        )

    async def _pre_create(
        self, uow: UnitOfWork, obj_in: TrackCreate, creator_id: uuid.UUID | None
    ) -> None:
        if obj_in.release_id is not None:
            if not await uow.releases.get(obj_in.release_id):
                raise AppException(errors.RELEASE_NOT_FOUND)

        if obj_in.isrc:
            if await uow.tracks.get_by_isrc(obj_in.isrc):
                raise AppException(errors.TRACK_ALREADY_EXISTS)

    async def _pre_update(
        self,
        uow: UnitOfWork,
        db_obj: Track,
        obj_in: TrackUpdate,
        updater_id: uuid.UUID | None,
    ) -> None:
        if "release_id" in obj_in.model_fields_set and obj_in.release_id is not None:
            if not await uow.releases.get(obj_in.release_id):
                raise AppException(errors.RELEASE_NOT_FOUND)

        if obj_in.isrc is not None and obj_in.isrc != db_obj.isrc:
            if await uow.tracks.get_by_isrc(obj_in.isrc):
                raise AppException(errors.TRACK_ALREADY_EXISTS)

