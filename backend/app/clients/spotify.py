import httpx
import structlog
from fastapi import HTTPException, status

from app.core.settings import settings

log = structlog.get_logger()


class SpotifyAPIClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def exchange_code_for_token(self, code: str, code_verifier: str) -> dict:
        log.info("Exchanging authorization code for token")
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "code_verifier": code_verifier,
        }

        token_response = await self.client.post(
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

    async def get_user_profile(self, spotify_access_token: str) -> dict:
        log.info("Fetching user profile from Spotify")
        headers = {"Authorization": f"Bearer {spotify_access_token}"}
        profile_response = await self.client.get(
            f"{settings.SPOTIFY_API_URL}/me", headers=headers
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
