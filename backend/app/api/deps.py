from typing import AsyncGenerator

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients.spotify import SpotifyAPIClient, UserSpotifyClient
from app.core.security import verify_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.db.uow import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from app.services.category import CategoryService
from app.services.user import UserService

log = structlog.get_logger()

security = HTTPBearer()


async def get_uow() -> AsyncGenerator[SqlAlchemyUnitOfWork, None]:
    uow = SqlAlchemyUnitOfWork(AsyncSessionLocal)
    async with uow:
        yield uow


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> User:
    user_service = UserService(uow.session)
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


async def get_user_spotify_client(
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> AsyncGenerator[UserSpotifyClient, None]:
    if not current_user.spotify_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have a Spotify token linked.",
        )

    token_repo = uow.spotify_tokens
    async with httpx.AsyncClient() as client:
        yield UserSpotifyClient(
            client=client,
            token_repo=token_repo,
            token_obj=current_user.spotify_token,
            spotify_user_id=current_user.spotify_id,
        )


def get_category_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_spotify_client: UserSpotifyClient = Depends(get_user_spotify_client),
) -> CategoryService:
    """FastAPI dependency to get an instance of CategoryService."""
    return CategoryService(
        category_repo=uow.categories,
        style_repo=uow.styles,
        user_spotify_client=user_spotify_client,
    )
