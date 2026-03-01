.PHONY: dev api-test web-build

dev:
	docker compose up --build

api-test:
	docker compose run --rm api pytest -q

web-build:
	docker compose run --rm web npm run build
