from typing import AsyncGenerator

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.spotify import SpotifyAPIClient
from app.core.security import verify_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.services.auth import AuthService
from app.services.user import UserService

log = structlog.get_logger()

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_service = UserService(db)
    try:
        payload = verify_token(credentials.credentials)
    except Exception as e:
        log.warning("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    spotify_id: str | None = payload.get("sub")
    if spotify_id is None:
        log.warning("Could not validate credentials, 'sub' not in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await user_service.get_user_by_spotify_id(spotify_id=spotify_id)
    if user is None:
        log.warning("User not found in DB", spotify_id=spotify_id)
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_spotify_api_client() -> AsyncGenerator[SpotifyAPIClient, None]:
    async with httpx.AsyncClient() as client:
        yield SpotifyAPIClient(client=client)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    spotify_client: SpotifyAPIClient = Depends(get_spotify_api_client),
) -> AuthService:
    """FastAPI dependency to get an instance of AuthService."""
    return AuthService(db=db, spotify_client=spotify_client)
