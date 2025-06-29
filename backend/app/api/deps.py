from typing import AsyncGenerator

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.spotify import SpotifyAPIClient, UserSpotifyClient
from app.core.security import verify_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.repositories.category import CategoryRepository
from app.repositories.spotify_token import SpotifyTokenRepository
from app.services.auth import AuthService
from app.services.category import CategoryService
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


async def get_user_spotify_client(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UserSpotifyClient, None]:
    if not current_user.spotify_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a Spotify token linked.",
        )

    token_repo = SpotifyTokenRepository(db)
    async with httpx.AsyncClient() as client:
        yield UserSpotifyClient(
            client=client,
            token_repo=token_repo,
            token_obj=current_user.spotify_token,
            spotify_user_id=current_user.spotify_id,
        )


def get_category_service(
    db: AsyncSession = Depends(get_db),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
) -> CategoryService:
    """FastAPI dependency to get an instance of CategoryService."""
    category_repo = CategoryRepository(db)
    return CategoryService(
        category_repo=category_repo, user_spotify_client=user_spotify_client
    )
