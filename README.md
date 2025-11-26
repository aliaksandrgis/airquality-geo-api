# AirQuality Geo API

FastAPI service serving air quality measurements from Supabase Postgres/PostGIS.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill Supabase settings
uvicorn app.main:app --reload --port 8000
```

## Environment (.env)
- `SUPABASE_URL` — Supabase PostgREST or direct Postgres URL.
- `SUPABASE_SERVICE_KEY` — service key for server-side access.
- `API_PORT` — default 8000.
- Optional: CORS allowed origins.

## Docker
```bash
docker build -t airquality-geo-api:dev .
docker run --env-file .env -p 8000:8000 airquality-geo-api:dev
```

## CI (template)
- Lint with `ruff`, run `pytest`, build container.

## Notes
- Keep read-only credentials for API; writes happen via Spark/ingest jobs.
- Add migrations (e.g., Alembic) and include in this repo.
