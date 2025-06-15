.PHONY: dev lint format test docker-build

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	pre-commit run --all-files

format:
	ruff format .
	black .

test:
	pytest

docker-build:
	docker build -t backend .
