---
id: ARCH-client-spotify
title: "Client: Spotify API"
type: component
layer: infrastructure
owner: '@team-backend'
version: v1
status: current
created: 2025-06-27
updated: 2025-06-27
tags: [spotify, api, client, auth]
depends_on: []
referenced_by: []
---
## Context
This component is responsible for all interactions with the external Spotify API. It encapsulates the logic for authentication and data retrieval, providing a clean interface for the application services.

## Structure
- **Class:** `SpotifyAPIClient` in `app/clients/spotify.py`.
- **Dependencies:** It uses `httpx.AsyncClient` for making asynchronous HTTP requests. It is configured via application settings in `app/core/settings.py`.

## Behavior
The client currently supports the user-centric OAuth2 Authorization Code flow.

- **`exchange_code_for_token(...)`**: Exchanges an authorization code, received from the user's login callback, for an access and refresh token.
- **`get_user_profile(...)`**: Fetches the profile information for the authenticated user using their access token.

## Evolution
### Planned
- **Server-to-Server Authentication**: The client will be enhanced to support the OAuth2 Client Credentials flow. This is necessary for background tasks that need to access the Spotify API without a user context, such as the track enrichment job. This will involve a method to request and cache a server-side access token.
- **Track Search Functionality**: A new method, `search_track_by_isrc(isrc: str)`, will be added. It will use the server-to-server token to search for tracks on Spotify using their ISRC. This is a key component for the track enrichment feature (see `TASK-2025-002`).

### Historical
- v1: Initial implementation focused on user authentication via the Authorization Code flow.
