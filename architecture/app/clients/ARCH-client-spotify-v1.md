---
id: ARCH-client-spotify
title: "Client: Spotify API"
type: component
layer: infrastructure
owner: '@team-backend'
version: v1
status: current
created: 2025-06-27
updated: 2025-06-28
tags: [spotify, api, client, auth]
depends_on: [] # No ARCH dependencies, but uses settings from app/core/settings.py
referenced_by: []
---
## Context
This component is responsible for all interactions with the external Spotify API. It encapsulates the logic for authentication and data retrieval, providing a clean interface for the application services.

## Structure
- **Class:** `SpotifyAPIClient` in `app/clients/spotify.py`.
- **Dependencies:** It uses `httpx.AsyncClient` for making asynchronous HTTP requests. It is configured via application settings in `app/core/settings.py`.

## Behavior
- **`exchange_code_for_token(...)`**: Exchanges an authorization code, received from the user's login callback, for an access and refresh token. This is part of the user-centric OAuth2 Authorization Code flow.
- **`get_user_profile(...)`**: Fetches the profile information for the authenticated user using their access token.
- **`search_track_by_isrc(isrc: str)`**: Searches for a track on Spotify using its ISRC. This method uses the server-to-server OAuth2 Client Credentials flow, automatically requesting and caching a server-side access token via the internal `_get_client_credentials_token` method. This is used for background track enrichment.

## Evolution
### Planned
- A new `UserSpotifyClient` is planned to handle ongoing, user-authenticated API calls, including automatic token refreshing. See `ARCH-client-user-spotify`.

### Historical
- v1: Initial implementation focused on user authentication (Authorization Code flow). Subsequently enhanced with server-to-server authentication (Client Credentials flow) for background processing and track search by ISRC.
