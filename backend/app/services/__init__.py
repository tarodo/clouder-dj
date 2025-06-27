from .auth import AuthService
from .artist import ArtistService
from .collection import CollectionService
from .label import LabelService
from .release import ReleaseService
from .track import TrackService
from .style import StyleService
from .user import UserService

__all__ = [
    "UserService",
    "AuthService",
    "ArtistService",
    "CollectionService",
    "LabelService",
    "ReleaseService",
    "TrackService",
    "StyleService",
]
