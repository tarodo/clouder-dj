---
id: ARCH-client-user-spotify
title: "Client: User-Specific Spotify Client"
type: component
layer: infrastructure
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-28
updated: 2025-06-28
tags: [spotify, api, client, auth, user, token-refresh]
depends_on: [ARCH-client-spotify]
referenced_by: []
---
## Context
This component is planned to handle all Spotify API calls made on behalf of a specific, authenticated user. It will encapsulate the critical logic for automatically refreshing expired access tokens, ensuring uninterrupted service for long-running user sessions. This contrasts with the existing `SpotifyAPIClient` which is primarily for server-to-server communication.

## Structure
- **Class:** `UserSpotifyClient` (new class, likely in `app/clients/spotify.py`).
- **Initialization:** The client will be initialized with the user's token data (access and refresh tokens) and a database session or repository to persist updated tokens after a refresh.
- **Dependency Injection:** A new FastAPI dependency, `get_user_spotify_client` (in `app/api/deps.py`), will be created. This dependency will be responsible for fetching the current user's token from the database, decrypting it, and providing an initialized `UserSpotifyClient` instance to the API layer.

## Behavior
- **Automatic Token Refresh:** Before making any API request to Spotify, the client will check if the user's `access_token` is expired. If it is, the client will use the `refresh_token` to request a new `access_token` from Spotify.
- **Token Persistence:** Upon a successful refresh, the client will use the provided database session/repository to update the `SpotifyToken` record in the database with the new `access_token` and its expiry time.
- **Error Handling:** The client will be designed to handle common Spotify API errors (e.g., 401, 403, 404) and raise specific, catchable exceptions.
- **Playlist Management:** It will contain methods for user-specific actions, such as `create_playlist`, `update_playlist_details`, and `unfollow_playlist`.

## Evolution
### Planned
- v1: Initial implementation with core token refresh logic and methods for playlist management (create, update, delete).
- Future versions could incorporate more sophisticated error handling, such as retry mechanisms with exponential backoff for rate-limiting errors (429).

### Historical
- This is a new, planned component.
