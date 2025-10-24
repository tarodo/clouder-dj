from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    ENCRYPTION_KEY: str
    JWT_SECRET: str
    JWT_ALGO: str = "HS256"
    BASE_URL: str = "http://localhost:8000"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SPOTIFY_AUTH_URL: str = "https://accounts.spotify.com/authorize"
    SPOTIFY_TOKEN_URL: str = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_URL: str = "https://api.spotify.com/v1"
    SPOTIFY_SCOPES: str = (
        "user-read-email user-read-private "
        "playlist-modify-public playlist-modify-private"
    )

    CORS_ALLOW_ORIGINS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_RENDERER: str = "console"  # "console" for development, "json" for production

    # Redis for Taskiq
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Security
    SECURE_COOKIES: bool = True

    # Spotify Client retry/backoff
    SPOTIFY_MAX_RETRIES: int = 3
    SPOTIFY_RETRY_BASE_DELAY_S: float = 1.0
    SPOTIFY_429_MAX_SLEEP_S: float = 60.0

    # Spotify Enrichment Task
    SPOTIFY_SEARCH_BATCH_SIZE: int = 50
    SPOTIFY_API_ERROR_SLEEP_S: int = 5

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SPOTIFY_REDIRECT_URI(self) -> str:
        """Get the Spotify redirect URI."""
        return f"{self.BASE_URL}/auth/callback"

    @property
    def redis_url(self) -> str:
        """Get the Redis URL for Taskiq."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


settings = Settings()  # type: ignore[call-arg]
