from datetime import datetime, timedelta, timezone

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.spotify import SpotifyAPIClient
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_data,
    verify_token,
)
from app.repositories.spotify_token import SpotifyTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

log = structlog.get_logger()


class AuthService:
    def __init__(self, db: AsyncSession, spotify_client: SpotifyAPIClient):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = SpotifyTokenRepository(db)
        self.spotify_client = spotify_client

    async def handle_spotify_callback(
        self, *, code: str, code_verifier: str
    ) -> dict[str, str]:
        log.info("Handling spotify callback", code_len=len(code))
        token_info = await self.spotify_client.exchange_code_for_token(
            code, code_verifier
        )
        user_profile = await self.spotify_client.get_user_profile(
            token_info["access_token"]
        )

        spotify_id = user_profile["id"]

        user = await self.user_repo.get_by_spotify_id(spotify_id=spotify_id)
        if user:
            log.info("User found, updating profile", spotify_id=spotify_id)
            user_in_update = UserUpdate(
                display_name=user_profile.get("display_name"),
                email=user_profile.get("email"),
            )
            user = await self.user_repo.update(db_obj=user, obj_in=user_in_update)
        else:
            log.info("User not found, creating new user", spotify_id=spotify_id)
            user_in_create = UserCreate(
                spotify_id=spotify_id,
                display_name=user_profile.get("display_name"),
                email=user_profile.get("email"),
            )
            user = await self.user_repo.create(obj_in=user_in_create)
            await self.db.flush()  # Flush to get the user ID

        await self.token_repo.create_or_update(user=user, token_info=token_info)
        log.info("Spotify token created/updated for user", spotify_id=spotify_id)

        access_token = create_access_token(data={"sub": spotify_id})
        refresh_token = create_refresh_token(data={"sub": spotify_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "spotify_access_token": token_info["access_token"],
        }

    async def refresh_app_and_spotify_tokens(
        self, refresh_token: str
    ) -> dict[str, str]:
        try:
            payload = verify_token(refresh_token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from e

        spotify_id: str | None = payload.get("sub")
        if not spotify_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        user = await self.user_repo.get_by_spotify_id(spotify_id=spotify_id)
        if not user or not user.spotify_token:
            raise HTTPException(status_code=401, detail="User or token not found")

        spotify_refresh_token = decrypt_data(user.spotify_token.encrypted_refresh_token)
        new_token_info = await self.spotify_client.refresh_token(spotify_refresh_token)

        await self.token_repo.update_tokens(
            db_token=user.spotify_token,
            new_access_token=new_token_info["access_token"],
            new_refresh_token=new_token_info.get(
                "refresh_token", spotify_refresh_token
            ),
            new_expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=new_token_info["expires_in"]),
            scope=new_token_info.get("scope", user.spotify_token.scope),
        )

        return {
            "access_token": create_access_token(data={"sub": spotify_id}),
            "token_type": "bearer",
            "spotify_access_token": new_token_info["access_token"],
        }
