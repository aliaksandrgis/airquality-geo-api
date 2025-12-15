# AirQuality Geo API

FastAPI service that exposes measurements/stations stored in PostgreSQL (Supabase) via REST endpoints.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in POSTGRES_* variables and CORS list
uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}
```

Endpoints:

- `GET /health`
- `GET /measurements`, `GET /measurements/timeseries`
- `GET /stations`, `GET /stations_wkt`

## Environment (.env)

| Variable            | Description                                     |
|---------------------|-------------------------------------------------|
| `POSTGRES_HOST`     | Supabase/Postgres host                          |
| `POSTGRES_PORT`     | Port (default 5432)                             |
| `POSTGRES_DB`       | Database name                                   |
| `POSTGRES_USER`     | Read-only user                                  |
| `POSTGRES_PASSWORD` | Password                                        |
| `API_PORT`          | uvicorn port (default 8000)                     |
| `ALLOWED_ORIGINS`   | Comma-separated list for CORS                   |

## Docker

```bash
docker build -t airquality-geo-api .
docker run --env-file .env -p 8000:8000 airquality-geo-api
```

## CI / publishing

- run tests/lint (e.g., `ruff`, `pytest`);
- build and push Docker image;
- deploy to the Pi by `git pull && systemctl restart airquality-geo-api`.
