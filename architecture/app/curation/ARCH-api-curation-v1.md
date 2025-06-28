---
id: ARCH-api-curation
title: "API: Curation Endpoints"
type: feature
layer: presentation
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-28
updated: 2025-06-28
tags: [api, curation, category, spotify]
depends_on: [ARCH-service-category]
referenced_by: []
---
## Context
This document outlines the planned API endpoints for managing user-specific curation categories. These endpoints will form a new router prefixed with `/curation` and will be protected by user authentication.

## Structure
- **Module:** `app/api/category.py` (new file)
- **Router:** A new `APIRouter` will be created and included in `app/main.py`.
- **Dependencies:** Endpoints will use `get_current_user`, a new `get_category_service`, and a new `get_user_spotify_client` dependency.
- **Schemas:** New Pydantic schemas will be defined in `app/schemas/category.py` for request and response models (`Category`, `CategoryCreate`, `CategoryUpdate`, etc.).

## Behavior
The API will expose full CRUD functionality for user-managed categories.

### `POST /curation/styles/{style_id}/categories`
- **Description:** Creates one or more new categories for the current user and a given style. This is a transactional operation that creates both a Spotify playlist and a database record for each category.
- **Request Body:** `List[CategoryCreate]` (e.g., `[{ "name": "string", "is_public": false }]`)
- **Response Body (201):** `List[CategoryCreateResponse]` (e.g., `[{ "name": "string", "spotify_playlist_id": "string", ... }]`)

### `GET /curation/styles/{style_id}/categories`
- **Description:** Lists all categories for the current user and a given style.
- **Response Body (200):** `List[Category]`

### `PATCH /curation/categories/{category_id}`
- **Description:** Updates the name of a category and its corresponding Spotify playlist.
- **Request Body:** `CategoryUpdate` (e.g., `{ "name": "string" }`)
- **Response Body (200):** `Category`

### `DELETE /curation/categories/{category_id}`
- **Description:** Deletes a category from the database and optionally from Spotify.
- **Query Parameters:** `delete_on_spotify: bool = False`
- **Response Body (204):** None

## Evolution
### Planned
- v1: Initial implementation of all CRUD endpoints.

### Historical
- This is a new, planned component.
