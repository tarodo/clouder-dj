from fastapi import Depends

from backend.api.dependencies import get_current_superuser, get_current_user
from backend.api.utils.generic_router import create_crud_router
from backend.core.errors import RELEASE_ALREADY_EXISTS, RELEASE_NOT_FOUND
from backend.schemas.release import ReleaseCreate, ReleaseRead, ReleaseUpdate
from backend.services.release_service import ReleaseService


router = create_crud_router(
    service_dependency=ReleaseService,
    create_schema=ReleaseCreate,
    update_schema=ReleaseUpdate,
    read_schema=ReleaseRead,
    entity_name="Release",
    create_dependencies=[Depends(get_current_superuser)],
    update_dependencies=[Depends(get_current_superuser)],
    delete_dependencies=[Depends(get_current_superuser)],
    get_all_dependencies=[Depends(get_current_user)],
    get_one_dependencies=[Depends(get_current_user)],
    create_error_codes=[RELEASE_ALREADY_EXISTS],
    update_error_codes=[RELEASE_ALREADY_EXISTS, RELEASE_NOT_FOUND],
    get_one_error_codes=[RELEASE_NOT_FOUND],
    delete_error_codes=[RELEASE_NOT_FOUND],
)

