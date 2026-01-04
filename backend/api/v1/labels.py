from fastapi import Depends

from backend.api.dependencies import get_current_superuser, get_current_user
from backend.api.utils.generic_router import create_crud_router
from backend.core.errors import LABEL_ALREADY_EXISTS, LABEL_NOT_FOUND
from backend.schemas.label import LabelCreate, LabelRead, LabelUpdate
from backend.services.label_service import LabelService


router = create_crud_router(
    service_dependency=LabelService,
    create_schema=LabelCreate,
    update_schema=LabelUpdate,
    read_schema=LabelRead,
    entity_name="Label",
    create_dependencies=[Depends(get_current_superuser)],
    update_dependencies=[Depends(get_current_superuser)],
    delete_dependencies=[Depends(get_current_superuser)],
    get_all_dependencies=[Depends(get_current_user)],
    get_one_dependencies=[Depends(get_current_user)],
    create_error_codes=[LABEL_ALREADY_EXISTS],
    update_error_codes=[LABEL_ALREADY_EXISTS, LABEL_NOT_FOUND],
    get_one_error_codes=[LABEL_NOT_FOUND],
    delete_error_codes=[LABEL_NOT_FOUND],
)

