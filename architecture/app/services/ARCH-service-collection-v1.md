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
tags: [collection, beatport, service, refactoring]
depends_on: [ARCH-service-data-processing, ARCH-client-beatport]
referenced_by: []
---
## Context
This service centralizes the business logic for data collection from primary sources (e.g., Beatport). It orchestrates interactions with external APIs and internal services to fetch and process raw music data. It is the first step in the data ingestion pipeline.

## Structure
- **Class:** `CollectionService` in `app/services/collection.py`.
- **Dependencies:** The service is initialized with `ExternalDataRepository` and `DataProcessingService`. It uses the `BeatportAPIClient` to interact with the Beatport API.
- **Unit of Work:** The service's methods are designed to be run within a managed database session (unit of work), which is provided by the `get_collection_service` dependency factory in `app/tasks/deps.py`. All operations within a service method call are part of a single transaction.

## Behavior
- **`collect_beatport_tracks_raw(...)`**: Interacts with the `BeatportAPIClient` to fetch raw track data from Beatport and uses the `ExternalDataRepository` to bulk-upsert it.
- **`process_unprocessed_beatport_tracks(...)`**: Fetches unprocessed Beatport records in batches from `ExternalDataRepository` and orchestrates their processing by invoking the `DataProcessingService`. It reports progress via a callback.

## Evolution
### Planned
- This service will be responsible for collecting data from other primary sources in the future (e.g., Tidal).

### Historical
- v2: Refactored to adhere to the Single Responsibility Principle. All data enrichment logic (e.g., Spotify matching) was moved to the new `EnrichmentService`. The `CollectionService` is now solely focused on initial data collection and processing orchestration.
- v1: Initial implementation. The service was created by migrating data collection, processing, and enrichment logic from `app/tasks/collection_tasks.py`.
