# Clouder-DJ

A collaborative music queueing service with Spotify integration and support for external data sources (Beatport, Tidal, etc).

## Architecture

- **backend/** — FastAPI, async Python, PostgreSQL, Redis, OAuth2 via Spotify, structured logging, Alembic, Taskiq. See [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md) for the detailed application architecture.
- **db/** — service files for dev environment (env, volume).
- **docker-compose.yml** — dev stack: backend, db (Postgres), redis.

### Key backend entities
- User, SpotifyToken, Track, Artist, Release, Label, ExternalData
- Authentication via Spotify OAuth2 (PKCE)
- Async SQLAlchemy, Alembic migrations
- Logging with structlog

## How to run in dev mode

1. Copy the env file:
   ```bash
   cp backend/.env.dev.example backend/.env.dev
   ```
2. Start the dev stack:
   ```bash
   make dev
   ```
   The backend will be available at http://localhost:8000

> For details and make targets, see [backend/README.md](backend/README.md)
