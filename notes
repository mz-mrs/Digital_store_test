настройки в докер композе для енв по умолчанию

Но есть ещё один важный момент: если приложение тоже будет запускаться в Docker, POSTGRES_HOST для него должен быть postgres, а не localhost. Для твоего текущего этапа, где FastAPI запускаешь из .venv на Windows, localhost правильный.


Я бы сделала так
services:
  postgres:
    image: postgres:17
    container_name: digital_store_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  migrations:
    build: .
    command: poetry run alembic upgrade head
    depends_on:
      postgres:
        condition: service_healthy

  seed:
    build: .
    command: poetry run python -m app.scripts.products_to_db
    depends_on:
      migrations:
        condition: service_completed_successfully

volumes:
  postgres_data:

Но есть один момент: это предполагает, что твой Dockerfile уже устанавливает Poetry и зависимости проекта.

И ещё: если ты сейчас запускаешь приложение локально через .venv, а Dockerfile у тебя пока не готов, не надо пока вставлять этот Compose вслепую.

Покажи мне текущий Dockerfile (если он уже есть). Тогда я подгоню Compose под него, и сделаем нормальный запуск:

docker compose up

который будет автоматически:

PostgreSQL
   ↓
Alembic
   ↓
products.json → products

Причём твой уже существующий volume postgres_data сохранится, поэтому повторный запуск не сотрёт базу.