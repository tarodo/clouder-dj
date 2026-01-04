from fastapi import Depends

from backend.api.dependencies import get_current_superuser, get_current_user
from backend.api.utils.generic_router import create_crud_router
from backend.core.errors import RELEASE_NOT_FOUND, TRACK_ALREADY_EXISTS, TRACK_NOT_FOUND
from backend.schemas.track import TrackCreate, TrackRead, TrackUpdate
from backend.services.track_service import TrackService


router = create_crud_router(
    service_dependency=TrackService,
    create_schema=TrackCreate,
    update_schema=TrackUpdate,
    read_schema=TrackRead,
    entity_name="Track",
    create_dependencies=[Depends(get_current_superuser)],
    update_dependencies=[Depends(get_current_superuser)],
    delete_dependencies=[Depends(get_current_superuser)],
    get_all_dependencies=[Depends(get_current_user)],
    get_one_dependencies=[Depends(get_current_user)],
    create_error_codes=[TRACK_ALREADY_EXISTS, RELEASE_NOT_FOUND],
    update_error_codes=[TRACK_ALREADY_EXISTS, TRACK_NOT_FOUND, RELEASE_NOT_FOUND],
    get_one_error_codes=[TRACK_NOT_FOUND],
    delete_error_codes=[TRACK_NOT_FOUND],
)

