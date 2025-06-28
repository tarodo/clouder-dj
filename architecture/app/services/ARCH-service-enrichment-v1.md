---
id: ARCH-service-enrichment
title: "Service: Enrichment"
type: service
layer: application
owner: '@team-backend'
version: v1
status: current
created: 2025-07-01
updated: 2025-07-01
tags: [enrichment, spotify, service, refactoring]
depends_on: [ARCH-client-spotify]
referenced_by: []
---
## Context
This service is responsible for enriching existing database entities with data from secondary, external sources like Spotify. It was created by refactoring the `CollectionService` to better adhere to the Single Responsibility Principle (SRP). Its primary goal is to take internal entities (like `Track` or `Artist`) and find their counterparts on other platforms, persisting the link and any relevant metadata.

## Structure
- **Class:** `EnrichmentService` in `app/services/enrichment.py`.
- **Dependencies:** The service is initialized with `ArtistRepository`, `TrackRepository`, and `ExternalDataRepository`. It makes heavy use of the `SpotifyAPIClient` to interact with the Spotify API.
- **Unit of Work:** The service's methods are designed to be run within a managed database session, which is provided by the `get_enrichment_service` dependency factory in `app/tasks/deps.py`. All operations within a service method call are part of a single transaction.

## Behavior
- **`enrich_tracks_with_spotify_data(...)`**: Fetches internal tracks that have an ISRC but are missing a Spotify data link. It uses the `SpotifyAPIClient` to search for them by ISRC. It validates the match by comparing artist names and persists the results (both found and not-found) back to the `ExternalDataRepository`. This process runs in batches and reports progress.
- **`enrich_artists_with_spotify_data(...)`**: A more complex enrichment process.
  1. It fetches internal artists that are missing a Spotify data link.
  2. For each artist, it finds associated tracks that *do* have Spotify data.
  3. It collects a list of potential Spotify artist candidates from these associated tracks.
  4. It uses a fuzzy matching algorithm (`rapidfuzz`) to find the most likely correct Spotify artist from the candidates based on name similarity.
  5. It fetches full artist details from the Spotify API for all matched artists.
  6. It persists the results (both found and not-found) back to the `ExternalDataRepository`. This process also runs in batches and reports progress.

## Evolution
### Planned
- This service could be extended to enrich data from other sources (e.g., MusicBrainz, Discogs).
- The matching algorithms could be improved with more sophisticated logic if fuzzy name matching proves insufficient.

### Historical
- v1: Initial implementation. The service was created by migrating all Spotify enrichment logic from the `CollectionService`. The complex `enrich_artists_with_spotify_data` method was internally refactored into smaller, more testable private methods.
