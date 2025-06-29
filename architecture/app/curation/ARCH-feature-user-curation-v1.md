---
id: ARCH-feature-user-curation
title: "Feature: User-Managed Curation Categories"
type: feature
layer: application
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-28
updated: 2025-06-28
tags: [curation, category, spotify, feature]
depends_on: [ARCH-data-model-category, ARCH-service-category, ARCH-client-user-spotify, ARCH-api-curation]
referenced_by: []
---
## Context
This document outlines the design for a new feature enabling users to manage personalized music curation categories. Each category corresponds to a Spotify playlist, managed directly through our application's API. The plan focuses on robust Spotify integration, including seamless token management, transactional integrity for bulk operations, and graceful error handling.

The primary objective is to build a full-featured CRUD API for user-specific curation categories, deeply integrated with the Spotify API for playlist management.

## Structure
This feature will introduce several new components into the existing architecture:
- **Data Model:** A new `Category` model to store category information. See `ARCH-data-model-category`.
- **Repository:** A `CategoryRepository` to manage database operations for the `Category` model.
- **User-Specific Spotify Client:** A new `UserSpotifyClient` responsible for making API calls on behalf of a user, including token refresh logic. See `ARCH-client-user-spotify`.
- **Service Layer:** A `CategoryService` to encapsulate all business logic, orchestrating calls to the Spotify client and the repository. See `ARCH-service-category`.
- **API Layer:** A new set of endpoints under the `/curation` prefix to expose the functionality. See `ARCH-api-curation`.

## Behavior
The typical flow for a user-initiated action (e.g., creating a category) will be:
1. A request hits the new `/curation` API endpoint.
2. The endpoint uses dependencies to get the current `User`, a `CategoryService`, and a user-specific `UserSpotifyClient`.
3. The `CategoryService` orchestrates the operation, first calling the `UserSpotifyClient` to perform the action on Spotify (e.g., create a playlist).
4. The `UserSpotifyClient` automatically handles token refreshing if necessary before making the API call.
5. If the Spotify action is successful, the `CategoryService` uses the `CategoryRepository` to persist changes to our database.
6. The entire service-level operation is wrapped in a single database transaction to ensure atomicity.

## Evolution
### Planned
- v1: Implement the full CRUD functionality as described.

### Historical
- This is a new, planned feature.
