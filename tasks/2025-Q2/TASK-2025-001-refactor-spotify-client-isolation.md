---
id: TASK-2025-001
title: "Refactoring: Isolate Spotify API Dependencies"
status: backlog
priority: high
type: tech_debt
estimate: 4h
assignee:
created: 2025-06-20
updated: 2025-06-20
parents: []
children: []
arch_refs: []
audit_log:
  - {date: 2025-06-20, user: "@AI-DocArchitect", action: "created with status backlog"}
---
## Description
This task focuses on isolating the logic for interacting with the external Spotify API. Currently, the `AuthService` in `app/services/auth.py` directly uses `httpx` to make HTTP requests to Spotify for token exchange and user profile retrieval. This mixes the business logic of authentication with the implementation details of an external API client, making it harder to test and reuse.

The goal is to extract all Spotify API calls into a dedicated, easily testable client.

## Acceptance Criteria
- A new file `app/clients/spotify.py` is created, containing a `SpotifyAPIClient` class.
- The logic from the `_exchange_code_for_token` and `_get_spotify_user_profile` methods in `AuthService` is moved into the new `SpotifyAPIClient`.
- The `AuthService` is refactored to use an instance of `SpotifyAPIClient` via dependency injection.
- The existing authentication flow (`/auth/login` and `/auth/callback`) continues to function exactly as before from a user's perspective.

## Definition of Done
- Code is implemented as per the acceptance criteria.
- Unit tests are created for `SpotifyAPIClient` (using a mocked `httpx.AsyncClient`).
- Existing tests for the authentication flow are updated and pass.
- The application runs and the authentication flow is fully functional.
