# AirQuality Geo API

FastAPI‑сервис, который читает измерения и станции из PostgreSQL/Supabase и отдаёт их в формате REST для веб‑клиента и любых других интеграций.

## Быстрый старт (локально)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # заполните POSTGRES_* и CORS
uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}
```

Доступные эндпоинты:
- `GET /health` — статус API;
- `GET /measurements` и `/measurements/timeseries` — таблица измерений;
- `GET /stations` и `/stations_wkt` — станции с последними значениями (GeoJSON/WKT).

## Переменные окружения

| Переменная          | Описание                                   |
|---------------------|--------------------------------------------|
| `POSTGRES_HOST`     | Хост базы (Supabase/локальный Postgres)    |
| `POSTGRES_PORT`     | Порт, по умолчанию `5432`                  |
| `POSTGRES_DB`       | Имя базы данных                            |
| `POSTGRES_USER`     | Read-only пользователь                     |
| `POSTGRES_PASSWORD` | Пароль                                     |
| `API_PORT`          | Порт uvicorn                               |
| `ALLOWED_ORIGINS`   | Список доменов для CORS (через запятую)    |

## Docker

```bash
docker build -t airquality-geo-api .
docker run --env-file .env -p 8000:8000 airquality-geo-api
```

## Развёртывание на Raspberry Pi

1. Скопируйте репозиторий в `/home/pc/airquality-geo-api`.
2. Создайте `python -m venv .venv`, установите зависимости.
3. Заполните `.env` (см. пример) и запустите `uvicorn` либо оформите unit:
   ```ini
   [Service]
   WorkingDirectory=/home/pc/airquality-geo-api
   EnvironmentFile=/home/pc/airquality-geo-api/.env
   ExecStart=/home/pc/airquality-geo-api/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}
   Restart=on-failure
   ```
4. Прокиньте внешний домен (например, `api.naviodev.com`) через Cloudflare Tunnel или nginx с TLS.

## CI / публикация

- линтеры/тесты (`ruff`, `pytest`);
- сборка контейнера и публикация образа;
- деплой на Pi выполняется через `git pull` + `systemctl restart airquality-geo-api`.
