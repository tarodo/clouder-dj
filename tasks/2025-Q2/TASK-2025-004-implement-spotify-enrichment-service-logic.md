---
id: TASK-2025-004
title: "Implement Spotify Enrichment Logic in Collection Service"
status: backlog
priority: high
type: feature
estimate: 2d
assignee:
created: 2025-06-27
updated: 2025-06-27
parents: [TASK-2025-001]
children: []
arch_refs: [ARCH-service-collection]
audit_log:
  - {date: 2025-06-27, user: "@AI-DocArchitect", action: "created with status backlog"}
---
## Description
This task involves implementing the core business logic for the track enrichment process within the `CollectionService`. This service method will orchestrate fetching track batches, calling the Spotify client, processing results, and preparing data for persistence. It will also use new configuration settings.

## Acceptance Criteria
- A new public async method `enrich_tracks_with_spotify_data` is created in `CollectionService`. It accepts a progress callback function.
- The method contains a `while` loop that calls `TrackRepository.get_tracks_missing_spotify_link` with an incrementing offset to process all eligible tracks in batches.
- The batch size is read from a new `SPOTIFY_SEARCH_BATCH_SIZE` setting in `app/core/settings.py`.
- Inside the loop, it iterates through the batch, calls `SpotifyAPIClient.search_track_by_isrc`, and handles potential API errors with a configurable sleep duration (`SPOTIFY_API_ERROR_SLEEP_S` setting).
- A simple artist name matching logic is implemented to validate search results (e.g., at least one artist name from the local track matches an artist from the Spotify result).
- The method prepares `ExternalData` records for `bulk_upsert`.
  - For found tracks, the record includes the Spotify ID and raw API data.
  - For not-found tracks, a placeholder record is created with a unique `external_id` (e.g., `f"NOT_FOUND_{track.id}_{uuid.uuid4()}"`) and `raw_data` indicating the status (e.g., `{"status": "not_found_by_isrc"}`).

## Definition of Done
- Code is implemented in `app/services/collection.py` and `app/core/settings.py`.
- The new service method is covered by unit tests.
