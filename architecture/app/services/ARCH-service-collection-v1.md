---
id: ARCH-service-collection
title: "Service: Collection"
type: service
layer: application
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-27
updated: 2025-06-27
tags: [collection, beatport, spotify, service, refactoring]
depends_on: [ARCH-service-data-processing, ARCH-infra-background-tasks]
referenced_by: []
---
## Context
This service is planned to centralize the business logic related to data collection and processing orchestration. Currently, this logic is improperly located within the task layer (`app/tasks/collection_tasks.py`), mixing infrastructure concerns with business rules. This refactoring will improve separation of concerns, testability, and maintainability.

## Structure
- **Class:** `CollectionService` in a new file `app/services/collection.py`.
- **Dependencies:** The service will be initialized with dependencies on `BeatportAPIClient`, `ExternalDataRepository`, and `DataProcessingService`.
- **Unit of Work:** The service will be responsible for managing the database transaction (commit/rollback) for the operations it orchestrates.

## Behavior
- **`collect_beatport_tracks_raw(...)`**: Interacts with the `BeatportAPIClient` to fetch raw track data and uses the `ExternalDataRepository` to persist it.
- **`process_unprocessed_beatport_tracks(...)`**: Orchestrates the processing of the collected raw Beatport data by invoking the `DataProcessingService`.
- **`enrich_tracks_with_spotify_data(...)`**: Orchestrates the Spotify enrichment background task. It will fetch tracks missing Spotify data from the `TrackRepository`, call the `SpotifyAPIClient` to search for them by ISRC, and persist the results (both found and not-found) to the `ExternalDataRepository`.

## Evolution
### Planned
- v1: Initial design and implementation. The service will be created and all relevant data collection logic from `collection_tasks.py` will be migrated into it. It will also include the new functionality for Spotify track data enrichment (see `TASK-2025-001`).

### Historical
—
