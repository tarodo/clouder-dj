---
id: ARCH-client-beatport
title: "Client: Beatport API"
type: component
layer: infrastructure
owner: '@team-backend'
version: v1
status: current
created: 2025-06-28
updated: 2025-06-28
tags: [beatport, api, client]
depends_on: []
referenced_by: []
---
## Context
This component is responsible for all interactions with the external Beatport API. It encapsulates the logic for fetching track data based on genre and date ranges.

## Structure
- **Class:** `BeatportAPIClient` in `app/clients/beatport.py`.
- **Dependencies:** It uses `httpx.AsyncClient` for making asynchronous HTTP requests and requires a Beatport authorization token for its headers.

## Behavior
- **`get_tracks(...)`**: An asynchronous generator that fetches paginated track data for a given genre ID and date range. It handles pagination by following the `next` URL provided by the Beatport API.

## Evolution
### Historical
- v1: Initial implementation for fetching track data.
