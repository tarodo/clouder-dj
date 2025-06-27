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
tags: [collection, beatport, service, refactoring]
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
- **`collect_beatport_tracks_raw(...)`**: This method will be responsible for interacting with the `BeatportAPIClient` to fetch raw track data and using the `ExternalDataRepository` to persist this raw data. This logic will be moved from `_collect_raw_tracks_data` in the task file.
- **`process_unprocessed_beatport_tracks(...)`**: This method will orchestrate the processing of the collected raw data by invoking the `DataProcessingService`. This logic will be moved from `_process_collected_tracks_data` in the task file.

## Evolution
### Planned
- v1: Initial design and implementation as part of a major refactoring effort (see `TASK-2025-003`). The service will be created and all relevant logic from `collection_tasks.py` will be migrated into it.

### Historical
—
