from backend.models.artist import Artist
from backend.repositories.base import BaseRepository


class ArtistRepository(BaseRepository[Artist]):
    model = Artist

