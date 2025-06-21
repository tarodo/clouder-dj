---
id: TASK-2025-002
title: "Configure taskiq Broker and Worker"
status: backlog
priority: medium
type: feature
estimate: 4h
assignee:
created: 2025-06-21
updated: 2025-06-21
parents: []
children: []
arch_refs: [ARCH-infra-background-tasks]
audit_log:
  - {date: 2025-06-21, user: "@AI-DocArchitect", action: "created with status backlog"}
---
## Description
Set up the necessary infrastructure for running asynchronous background tasks using taskiq. This involves configuring the broker connection (Redis) and setting up a dedicated worker service.

## Acceptance Criteria
- The taskiq broker is configured in the FastAPI application to use the existing Redis service.
- A new `worker` service is added to `docker-compose.yml`.
- The `worker` service runs the `taskiq` worker process.
- A simple test task (e.g., a 'hello world' logger task) is created and can be successfully executed.

## Definition of Done
- Code is written and committed.
- The new `worker` service runs correctly with `make dev`.

## Notes
- This is a foundational step for implementing features like data scraping and enrichment.
- The existing Redis service in `docker-compose.yml` should be used as the broker.
