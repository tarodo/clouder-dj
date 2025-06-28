---
id: ARCH-service-collection
title: "Service: Collection"
type: service
layer: application
owner: '@team-backend'
version: v1
status: current
created: 2025-06-27
updated: 2025-06-28
tags: [collection, beatport, spotify, service, refactoring]
depends_on: [ARCH-service-data-processing, ARCH-client-beatport, ARCH-client-spotify]
referenced_by: []
---
## Context
This service centralizes the business logic for data collection and enrichment. It orchestrates interactions with external APIs (like Beatport and Spotify) and internal services to fetch, process, and enrich music data. It was created by refactoring logic out of the task layer (`app/tasks/collection_tasks.py`) to improve separation of concerns.

## Structure
- **Class:** `CollectionService` in `app/services/collection.py`.
- **Dependencies:** The service is initialized with `ExternalDataRepository` and `DataProcessingService`. It also makes use of `BeatportAPIClient` and `SpotifyAPIClient` to interact with external sources.
- **Unit of Work:** The service's methods are designed to be run within a managed database session (unit of work), which is provided by the `get_collection_service` dependency factory in `app/tasks/deps.py`.

## Behavior
- **`collect_beatport_tracks_raw(...)`**: Interacts with the `BeatportAPIClient` to fetch raw track data from Beatport and uses the `ExternalDataRepository` to bulk-upsert it.
- **`process_unprocessed_beatport_tracks(...)`**: Fetches unprocessed Beatport records in batches from `ExternalDataRepository` and orchestrates their processing by invoking the `DataProcessingService`. It reports progress via a callback.
- **`enrich_tracks_with_spotify_data(...)`**: Fetches internal tracks that have an ISRC but are missing a Spotify data link. It uses the `SpotifyAPIClient` to search for them by ISRC and persists the results (both found and not-found) back to the `ExternalDataRepository`. This process also runs in batches and reports progress.

## Evolution
### Planned
—

### Historical
- v1: Initial implementation. The service was created by migrating data collection and processing logic from `collection_tasks.py`. It also includes the new functionality for enriching track data with Spotify information.
