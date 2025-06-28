import time

import httpx
import structlog
from fastapi import HTTPException, status

from app.core.settings import settings

log = structlog.get_logger()


class SpotifyAPIClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self._client_credentials_token: str | None = None
        self._client_credentials_token_expires_at: float | None = None

    async def _get_client_credentials_token(self) -> str:
        if (
            self._client_credentials_token
            and self._client_credentials_token_expires_at
            and time.time() < self._client_credentials_token_expires_at
        ):
            return self._client_credentials_token

        log.info("Requesting new client credentials token from Spotify")
        data = {"grant_type": "client_credentials"}

        try:
            response = await self.client.post(
                settings.SPOTIFY_TOKEN_URL,
                data=data,
                auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error(
                "Failed to get client credentials token from Spotify",
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            raise

        token_data = response.json()
        self._client_credentials_token = token_data["access_token"]
        # Add a small buffer (e.g., 60 seconds) to the expiry time
        self._client_credentials_token_expires_at = (
            time.time() + token_data["expires_in"] - 60
        )
        log.info("Successfully obtained new client credentials token")
        assert self._client_credentials_token is not None
        return self._client_credentials_token

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

    async def search_track_by_isrc(self, isrc: str) -> dict | None:
        """Searches for a track on Spotify by its ISRC."""
        log.debug("Searching track by ISRC", isrc=isrc)
        try:
            token = await self._get_client_credentials_token()
        except httpx.HTTPStatusError:
            log.error("Could not obtain token for ISRC search", isrc=isrc)
            return None

        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": f"isrc:{isrc}", "type": "track"}

        try:
            response = await self.client.get(
                f"{settings.SPOTIFY_API_URL}/search", headers=headers, params=params
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.warning(
                "Spotify ISRC search failed",
                isrc=isrc,
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            return None

        data = response.json()
        tracks = data.get("tracks", {}).get("items", [])

        if not tracks:
            log.debug("No track found for ISRC", isrc=isrc)
            return None

        log.info("Found track for ISRC", isrc=isrc, track_id=tracks[0].get("id"))
        return tracks[0]

    async def get_artists_by_ids(self, artist_ids: list[str]) -> list[dict] | None:
        """Fetches details for multiple artists from Spotify by their IDs."""
        if not artist_ids:
            return []

        log.debug("Fetching artists by IDs", count=len(artist_ids))
        try:
            token = await self._get_client_credentials_token()
        except httpx.HTTPStatusError:
            log.error("Could not obtain token for artist search")
            return None

        headers = {"Authorization": f"Bearer {token}"}
        all_artists = []

        # Spotify API allows up to 50 IDs per request
        for i in range(0, len(artist_ids), 50):
            batch_ids = artist_ids[i : i + 50]
            params = {"ids": ",".join(batch_ids)}

            try:
                response = await self.client.get(
                    f"{settings.SPOTIFY_API_URL}/artists",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                log.warning(
                    "Spotify get artists by IDs failed",
                    status_code=e.response.status_code,
                    response_text=e.response.text,
                )
                continue

            data = response.json()
            artists = data.get("artists", [])
            all_artists.extend([artist for artist in artists if artist])

        log.info("Fetched artists from Spotify", count=len(all_artists))
        return all_artists
