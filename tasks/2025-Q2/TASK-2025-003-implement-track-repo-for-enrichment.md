---
id: TASK-2025-003
title: "Implement Track Repository Method for Enrichment"
status: backlog
priority: high
type: feature
estimate: 1d
assignee:
created: 2025-06-27
updated: 2025-06-27
parents: [TASK-2025-001]
children: []
arch_refs: []
audit_log:
  - {date: 2025-06-27, user: "@AI-DocArchitect", action: "created with status backlog"}
---
## Description
To efficiently process tracks that need Spotify enrichment, a new method must be added to the `TrackRepository`. This method will query the database for batches of tracks that have an ISRC but do not yet have a corresponding `SPOTIFY` entry in the `external_data` table.

## Acceptance Criteria
- A new async method `get_tracks_missing_spotify_link(self, *, offset: int, limit: int) -> Tuple[List[Track], int]` is implemented in `app/repositories/track.py`.
- The method uses an efficient query (e.g., `LEFT JOIN` or `NOT EXISTS` subquery) to select tracks where `isrc` is not null and no `ExternalData` record exists for the `SPOTIFY` provider and that track.
- The method returns both a list of `Track` objects for the current batch and the total count of all such tracks in the database for progress reporting.
- The returned `Track` objects must have their `artists` relationship preloaded to be used in the service layer logic.

## Definition of Done
- Code is implemented in `app/repositories/track.py`.
- The new method is covered by unit tests.
