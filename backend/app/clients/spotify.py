import asyncio
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

import httpx
import structlog
from fastapi import HTTPException, status
from email.utils import parsedate_to_datetime

from app.core.exceptions import BaseAPIException
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
        log.info("Exchanging authorization code for token", code_length=len(code))

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "code_verifier": code_verifier,
        }

        start_time = time.time()
        log.debug(
            "Spotify token exchange request started",
            url=settings.SPOTIFY_TOKEN_URL,
            grant_type="authorization_code",
        )

        token_response = await self.client.post(
            settings.SPOTIFY_TOKEN_URL, data=token_data
        )

        duration_ms = (time.time() - start_time) * 1000

        if token_response.status_code != HTTPStatus.OK:
            log.error(
                "Failed to get access token from Spotify",
                status_code=token_response.status_code,
                duration_ms=round(duration_ms, 2),
                response_headers=dict(token_response.headers),
                response_text=token_response.text[:200],
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from Spotify",
            )

        log.info(
            "Successfully exchanged code for token",
            status_code=token_response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return token_response.json()

    async def get_user_profile(self, spotify_access_token: str) -> dict:
        log.info("Fetching user profile from Spotify")

        headers = {"Authorization": f"Bearer {spotify_access_token}"}
        profile_url = f"{settings.SPOTIFY_API_URL}/me"

        start_time = time.time()
        log.debug(
            "Spotify user profile request started",
            url=profile_url,
            method="GET",
        )

        profile_response = await self.client.get(profile_url, headers=headers)
        duration_ms = (time.time() - start_time) * 1000

        if profile_response.status_code != HTTPStatus.OK:
            log.error(
                "Failed to get user profile from Spotify",
                status_code=profile_response.status_code,
                duration_ms=round(duration_ms, 2),
                url=profile_url,
                response_headers=dict(profile_response.headers),
                response_text=profile_response.text[:200],
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user profile from Spotify",
            )

        profile_data = profile_response.json()
        log.info(
            "Successfully fetched user profile",
            status_code=profile_response.status_code,
            duration_ms=round(duration_ms, 2),
            spotify_id=profile_data.get("id"),
            display_name=profile_data.get("display_name"),
            country=profile_data.get("country"),
            followers=profile_data.get("followers", {}).get("total"),
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


class SpotifyClientError(BaseAPIException):
    """Base exception for Spotify client errors."""

    status_code = HTTPStatus.BAD_GATEWAY
    code = "SPOTIFY_CLIENT_ERROR"
    detail = "An unspecified Spotify client error occurred."


class SpotifyUnauthorizedError(SpotifyClientError):
    """Exception for 401 Unauthorized errors."""

    def __init__(self, message: str = "Spotify API access unauthorized."):
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            code="SPOTIFY_UNAUTHORIZED",
            detail=message,
        )


class SpotifyForbiddenError(SpotifyClientError):
    """Exception for 403 Forbidden errors."""

    def __init__(
        self, message: str = "Access to the requested Spotify resource is forbidden."
    ):
        super().__init__(
            status_code=HTTPStatus.FORBIDDEN, code="SPOTIFY_FORBIDDEN", detail=message
        )


class SpotifyNotFoundError(SpotifyClientError):
    """Exception for 404 Not Found errors."""

    def __init__(self, message: str = "The requested Spotify resource was not found."):
        super().__init__(
            status_code=HTTPStatus.NOT_FOUND, code="SPOTIFY_NOT_FOUND", detail=message
        )


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
        self._refresh_lock = asyncio.Lock()
        self._token_revoked = False

        # Log token info for debugging
        log.debug(
            "UserSpotifyClient initialized",
            user_id=self.token_obj.user_id,
            spotify_user_id=self.spotify_user_id,
            token_scope=self.token_obj.scope,
            expires_at=(
                self.token_obj.expires_at.isoformat()
                if self.token_obj.expires_at
                else None
            ),
        )

    def _is_token_expired_or_expiring_soon(self) -> bool:
        """Check if token is expired or will expire within 5 minutes."""
        if not self.token_obj.expires_at:
            return True

        # Add 5 minute buffer
        expiry_buffer = timedelta(minutes=5)
        return datetime.now(timezone.utc) >= (self.token_obj.expires_at - expiry_buffer)

    def _get_safe_url_for_logging(self, url: str) -> str:
        """Get URL for logging, removing query params - might sensitive data."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def _get_request_context(self, method: str, url: str) -> dict[str, Any]:
        """Get structured context for request logging."""
        return {
            "method": method.upper(),
            "url": self._get_safe_url_for_logging(url),
            "user_id": self.token_obj.user_id,
            "spotify_user_id": self.spotify_user_id,
        }

    def _log_request_start(self, method: str, url: str) -> dict[str, Any]:
        """Log the start of an HTTP request and return context."""
        context = self._get_request_context(method, url)
        log.debug("Spotify API request started", **context)
        return context

    def _log_request_success(
        self, context: dict[str, Any], response: httpx.Response, duration_ms: float
    ) -> None:
        """Log successful HTTP response."""
        content_length = len(response.content) if response.content else 0
        log.info(
            "Spotify API request successful",
            **context,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            content_length=content_length,
            rate_limit_remaining=response.headers.get("x-ratelimit-remaining"),
            rate_limit_reset=response.headers.get("x-ratelimit-reset"),
        )

    def _log_request_error(
        self,
        context: dict[str, Any],
        error: Exception,
        duration_ms: float,
        response: httpx.Response | None = None,
    ) -> None:
        """Log HTTP request error."""
        error_context = {
            **context,
            "duration_ms": round(duration_ms, 2),
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        if response is not None:
            error_context.update(
                {
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                    "response_text": (
                        response.text[:500] if response.text else None
                    ),  # Limit size
                }
            )

        log.error("Spotify API request failed", **error_context)

    def _parse_retry_after(self, header_value: str | None) -> float | None:
        """Parse Retry-After header which can be seconds or HTTP-date (RFC7231).
        Returns delay in seconds, or None if cannot parse.
        """
        if not header_value:
            return None
        value = header_value.strip()
        # Try numeric seconds first
        try:
            seconds = float(value)
            if seconds >= 0:
                return seconds
        except (ValueError, TypeError):
            pass
        # Try HTTP-date
        try:
            dt = parsedate_to_datetime(value)
            if dt is not None:
                # Ensure timezone-aware comparison
                now = datetime.now(timezone.utc)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                delta = (dt - now).total_seconds()
                return max(delta, 0.0)
        except Exception:
            return None
        return None

    async def _refresh_access_token(self) -> None:
        log.info("Refreshing Spotify access token", user_id=self.token_obj.user_id)

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        start_time = time.time()
        try:
            log.debug(
                "Spotify token refresh request started",
                user_id=self.token_obj.user_id,
                url=settings.SPOTIFY_TOKEN_URL,
            )

            response = await self.client.post(
                settings.SPOTIFY_TOKEN_URL,
                data=data,
                auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            )

            duration_ms = (time.time() - start_time) * 1000

            response.raise_for_status()

            log.info(
                "Spotify token refresh successful",
                user_id=self.token_obj.user_id,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

        except httpx.HTTPStatusError as e:
            duration_ms = (time.time() - start_time) * 1000

            # Check for revoked refresh token
            error_data = {}
            if e.response.headers.get("content-type", "").startswith(
                "application/json"
            ):
                try:
                    error_data = e.response.json()
                except Exception:
                    pass

            if (
                e.response.status_code == 400
                and error_data.get("error") == "invalid_grant"
            ):
                log.error(
                    "Refresh token revoked, deleting from database",
                    user_id=self.token_obj.user_id,
                    status_code=e.response.status_code,
                    duration_ms=round(duration_ms, 2),
                    error_code=error_data.get("error"),
                    error_description=error_data.get("error_description"),
                    response_text=e.response.text[:200],  # Limit size
                )
                # Delete the revoked token from database
                await self.token_repo.delete_token(user_id=self.token_obj.user_id)
                self._token_revoked = True
                raise SpotifyUnauthorizedError(
                    "Refresh token revoked. Re-authorization required."
                ) from e

            log.error(
                "Failed to refresh Spotify token",
                user_id=self.token_obj.user_id,
                status_code=e.response.status_code,
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                response_headers=dict(e.response.headers),
                response_text=e.response.text[:200],  # Limit size
            )
            raise SpotifyUnauthorizedError("Failed to refresh Spotify token.") from e

        token_data = response.json()
        new_access_token = token_data["access_token"]
        expires_in = token_data["expires_in"]
        new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Spotify may return a new refresh token
        new_refresh_token = token_data.get("refresh_token")

        if new_refresh_token:
            log.debug(
                "Updating both access and refresh tokens",
                user_id=self.token_obj.user_id,
                expires_in_seconds=expires_in,
                has_new_refresh_token=True,
            )
            # Update both access and refresh tokens
            await self.token_repo.update_tokens(
                db_token=self.token_obj,
                new_access_token=new_access_token,
                new_refresh_token=new_refresh_token,
                new_expires_at=new_expires_at,
                scope=token_data.get("scope", self.token_obj.scope),
            )
            self.refresh_token = new_refresh_token
        else:
            log.debug(
                "Updating access token only",
                user_id=self.token_obj.user_id,
                expires_in_seconds=expires_in,
                has_new_refresh_token=False,
            )
            # Update only access token
            await self.token_repo.update_access_token(
                db_token=self.token_obj,
                new_access_token=new_access_token,
                new_expires_at=new_expires_at,
            )

        self.access_token = new_access_token
        log.info(
            "Successfully refreshed Spotify access token",
            user_id=self.token_obj.user_id,
            expires_at=new_expires_at.isoformat(),
            token_scope=token_data.get("scope", self.token_obj.scope),
            refresh_token_updated=bool(new_refresh_token),
        )

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        # Check if token is expired or will expire soon (within 5 minutes)
        if self._is_token_expired_or_expiring_soon() and not self._token_revoked:
            async with self._refresh_lock:
                # If token was already revoked, don't retry
                if self._token_revoked:
                    raise SpotifyUnauthorizedError(
                        "Refresh token revoked. Re-authorization required."
                    )

                # Re-check after acquiring lock
                if self._is_token_expired_or_expiring_soon():
                    log.info(
                        "Token expired or expiring soon, refreshing proactively",
                        user_id=self.token_obj.user_id,
                    )
                    await self._refresh_access_token()

        token_for_request = self.access_token
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token_for_request}"
        kwargs["headers"] = headers

        # Setup logging context
        log_context = self._log_request_start(method, url)

        # Retry logic for server errors
        max_retries = settings.SPOTIFY_MAX_RETRIES
        base_delay = float(settings.SPOTIFY_RETRY_BASE_DELAY_S)
        max_sleep_429 = float(settings.SPOTIFY_429_MAX_SLEEP_S)
        start_time = time.time()

        for attempt in range(max_retries + 1):
            attempt_start = time.time()

            try:
                response = await self.client.request(method, url, **kwargs)
                attempt_duration = (time.time() - attempt_start) * 1000

                # Log attempt result
                if attempt > 0:
                    log.debug(
                        "Spotify API retry attempt completed",
                        **log_context,
                        attempt=attempt + 1,
                        status_code=response.status_code,
                        duration_ms=round(attempt_duration, 2),
                    )

                if response.status_code == HTTPStatus.UNAUTHORIZED:
                    log.warning(
                        "Received 401 from Spotify, attempting token refresh",
                        **log_context,
                        attempt=attempt + 1,
                    )
                    async with self._refresh_lock:
                        # If token was already revoked, don't retry
                        if self._token_revoked:
                            log.info(
                                "Token already revoked, skipping refresh attempt",
                                **log_context,
                            )
                            raise SpotifyUnauthorizedError(
                                "Refresh token revoked. Re-authorization required."
                            )

                        # Re-check if token was already refreshed by another coroutine
                        # while waiting for the lock.
                        if self.access_token == token_for_request:
                            log.info(
                                "Acquired lock, proceeding with refresh",
                                **log_context,
                            )
                            await self._refresh_access_token()
                        else:
                            log.info(
                                "Acquired lock but token was already refreshed",
                                **log_context,
                            )

                        # Retry the request with the new token
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        kwargs["headers"] = headers

                    # Make retry request
                    retry_start = time.time()
                    response = await self.client.request(method, url, **kwargs)
                    retry_duration = (time.time() - retry_start) * 1000

                    log.debug(
                        "Spotify API token refresh retry completed",
                        **log_context,
                        status_code=response.status_code,
                        duration_ms=round(retry_duration, 2),
                    )

                # Handle rate limiting (429 Too Many Requests)
                if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    if attempt < max_retries:
                        retry_after_header = response.headers.get("Retry-After")
                        retry_after_s = self._parse_retry_after(retry_after_header)
                        if retry_after_s is None or retry_after_s <= 0:
                            retry_after_s = base_delay
                        retry_after_s = min(retry_after_s, max_sleep_429)
                        log.warning(
                            "Received 429 from Spotify, retrying after delay",
                            **log_context,
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            retry_after_s=retry_after_s,
                            rate_limit_remaining=response.headers.get(
                                "x-ratelimit-remaining"
                            ),
                            rate_limit_reset=response.headers.get(
                                "x-ratelimit-reset"
                            ),
                            retry_after_header=retry_after_header,
                            duration_ms=round(attempt_duration, 2),
                        )
                        await asyncio.sleep(retry_after_s)
                        continue
                    else:
                        total_duration = (time.time() - start_time) * 1000
                        log.error(
                            "Max retries reached due to Spotify rate limit",
                            **log_context,
                            status_code=response.status_code,
                            max_retries=max_retries,
                            rate_limit_remaining=response.headers.get(
                                "x-ratelimit-remaining"
                            ),
                            rate_limit_reset=response.headers.get(
                                "x-ratelimit-reset"
                            ),
                            retry_after_header=response.headers.get("Retry-After"),
                            total_duration_ms=round(total_duration, 2),
                        )
                        break

                # Check for server errors that should be retried
                if response.status_code in [
                    HTTPStatus.BAD_GATEWAY,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.GATEWAY_TIMEOUT,
                ]:
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)  # exponential backoff
                        log.warning(
                            "Received server error from Spotify, retrying",
                            **log_context,
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay_seconds=delay,
                            duration_ms=round(attempt_duration, 2),
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        total_duration = (time.time() - start_time) * 1000
                        log.error(
                            "Max retries reached for server error",
                            **log_context,
                            status_code=response.status_code,
                            max_retries=max_retries,
                            total_duration_ms=round(total_duration, 2),
                        )
                        self._log_request_error(
                            log_context,
                            Exception(f"Server error after {max_retries} retries"),
                            total_duration,
                            response,
                        )
                        break
                else:
                    # Success or non-retryable error - break out of retry loop
                    break

            except Exception as e:
                attempt_duration = (time.time() - attempt_start) * 1000

                if attempt < max_retries and isinstance(
                    e, (httpx.TimeoutException, httpx.ConnectError)
                ):
                    delay = base_delay * (2**attempt)
                    log.warning(
                        "Network error, retrying Spotify API request",
                        **log_context,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        attempt=attempt + 1,
                        delay_seconds=delay,
                        duration_ms=round(attempt_duration, 2),
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    total_duration = (time.time() - start_time) * 1000
                    self._log_request_error(log_context, e, total_duration)
                    raise

        # Calculate total request duration
        total_duration = (time.time() - start_time) * 1000

        # Handle final response
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            self._log_request_error(
                log_context,
                Exception("Authorization failed even after token refresh"),
                total_duration,
                response,
            )
            raise SpotifyUnauthorizedError(
                "Authorization failed even after token refresh."
            )

        if response.status_code == HTTPStatus.FORBIDDEN:
            self._log_request_error(
                log_context, Exception("Access forbidden"), total_duration, response
            )
            raise SpotifyForbiddenError()

        if response.status_code == HTTPStatus.NOT_FOUND:
            self._log_request_error(
                log_context, Exception("Resource not found"), total_duration, response
            )
            raise SpotifyNotFoundError()

        try:
            response.raise_for_status()
            # Log successful request
            self._log_request_success(log_context, response, total_duration)
            return response
        except httpx.HTTPStatusError as e:
            self._log_request_error(log_context, e, total_duration, response)
            raise

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

        # Log detailed playlist info for debugging
        log.info(
            "Successfully created playlist",
            playlist_id=playlist_data.get("id"),
            playlist_name=playlist_data.get("name"),
            is_public=playlist_data.get("public"),
            owner_id=playlist_data.get("owner", {}).get("id"),
            expected_owner=self.spotify_user_id,
            owner_match=playlist_data.get("owner", {}).get("id")
            == self.spotify_user_id,
            collaborative=playlist_data.get("collaborative"),
            followers_total=playlist_data.get("followers", {}).get("total", 0),
        )
        return playlist_data

    async def get_playlist(self, *, playlist_id: str) -> dict:
        """
        Fetches a playlist's metadata from Spotify.
        """
        log.info("Fetching playlist metadata", playlist_id=playlist_id)
        url = f"{settings.SPOTIFY_API_URL}/playlists/{playlist_id}"
        # We don't need all the track data here, just playlist metadata
        params = {"fields": "id,name,description,external_urls,owner,uri,tracks.total"}
        response = await self.request("GET", url, params=params)
        return response.json()

    async def get_playlist_all_items(self, *, playlist_id: str) -> list[dict]:
        """
        Fetches all track items from a Spotify playlist, handling pagination.
        Returns a list of track objects from the playlist items.
        """
        log.info("Fetching all items from playlist", playlist_id=playlist_id)
        all_track_items: list[dict] = []
        url: str | None = f"{settings.SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
        params: dict[str, Any] | None = {
            "limit": 50,
            "fields": "items(track(uri)),next",
        }

        page_num = 0
        while url:
            page_num += 1
            log.debug(
                "Fetching page of playlist items",
                playlist_id=playlist_id,
                page=page_num,
                url=url,
            )
            try:
                response = await self.request("GET", url, params=params)
                # After the first request, the full URL is in `data.get("next")`,
                # so we don't need params anymore.
                params = None
                data = response.json()

                items = data.get("items", [])
                for item in items:
                    if item and (track := item.get("track")) and track.get("uri"):
                        all_track_items.append(track)

                url = data.get("next")

            except httpx.HTTPStatusError as e:
                log.error(
                    "Failed to fetch playlist items from Spotify",
                    playlist_id=playlist_id,
                    url=url,
                    status_code=e.response.status_code,
                )
                # For now, we break the loop on error.
                break

        log.info(
            "Successfully fetched all items from playlist",
            playlist_id=playlist_id,
            count=len(all_track_items),
        )
        return all_track_items

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

    async def add_items_to_playlist(
        self, *, playlist_id: str, track_uris: list[str]
    ) -> None:
        """Adds items to a playlist, handling batching for more than 100 items."""
        if not track_uris:
            return

        log.info(
            "Adding items to playlist",
            playlist_id=playlist_id,
            count=len(track_uris),
            user_id=self.spotify_user_id,
        )
        url = f"{settings.SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"

        # Spotify API allows a maximum of 100 items per request
        for i in range(0, len(track_uris), 100):
            batch_uris = track_uris[i : i + 100]
            batch_start = i + 1
            batch_end = min(i + 100, len(track_uris))

            log.debug(
                "Adding batch of tracks to playlist",
                playlist_id=playlist_id,
                batch_start=batch_start,
                batch_end=batch_end,
                batch_size=len(batch_uris),
                user_id=self.spotify_user_id,
            )

            payload = {"uris": batch_uris}
            try:
                await self.request("POST", url, json=payload)
                log.debug(
                    "Successfully added batch to playlist",
                    playlist_id=playlist_id,
                    batch_start=batch_start,
                    batch_end=batch_end,
                )
            except Exception as e:
                log.error(
                    "Failed to add batch to playlist",
                    playlist_id=playlist_id,
                    batch_start=batch_start,
                    batch_end=batch_end,
                    batch_uris_sample=batch_uris[:3],  # First 3 URIs for debugging
                    user_id=self.spotify_user_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        log.info(
            "Successfully added items to playlist",
            playlist_id=playlist_id,
            count=len(track_uris),
        )

    async def get_playlist_items(self, *, playlist_id: str) -> list[str]:
        """
        Fetches all track URIs from a Spotify playlist, handling pagination.
        """
        log.info("Fetching all items from playlist", playlist_id=playlist_id)
        all_track_uris: list[str] = []
        url: str | None = f"{settings.SPOTIFY_API_URL}/playlists/{playlist_id}/tracks"
        params: dict[str, Any] | None = {
            "limit": 50,
            "fields": "items(track(uri)),next",
        }

        while url:
            try:
                response = await self.request("GET", url, params=params)
                # After the first request, the full URL is in `data.get("next")`,
                # so we don't need params anymore.
                params = None
                data = response.json()

                items = data.get("items", [])
                for item in items:
                    if (
                        item
                        and (track := item.get("track"))
                        and (uri := track.get("uri"))
                    ):
                        all_track_uris.append(uri)

                url = data.get("next")

            except httpx.HTTPStatusError as e:
                log.error(
                    "Failed to fetch playlist items from Spotify",
                    playlist_id=playlist_id,
                    url=url,
                    status_code=e.response.status_code,
                )
                # For now, we break the loop on error.
                break

        log.info(
            "Successfully fetched all items from playlist",
            playlist_id=playlist_id,
            count=len(all_track_uris),
        )
        return all_track_uris
