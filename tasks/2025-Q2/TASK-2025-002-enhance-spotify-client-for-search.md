---
id: TASK-2025-002
title: "Enhance Spotify Client for Server-to-Server Search"
status: backlog
priority: high
type: feature
estimate: 1d
assignee:
created: 2025-06-27
updated: 2025-06-27
parents: [TASK-2025-001]
children: []
arch_refs: [ARCH-client-spotify]
audit_log:
  - {date: 2025-06-27, user: "@AI-DocArchitect", action: "created with status backlog"}
---
## Description
The `SpotifyAPIClient` needs to be updated to support server-to-server API calls required for the enrichment task. This involves implementing the Client Credentials authentication flow and adding a method to search for tracks by ISRC.

## Acceptance Criteria
- The `SpotifyAPIClient` has a private method (e.g., `_get_client_credentials_token`) that can request and cache an access token from Spotify using the app's `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
- A new public async method `search_track_by_isrc(self, isrc: str) -> dict | None` exists in the client.
- The `search_track_by_isrc` method uses the client credentials token to make a `GET https://api.spotify.com/v1/search` call with `q=isrc:{isrc}` and `type=track`.
- The method correctly handles the API call and returns the JSON response for the first found track, or `None` if no track is found or an error occurs.

## Definition of Done
- Code is implemented in `app/clients/spotify.py`.
- The new methods are covered by unit tests.
