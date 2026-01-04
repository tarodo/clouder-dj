import uuid

from backend.core import errors
from backend.core.exceptions import AppException
from backend.db.uow import UnitOfWork
from backend.models.release import Release
from backend.repositories.release import ReleaseRepository
from backend.schemas.release import ReleaseCreate, ReleaseRead, ReleaseUpdate
from backend.services.base import GenericService


class ReleaseService(GenericService[Release, ReleaseCreate, ReleaseUpdate, ReleaseRead]):
    def __init__(self):
        super().__init__(
            model=Release,
            repository=ReleaseRepository,
            read_schema=ReleaseRead,
            not_found_error_code=errors.RELEASE_NOT_FOUND,
        )

    async def _pre_create(
        self, uow: UnitOfWork, obj_in: ReleaseCreate, creator_id: uuid.UUID | None
    ) -> None:
        if obj_in.label_id is not None:
            if not await uow.labels.get(obj_in.label_id):
                raise AppException(errors.LABEL_NOT_FOUND)

        if obj_in.label_id and obj_in.code:
            existing = await uow.releases.get_by_label_and_code(
                obj_in.label_id, obj_in.code
            )
            if existing:
                raise AppException(errors.RELEASE_ALREADY_EXISTS)

    async def _pre_update(
        self,
        uow: UnitOfWork,
        db_obj: Release,
        obj_in: ReleaseUpdate,
        updater_id: uuid.UUID | None,
    ) -> None:
        if "label_id" in obj_in.model_fields_set and obj_in.label_id is not None:
            if not await uow.labels.get(obj_in.label_id):
                raise AppException(errors.LABEL_NOT_FOUND)

        target_label_id = (
            obj_in.label_id if "label_id" in obj_in.model_fields_set else db_obj.label_id
        )
        target_code = obj_in.code if "code" in obj_in.model_fields_set else db_obj.code

        if (
            target_label_id is not None
            and target_code is not None
            and ("label_id" in obj_in.model_fields_set or "code" in obj_in.model_fields_set)
        ):
            existing = await uow.releases.get_by_label_and_code(target_label_id, target_code)
            if existing and existing.id != db_obj.id:
                raise AppException(errors.RELEASE_ALREADY_EXISTS)

