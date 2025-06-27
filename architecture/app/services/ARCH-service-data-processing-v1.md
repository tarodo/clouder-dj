---
id: ARCH-service-data-processing
title: "Service: Data Processing"
type: service
layer: application
owner: '@team-backend'
version: v1
status: current
created: 2025-06-27
updated: 2025-06-27
tags: [data, processing, service]
depends_on: []
referenced_by: []
---
## Context
This service is responsible for processing batches of raw `ExternalData` records (e.g., from Beatport) and creating the corresponding normalized entities (Artists, Labels, Releases, Tracks) in the application's database. It encapsulates the complex logic of entity creation and relationship mapping.

## Structure
- **Class:** `DataProcessingService` located in `app/services/data_processing.py`.
- **Dependencies:** It is initialized with a database session (`AsyncSession`) and instances of all core repositories: `ArtistRepository`, `LabelRepository`, `ReleaseRepository`, `TrackRepository`, and `ExternalDataRepository`.

## Behavior
The primary method is `process_batch(records: List[ExternalData])`. This method orchestrates the creation and linking of database entities in a specific, dependency-aware order to ensure relational integrity:
1.  Processes and bulk-creates `Label` entities.
2.  Processes and bulk-creates `Artist` entities.
3.  Processes and bulk-creates `Release` entities, linking them to the previously created labels.
4.  Processes and bulk-creates `Track` entities, linking them to releases and artists.
5.  Updates `ExternalData` records to link them to the newly created internal entities.
The entire batch is processed within a single database transaction, which is committed by this service.

## Evolution
### Historical
- v1: Initial implementation to handle batch processing of Beatport track data.
