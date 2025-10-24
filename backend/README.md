# Backend Service

Backend FastAPI service. Development and deployment are done exclusively via Docker Compose and Makefile.

## Quick start (dev)

1. Copy the env file:
    ```bash
    cp backend/.env.example backend/.env
    ```
2. Start the dev stack:
    ```bash
    make dev
    ```
    The backend will be available at `http://localhost:8000`.

## Make targets

- `make dev` — Launches the dev stack via Docker Compose (backend, db, redis)
- `make lint` — Lint code (ruff, mypy)
- `make format` — Format code (ruff, black)
- `make test` — Run tests (pytest)
- `make docker-build` — Build the backend Docker image

## Compose services

- `backend` — FastAPI application
- `db` — PostgreSQL 15
- `redis` — Redis 7
