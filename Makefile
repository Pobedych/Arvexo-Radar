.PHONY: up down logs api-shell migrate seed test lint

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

seed:
	docker compose exec api python -m app.seed_demo

test:
	cd backend && python -m pytest

lint:
	cd backend && ruff check .
