# Backend Service

This is the backend service for the project.

## Quick start (uv)

This project uses `uv` for package management.

1.  **Install `uv`**:
    Follow the instructions on the [official `uv` website](https://github.com/astral-sh/uv).

2.  **Create a virtual environment**:
    ```bash
    uv venv
    ```

3.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

4.  **Install dependencies**:
    ```bash
    uv pip install -r requirements.txt -r requirements-dev.txt
    ```

5.  **Set up environment variables**:
    Copy the example environment file and fill in your details if needed.
    ```bash
    cp .env.example .env
    ```

6.  **Run the application**:
    ```bash
    make dev
    ```
    The application will be available at `http://localhost:8000`.

## Docker workflow

1.  **Run the entire stack with Docker Compose**:
    Make sure you are in the project root directory (where `docker-compose.yml` is located).
    ```bash
    cp backend/.env.example backend/.env
    docker compose up --build
    ```
    The backend will be available at `http://localhost:8000`.

## Make targets

- `make dev`: Starts the development server with auto-reload.
- `make lint`: Runs linters (`ruff`, `mypy`) via pre-commit.
- `make format`: Formats the code using `ruff` and `black`.
- `make test`: Runs tests with `pytest`.
- `make docker-build`: Builds the Docker image for the backend service.

## Compose services

The `docker-compose.yml` file at the project root defines the following services:

- `backend`: The Python FastAPI application.
- `db`: A PostgreSQL 15 database.
- `redis`: A Redis 7 cache.
