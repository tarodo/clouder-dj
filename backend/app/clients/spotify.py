import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog
from fastapi import HTTPException, status

from app.core.security import decrypt_data
from app.core.settings import settings
from app.db.models.spotify_token import SpotifyToken
from app.repositories.spotify_token import SpotifyTokenRepository

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


class SpotifyClientError(Exception):
    """Base exception for Spotify client errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SpotifyUnauthorizedError(SpotifyClientError):
    """Exception for 401 Unauthorized errors."""

    def __init__(self, message: str = "Spotify API access unauthorized."):
        super().__init__(message, status_code=401)


class SpotifyForbiddenError(SpotifyClientError):
    """Exception for 403 Forbidden errors."""

    def __init__(
        self, message: str = "Access to the requested Spotify resource is forbidden."
    ):
        super().__init__(message, status_code=403)


class SpotifyNotFoundError(SpotifyClientError):
    """Exception for 404 Not Found errors."""

    def __init__(self, message: str = "The requested Spotify resource was not found."):
        super().__init__(message, status_code=404)


class UserSpotifyClient:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        token_repo: SpotifyTokenRepository,
        token_obj: SpotifyToken,
        spotify_user_id: str,
    ):
        self.client = client
        self.token_repo = token_repo
        self.token_obj = token_obj
        self.spotify_user_id = spotify_user_id
        self.access_token = decrypt_data(token_obj.encrypted_access_token)
        self.refresh_token = decrypt_data(token_obj.encrypted_refresh_token)

    async def _refresh_access_token(self) -> None:
        log.info("Refreshing Spotify access token", user_id=self.token_obj.user_id)
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        try:
            response = await self.client.post(
                settings.SPOTIFY_TOKEN_URL,
                data=data,
                auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error(
                "Failed to refresh Spotify token",
                user_id=self.token_obj.user_id,
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            raise SpotifyUnauthorizedError("Failed to refresh Spotify token.") from e

        token_data = response.json()
        new_access_token = token_data["access_token"]
        expires_in = token_data["expires_in"]
        new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        await self.token_repo.update_access_token(
            db_token=self.token_obj,
            new_access_token=new_access_token,
            new_expires_at=new_expires_at,
        )
        self.access_token = new_access_token
        log.info(
            "Successfully refreshed Spotify access token",
            user_id=self.token_obj.user_id,
        )

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        response = await self.client.request(method, url, **kwargs)

        if response.status_code == 401:
            log.warning(
                "Received 401 from Spotify, attempting token refresh",
                user_id=self.token_obj.user_id,
            )
            await self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            kwargs["headers"] = headers
            response = await self.client.request(method, url, **kwargs)  # retry

        if response.status_code == 401:
            raise SpotifyUnauthorizedError(
                "Authorization failed even after token refresh."
            )
        if response.status_code == 403:
            raise SpotifyForbiddenError()
        if response.status_code == 404:
            raise SpotifyNotFoundError()

        response.raise_for_status()
        return response

    async def create_playlist(
        self, *, name: str, public: bool, description: str
    ) -> dict:
        """Creates a new playlist for the user."""
        log.info("Creating playlist for user", user_id=self.spotify_user_id, name=name)
        url = f"{settings.SPOTIFY_API_URL}/users/{self.spotify_user_id}/playlists"
        payload = {
            "name": name,
            "public": public,
            "description": description,
        }
        response = await self.request("POST", url, json=payload)
        playlist_data = response.json()
        log.info(
            "Successfully created playlist",
            playlist_id=playlist_data.get("id"),
            user_id=self.spotify_user_id,
        )
        return playlist_data

    async def update_playlist_details(self, *, playlist_id: str, name: str) -> None:
        """Updates a playlist's details."""
        log.info("Updating playlist details", playlist_id=playlist_id, new_name=name)
        url = f"{settings.SPOTIFY_API_URL}/playlists/{playlist_id}"
        payload = {"name": name}
        await self.request("PUT", url, json=payload)
        log.info("Successfully updated playlist", playlist_id=playlist_id)

    async def unfollow_playlist(self, *, playlist_id: str) -> None:
        """Unfollows (deletes) a playlist."""
        log.info("Unfollowing playlist", playlist_id=playlist_id)
        url = f"{settings.SPOTIFY_API_URL}/playlists/{playlist_id}/followers"
        try:
            await self.request("DELETE", url)
            log.info("Successfully unfollowed playlist", playlist_id=playlist_id)
        except SpotifyNotFoundError:
            log.warning(
                "Playlist to unfollow not found on Spotify, likely already deleted.",
                playlist_id=playlist_id,
            )
            # If not found, it's already "unfollowed", so we can pass.
            pass
