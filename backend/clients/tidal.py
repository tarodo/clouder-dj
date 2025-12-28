import httpx
import structlog
from fastapi import HTTPException, status

from backend.core.settings import settings

log = structlog.get_logger()


class TidalAPIClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def exchange_code_for_token(self, code: str, code_verifier: str) -> dict:
        log.info("Exchanging authorization code for TIDAL token")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.TIDAL_REDIRECT_URI,
            "code_verifier": code_verifier,
        }
        # TIDAL usually expects Basic Auth with client_id:client_secret
        auth = (settings.TIDAL_CLIENT_ID, settings.TIDAL_CLIENT_SECRET)

        try:
            response = await self.client.post(
                settings.TIDAL_TOKEN_URL,
                data=data,
                auth=auth,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error(
                "Failed to get access token from TIDAL",
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from TIDAL",
            )

        return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        log.info("Refreshing TIDAL token")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        auth = (settings.TIDAL_CLIENT_ID, settings.TIDAL_CLIENT_SECRET)

        try:
            response = await self.client.post(
                settings.TIDAL_TOKEN_URL,
                data=data,
                auth=auth,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error("Failed to refresh TIDAL token", status_code=e.response.status_code)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh TIDAL token",
            )

        return response.json()

    async def get_user_profile(self, access_token: str) -> dict:
        log.info("Fetching user profile from TIDAL")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "Clouder-DJ/1.0",
            "X-Tidal-Token": settings.TIDAL_CLIENT_ID,
            "Accept": "application/vnd.tidal.v1+json",
        }
        # Using /sessions to get userId
        url = f"{settings.TIDAL_API_URL}/sessions"

        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error(
                "Failed to get user profile from TIDAL",
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user profile from TIDAL",
            )

        return response.json()

