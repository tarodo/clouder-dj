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
    SPOTIFY_SCOPES: str = "user-read-email user-read-private"

    CORS_ALLOW_ORIGINS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_RENDERER: str = "console"  # "console" for development, "json" for production

    # Security
    SECURE_COOKIES: bool = True

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SPOTIFY_REDIRECT_URI(self) -> str:
        """Get the Spotify redirect URI."""
        return f"{self.BASE_URL}/auth/callback"


settings = Settings()  # type: ignore[call-arg]
