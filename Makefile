.PHONY: dev lint format test docker-build

dev:
	docker compose up --build

dev-restart:
	docker compose down -v
	docker compose up --build
	docker compose exec backend alembic upgrade head

lint:
	pre-commit run --all-files

format:
	ruff format .
	black .

test:
	pytest
