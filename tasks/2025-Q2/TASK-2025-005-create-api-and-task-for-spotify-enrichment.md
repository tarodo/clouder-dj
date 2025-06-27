---
id: TASK-2025-005
title: "Create API Endpoint and Task for Spotify Enrichment"
status: backlog
priority: medium
type: feature
estimate: 1d
assignee:
created: 2025-06-27
updated: 2025-06-27
parents: [TASK-2025-001]
children: []
arch_refs: [ARCH-infra-background-tasks, ARCH-service-collection]
audit_log:
  - {date: 2025-06-27, user: "@AI-DocArchitect", action: "created with status backlog"}
---
## Description
This task exposes the new Spotify enrichment functionality through the background task system and a public API. It involves creating a new Taskiq task function, implementing progress reporting, and adding an API endpoint to trigger the task.

## Acceptance Criteria
- A new `@broker.task` named `collection.enrich_spotify_data` is defined in `app/tasks/collection_tasks.py`.
- The task function is a thin wrapper that uses a dependency provider (`get_collection_service`) to get a service instance and calls the `enrich_tracks_with_spotify_data` method.
- The task function defines a progress callback that it passes to the service. This callback updates the task's result in the result backend via `context.message.task_id`. The reported state includes `total`, `processed`, `found`, `not_found`, and `errors`.
- A new API endpoint `POST /collect/spotify/enrich` is added to the router in `app/api/collection.py`.
- The endpoint is protected by user authentication, calls `enrich_spotify_data_task.kiq()`, and returns a `202 Accepted` response with the `task_id`.

## Definition of Done
- Code is implemented in `app/tasks/collection_tasks.py` and `app/api/collection.py`.
- The API endpoint and task are covered by integration tests.
