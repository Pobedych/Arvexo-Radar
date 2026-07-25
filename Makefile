.PHONY: up down logs api-shell migrate test lint

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

api-shell:
	docker compose exec api sh

migrate:
	docker compose exec api alembic upgrade head

test:
	cd backend && python -m pytest

lint:
	cd backend && ruff check .
