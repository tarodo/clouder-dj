---
id: ARCH-service-category
title: "Service: Category Management"
type: service
layer: application
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-28
updated: 2025-06-28
tags: [service, curation, category, spotify, transaction]
depends_on: [ARCH-data-model-category, ARCH-client-user-spotify]
referenced_by: []
---
## Context
This service is planned to encapsulate all business logic for managing user-defined curation categories. It will act as an orchestrator, coordinating actions between the Spotify API (via the `UserSpotifyClient`) and the application's database (via the `CategoryRepository`).

## Structure
- **Class:** `CategoryService` in `app/services/category.py` (new file).
- **Dependencies:** The service will be initialized with a `CategoryRepository` and a `UserSpotifyClient`.
- **Unit of Work:** All public methods of this service will be designed to run within a single database transaction. A failure at any step (e.g., a Spotify API call fails midway through a bulk operation) will trigger a complete rollback of all database changes made during that operation.

## Behavior
- **`create_categories(...)`**: A transactional method for bulk-creating categories. For each category, it will first call the `UserSpotifyClient` to create a playlist on Spotify. If successful, it will then use the `CategoryRepository` to create the corresponding record in the database. If any Spotify call fails, the entire transaction is rolled back.
- **`update_category(...)`**: Updates a category's name. This involves calling the `UserSpotifyClient` to rename the Spotify playlist and then updating the record in the database. It will gracefully handle cases where the playlist was deleted on Spotify by the user (e.g., by deleting the local category record).
- **`delete_category(...)`**: Deletes a category record from the database. It will also call the `UserSpotifyClient` to unfollow (delete) the corresponding Spotify playlist if requested.

## Evolution
### Planned
- v1: Initial implementation of core CRUD business logic with transactional integrity.

### Historical
- This is a new, planned component.
