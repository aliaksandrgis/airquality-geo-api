# AirQuality Geo API

FastAPI service that exposes measurements and stations stored in Supabase/Postgres.

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}
```

## Endpoints
- GET /health
- GET /measurements
- GET /measurements/timeseries
- GET /stations
- GET /stations_wkt

## Docker
```bash
docker build -t airquality-geo-api .
docker run --env-file .env -p 8000:8000 airquality-geo-api
```
