.PHONY: dev prod api-test web-build web-lint web-format api-lint api-format

dev:
	docker compose up --build

prod:
	docker compose -f docker-compose.prod.yml up --build -d

api-test:
	docker compose run --rm api bash -lc "PYTHONPATH=. pytest -q"

api-lint:
	docker compose run --rm api ruff check apps/api

api-format:
	docker compose run --rm api black apps/api

web-build:
	docker compose run --rm web npm run build

web-lint:
	docker compose run --rm web npm run lint

web-format:
	docker compose run --rm web npm run format
