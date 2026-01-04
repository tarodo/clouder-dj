import uuid

from backend.core import errors
from backend.core.exceptions import AppException
from backend.db.uow import UnitOfWork
from backend.models.label import Label
from backend.repositories.label import LabelRepository
from backend.schemas.label import LabelCreate, LabelRead, LabelUpdate
from backend.services.base import GenericService


class LabelService(GenericService[Label, LabelCreate, LabelUpdate, LabelRead]):
    def __init__(self):
        super().__init__(
            model=Label,
            repository=LabelRepository,
            read_schema=LabelRead,
            not_found_error_code=errors.LABEL_NOT_FOUND,
        )

    async def _pre_create(
        self, uow: UnitOfWork, obj_in: LabelCreate, creator_id: uuid.UUID | None
    ) -> None:
        if await uow.labels.get_by_name(obj_in.name):
            raise AppException(errors.LABEL_ALREADY_EXISTS)
        if obj_in.code and await uow.labels.get_by_code(obj_in.code):
            raise AppException(errors.LABEL_ALREADY_EXISTS)

    async def _pre_update(
        self,
        uow: UnitOfWork,
        db_obj: Label,
        obj_in: LabelUpdate,
        updater_id: uuid.UUID | None,
    ) -> None:
        if obj_in.name is not None and obj_in.name != db_obj.name:
            if await uow.labels.get_by_name(obj_in.name):
                raise AppException(errors.LABEL_ALREADY_EXISTS)

        if obj_in.code is not None and obj_in.code != db_obj.code:
            if await uow.labels.get_by_code(obj_in.code):
                raise AppException(errors.LABEL_ALREADY_EXISTS)

