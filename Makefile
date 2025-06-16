.PHONY: dev lint format test docker-build

dev:
	docker compose up --build

lint:
	pre-commit run --all-files

format:
	ruff format .
	black .

test:
	pytest
