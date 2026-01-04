from backend.core import errors
from backend.models.artist import Artist
from backend.repositories.artist import ArtistRepository
from backend.schemas.artist import ArtistCreate, ArtistRead, ArtistUpdate
from backend.services.base import GenericService


class ArtistService(GenericService[Artist, ArtistCreate, ArtistUpdate, ArtistRead]):
    def __init__(self):
        super().__init__(
            model=Artist,
            repository=ArtistRepository,
            read_schema=ArtistRead,
            not_found_error_code=errors.ARTIST_NOT_FOUND,
        )

