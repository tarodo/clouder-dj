from .user import User  # noqa: F401
from .spotify_token import SpotifyToken  # noqa: F401
from .artist import Artist  # noqa: F401
from .label import Label  # noqa: F401
from .release import Release  # noqa: F401
from .track import Track, track_artists  # noqa: F401
from .external_data import ExternalData  # noqa: F401
from .style import Style  # noqa: F401

# from .other_model import OtherModel  # Добавляй сюда новые модели

__all__ = [
    "User",
    "SpotifyToken",
    "Artist",
    "Label",
    "Release",
    "Track",
    "track_artists",
    "ExternalData",
    "Style",
]
