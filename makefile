# Запуск контейнеров в режиме разработки 
run_dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Запуск миграции для alembic
run_alembic:
	alembic revision --autogenerate -m "create users table"
	alembic upgrade head