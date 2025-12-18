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

## Start Project

### Using Make

**Docker deployment:**
```sh
make up
```
Builds and starts all services (backend, database, Redis), runs migrations, and creates a superuser.

**Stop services:**
```sh
make stop
```

**Other useful commands:**
```sh
make format          # Auto-format code (black + ruff)
make check           # Run linting and type checks
make alembic-gen MSG="migration message"  # Generate new migration
make alembic-head    # Apply pending migrations
```

### Testing

The testing setup is optimized to avoid unnecessary Docker image rebuilds, making the test cycle fast and flexible.

**Run all tests:**
```sh
make test-docker
```

**Run specific tests or pass arguments:**

You can pass any `pytest` arguments via the `PYTEST_ARGS` variable.
```sh
# Run tests in a specific file
make test-docker PYTEST_ARGS="tests/api/test_login.py"

# Run tests by keyword matching
make test-docker PYTEST_ARGS="-k 'test_create_user_success' -vv"

# Rebuild the test image if dependencies have changed (e.g., Dockerfile or pyproject.toml changed)
make build-test
```