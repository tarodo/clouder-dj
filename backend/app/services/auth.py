import httpx
from fastapi import HTTPException, status
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.core.settings import settings
from app.repositories.spotify_token import SpotifyTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

log = structlog.get_logger()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = SpotifyTokenRepository(db)

    async def handle_spotify_callback(
        self, *, code: str, code_verifier: str
    ) -> dict[str, str]:
        log.info("Handling spotify callback", code_len=len(code))
        token_info = await self._exchange_code_for_token(code, code_verifier)
        user_profile = await self._get_spotify_user_profile(token_info["access_token"])

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

        await self.token_repo.create_or_update(user=user, token_info=token_info)
        log.info("Spotify token created/updated for user", spotify_id=spotify_id)

        access_token = create_access_token(data={"sub": spotify_id})
        refresh_token = create_refresh_token(data={"sub": spotify_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def _exchange_code_for_token(self, code: str, code_verifier: str) -> dict:
        log.info("Exchanging authorization code for token")
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                settings.SPOTIFY_TOKEN_URL, data=token_data
            )
            if token_response.status_code != 200:
                log.error(
                    "Failed to get access token from Spotify",
                    status_code=token_response.status_code,
                    response_text=token_response.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get access token from Spotify",
                )
            log.info("Successfully exchanged code for token")
            return token_response.json()

    async def _get_spotify_user_profile(self, spotify_access_token: str) -> dict:
        log.info("Fetching user profile from Spotify")
        headers = {"Authorization": f"Bearer {spotify_access_token}"}
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(
                settings.SPOTIFY_API_URL, headers=headers
            )
            if profile_response.status_code != 200:
                log.error(
                    "Failed to get user profile from Spotify",
                    status_code=profile_response.status_code,
                    response_text=profile_response.text,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user profile from Spotify",
                )
            profile_data = profile_response.json()
            log.info(
                "Successfully fetched user profile",
                spotify_id=profile_data.get("id"),
                display_name=profile_data.get("display_name"),
            )
            return profile_data
