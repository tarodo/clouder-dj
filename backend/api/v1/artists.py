from fastapi import Depends

from backend.api.dependencies import get_current_superuser, get_current_user
from backend.api.utils.generic_router import create_crud_router
from backend.core.errors import ARTIST_NOT_FOUND
from backend.schemas.artist import ArtistCreate, ArtistRead, ArtistUpdate
from backend.services.artist_service import ArtistService


router = create_crud_router(
    service_dependency=ArtistService,
    create_schema=ArtistCreate,
    update_schema=ArtistUpdate,
    read_schema=ArtistRead,
    entity_name="Artist",
    create_dependencies=[Depends(get_current_superuser)],
    update_dependencies=[Depends(get_current_superuser)],
    delete_dependencies=[Depends(get_current_superuser)],
    get_all_dependencies=[Depends(get_current_user)],
    get_one_dependencies=[Depends(get_current_user)],
    get_one_error_codes=[ARTIST_NOT_FOUND],
    delete_error_codes=[ARTIST_NOT_FOUND],
)

