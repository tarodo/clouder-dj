---
id: ARCH-infra-background-tasks
title: "Infrastructure: Background Tasks"
layer: infrastructure
owner: '@team-backend'
version: v1
status: current
created: 2025-06-21
updated: 2025-06-27
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

## Behavior
- The `/collect/beatport` API endpoint (`app/api/collection.py`) receives a request and calls `collect_bp_tracks_task.kiq()` to send a task message to the Redis broker.
- The Taskiq worker, running in its own container, picks up the message from the queue.
- The worker executes the task function with the provided arguments.
- Results and status are stored in the Redis result backend. The status can be queried via the `/tasks/status/{task_id}` endpoint.
- **Architectural Issue**: The `collect_bp_tracks_task` currently contains significant business logic, including direct database session management and repository instantiation. This violates the principle of thin task layers.

## Evolution
### Planned
- **Refactoring**: Move all business logic out of `app/tasks/collection_tasks.py` and into the `CollectionService`. The task will be refactored to be a thin wrapper that calls this service.
- **New Enrichment Task**: Addition of a new background task for enriching track data with Spotify information (see `TASK-2025-001`). This task will follow the new "thin task, fat service" pattern.

### Historical
- v1: Initial implementation with Redis broker, a dedicated worker service, and a data collection task that contains business logic.
