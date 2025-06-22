from __future__ import annotations

from typing import Any, AsyncGenerator

import httpx
import structlog
from fastapi import HTTPException, status
from urllib.parse import urlparse, parse_qs

log = structlog.get_logger(__name__)

BEATPORT_API_URL = "https://api.beatport.com/v4/catalog"


class BeatportAPIClient:
    """A client for interacting with the Beatport API."""

    def __init__(self, client: httpx.AsyncClient, bp_token: str):
        self.client = client
        self.headers = {"Authorization": f"Bearer {bp_token}"}

    def _extract_params_for_requests(self, url: str) -> dict[str, str]:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        clean_params = {k: v[0] for k, v in params.items()}
        return clean_params

    async def _make_request(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        log.debug("Requesting Beatport API", url=url, params=params)
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            log.error(
                "Beatport API request failed",
                url=e.request.url,
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch data from Beatport.",
            ) from e
        except httpx.RequestError as e:
            log.error("Beatport API request error", url=e.request.url, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error communicating with Beatport.",
            ) from e

        data = response.json()
        log.info(
            "Beatport API request successful",
            url=url,
            page=data.get("page"),
            count=data.get("count"),
            next=data.get("next"),
        )
        return data

    async def get_tracks(
        self, genre_id: int, publish_date_start: str, publish_date_end: str
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        """Asynchronously generates pages of tracks for a given genre and date range."""
        url = f"{BEATPORT_API_URL}/tracks/"
        params: dict[str, Any] = {
            "genre_id": genre_id,
            "publish_date": f"{publish_date_start}:{publish_date_end}",
            "page": 1,
            "per_page": 100,
            "order_by": "-publish_date",
        }

        while True:
            try:
                data = await self._make_request(url, params=params)
                yield data.get("results", [])
                next_url = data.get("next")
                if next_url:
                    params = self._extract_params_for_requests(next_url)
                else:
                    break
            except (HTTPException, Exception) as e:
                log.error(
                    "Beatport API request failed", url=url, params=params, error=str(e)
                )
                break
