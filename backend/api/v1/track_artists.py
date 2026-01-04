from fastapi import Depends

from backend.api.dependencies import get_current_superuser, get_current_user
from backend.api.utils.generic_router import create_crud_router
from backend.core.errors import (
    ARTIST_NOT_FOUND,
    TRACK_ARTIST_ALREADY_EXISTS,
    TRACK_ARTIST_NOT_FOUND,
    TRACK_NOT_FOUND,
)
from backend.schemas.track_artist import TrackArtistCreate, TrackArtistRead, TrackArtistUpdate
from backend.services.track_artist_service import TrackArtistService


router = create_crud_router(
    service_dependency=TrackArtistService,
    create_schema=TrackArtistCreate,
    update_schema=TrackArtistUpdate,
    read_schema=TrackArtistRead,
    entity_name="TrackArtist",
    create_dependencies=[Depends(get_current_superuser)],
    update_dependencies=[Depends(get_current_superuser)],
    delete_dependencies=[Depends(get_current_superuser)],
    get_all_dependencies=[Depends(get_current_user)],
    get_one_dependencies=[Depends(get_current_user)],
    create_error_codes=[TRACK_ARTIST_ALREADY_EXISTS, ARTIST_NOT_FOUND, TRACK_NOT_FOUND],
    get_one_error_codes=[TRACK_ARTIST_NOT_FOUND],
    delete_error_codes=[TRACK_ARTIST_NOT_FOUND],
)

