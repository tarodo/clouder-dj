---
id: ARCH-infra-background-tasks
title: "Infrastructure: Background Task Processing"
type: component
layer: infrastructure
owner: '@team-backend'
version: v1
status: planned
created: 2025-06-21
updated: 2025-06-21
tags: [taskiq, redis, worker, async]
depends_on: []
referenced_by: []
---
## Context
This document describes the planned architecture for asynchronous background task processing using Taskiq. This system is essential for offloading long-running operations from the main API thread, such as data scraping from external sources (e.g., Beatport) and data enrichment (e.g., finding matches on Spotify).

## Structure
- **Broker:** Redis will be used as the message broker. The existing `redis` service in `docker-compose.yml` will be utilized.
- **Taskiq Integration:** A Taskiq `AsyncBroker` instance will be configured within the FastAPI application to allow API endpoints to send tasks to the broker.
- **Worker:** A dedicated `worker` service will be added to `docker-compose.yml`. This service will run the Taskiq worker process, which listens for tasks on the Redis queue and executes them.
- **Tasks:** Tasks will be defined in a dedicated module, e.g., `app/tasks/`. The initial implementation will include a simple test task to verify the setup.

## Behavior
- An API endpoint or another service calls `task.kiq()` to send a task message to the Redis broker.
- The Taskiq worker, running in its own container, picks up the message from the queue.
- The worker executes the task function with the provided arguments.
- Results (if any) can be stored or retrieved via Taskiq's result backend mechanism, which will also be configured to use Redis.

## Evolution
### Planned
- v1: Initial setup with Redis broker, a dedicated worker service, and a simple test task.
- Future: Implement specific tasks for Beatport scraping and Spotify data enrichment.

### Historical
—
