---
id: ARCH-infra-background-tasks
title: "Infrastructure: Background Tasks"
layer: infrastructure
owner: '@team-backend'
version: v1
status: current
created: 2025-06-21
updated: 2025-06-28
tags: [taskiq, redis, worker, async]
depends_on: []
referenced_by: []
---
## Context
This document describes the architecture for asynchronous background task processing using Taskiq. This system is essential for offloading long-running operations from the main API thread, such as data scraping from external sources (e.g., Beatport).

## Structure
- **Broker:** Redis is used as the message broker. A `ListQueueBroker` is configured in `app/broker.py` and initialized in the FastAPI application lifecycle (`app/main.py`).
- **Worker:** A dedicated `worker` service in `docker-compose.yml` runs the Taskiq worker process via the `app/worker.py` entrypoint. It listens for tasks on the Redis queue and executes them.
- **Tasks:** Tasks are defined in the `app/tasks/` module. The primary implemented task is `collect_bp_tracks_task` in `app/tasks/collection_tasks.py`. A new task, `enrich_spotify_data_task`, is planned to handle Spotify data enrichment.
  - `collect_bp_tracks_task` in `app/tasks/collection_tasks.py`: Collects and processes tracks from Beatport.
  - `enrich_spotify_data_task` in `app/tasks/collection_tasks.py`: Enriches existing tracks with data from Spotify.

## Behavior
- API endpoints in `app/api/collection.py` (e.g., `/collect/beatport/collect`, `/collect/spotify/enrich`) call the `.kiq()` method on a task to send a message to the Redis broker.
- The Taskiq worker, running in its own container, picks up the message from the queue.
- The worker executes the task function with the provided arguments. The tasks themselves are now thin wrappers that instantiate and call the appropriate service (e.g., `CollectionService`) to perform the business logic.
- Results and status are stored in the Redis result backend. The status can be queried via the `/tasks/status/{task_id}` endpoint.

## Evolution
### Planned
—

### Historical
- v1: Initial implementation with Redis broker and a worker service. Later refactored to move business logic from tasks into a dedicated `CollectionService`, making tasks thin wrappers. Added the `enrich_spotify_data_task` for Spotify data enrichment.
