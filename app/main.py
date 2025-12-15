from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings


class Measurement(BaseModel):
    station_id: str
    pollutant: str
    value: float | None
    unit: str | None
    city: str | None
    location_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    country: str | None
    timestamp: datetime
    source: str | None


class TimePoint(BaseModel):
    station_id: str
    pollutant: str
    value: float | None
    unit: str | None
    country: str | None
    city: str | None
    location_name: str | None = None
    timestamp: datetime
    source: str | None


app = FastAPI(
    title="Air Quality GeoAPI",
    description="GeoAPI backed by Postgres measurements table.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_conn():
    return psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/measurements", response_model=List[Measurement])
def list_measurements(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    station_id: Optional[str] = None,
    country: Optional[str] = None,
    pollutant: Optional[str] = None,
    latest_per_station: bool = Query(
        False,
        description="If true, return only the latest record per station/pollutant",
    ),
) -> List[Measurement]:
    filters = []
    params = {}
    if station_id:
        filters.append("station_id = %(station_id)s")
        params["station_id"] = station_id
    if country:
        filters.append("country = %(country)s")
        params["country"] = country
    if pollutant:
        filters.append("pollutant = %(pollutant)s")
        params["pollutant"] = pollutant

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    if latest_per_station:
        sql = f"""
            WITH filtered AS (
                SELECT station_id, pollutant, value, unit, city, location_name, lat, lon, country, ts, source
                FROM measurements
                {where_clause}
            )
            SELECT DISTINCT ON (station_id, pollutant)
                station_id, pollutant, value, unit, city, location_name, lat, lon, country, ts, source
            FROM filtered
            ORDER BY station_id, pollutant, ts DESC
            LIMIT %(limit)s OFFSET %(offset)s;
        """
    else:
        sql = f"""
            SELECT station_id, pollutant, value, unit, city, location_name, lat, lon, country, ts, source
            FROM measurements
            {where_clause}
            ORDER BY ts DESC
            LIMIT %(limit)s OFFSET %(offset)s;
        """
    sql = f"""
        SELECT station_id, pollutant, value, unit, city, location_name, lat, lon, country, ts, source
        FROM measurements
        {where_clause}
        ORDER BY ts DESC
        LIMIT %(limit)s OFFSET %(offset)s;
    """
    params.update({"limit": limit, "offset": offset})

    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    measurements = [
        Measurement(
            station_id=row[0],
            pollutant=row[1],
            value=row[2],
            unit=row[3],
            city=row[4],
            location_name=row[5],
            lat=row[6],
            lon=row[7],
            country=row[8],
            timestamp=row[9],
            source=row[10],
        )
        for row in rows
    ]
    return measurements


@app.get("/measurements/timeseries", response_model=List[TimePoint])
def measurements_timeseries(
    station_id: str = Query(..., description="Station identifier (e.g., NL01491)"),
    pollutant: str = Query(..., description="Pollutant code (e.g., pm25, no2, o3)"),
    hours: int = Query(
        24,
        ge=1,
        le=168,
        description="How many hours back from now to include",
    ),
) -> List[TimePoint]:
    """
    Return time series for a given station/pollutant for the last N hours.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    params: dict[str, object] = {
        "station_id": station_id,
        "pollutant": pollutant,
        "since": since,
    }
    sql = """
        SELECT station_id,
               pollutant,
               value,
               unit,
               country,
               city,
               location_name,
               ts,
               source
        FROM measurements
        WHERE station_id = %(station_id)s
          AND pollutant = %(pollutant)s
          AND ts >= %(since)s
        ORDER BY ts;
    """
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    if not rows:
        # return 404 so the client can distinguish empty data from network errors
        raise HTTPException(status_code=404, detail="No measurements for given station/pollutant")

    return [
        TimePoint(
            station_id=row[0],
            pollutant=row[1],
            value=row[2],
            unit=row[3],
            country=row[4],
            city=row[5],
            location_name=row[6],
            timestamp=row[7],
            source=row[8],
        )
        for row in rows
    ]


@app.get("/stations")
def list_stations(
    country: Optional[str] = None, pollutant: Optional[str] = None
) -> dict:
    params = {}
    meas_filters = []
    if pollutant:
        meas_filters.append("m.pollutant = %(pollutant)s")
        params["pollutant"] = pollutant
    meas_where = f"WHERE {' AND '.join(meas_filters)}" if meas_filters else ""

    station_filters = ["s.lat IS NOT NULL", "s.lon IS NOT NULL"]
    if country:
        station_filters.append("s.country = %(country)s")
        params["country"] = country
    station_where = f"WHERE {' AND '.join(station_filters)}" if station_filters else ""

    sql = f"""
        WITH latest_meas AS (
            SELECT DISTINCT ON (station_id)
                station_id, source, pollutant, value, unit, ts
            FROM measurements m
            {meas_where}
            ORDER BY station_id, ts DESC
        )
        SELECT
            s.station_id,
            s.source,
            s.country,
            s.city,
            s.location_name,
            s.lat,
            s.lon,
            lm.pollutant,
            lm.value,
            lm.unit,
            lm.ts
        FROM stations s
        JOIN latest_meas lm ON lm.station_id = s.station_id
        {station_where};
    """
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    features = []
    for row in rows:
        lon = row[6]
        lat = row[5]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "station_id": row[0],
                    "source": row[1],
                    "country": row[2],
                    "city": row[3],
                    "location_name": row[4],
                    "pollutant": row[7],
                    "value": row[8],
                    "unit": row[9],
                    "timestamp": row[10].isoformat() if isinstance(row[10], datetime) else row[10],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


@app.get("/stations_wkt")
def list_stations_wkt(
    country: Optional[str] = None, pollutant: Optional[str] = None
) -> List[dict]:
    """
    Return stations as WKT with latest measurements per pollutant.
    If pollutant is provided, only measurements of that pollutant are included.
    """
    params = {}
    meas_filters = []
    if pollutant:
        meas_filters.append("m.pollutant = %(pollutant)s")
        params["pollutant"] = pollutant
    meas_where = f"WHERE {' AND '.join(meas_filters)}" if meas_filters else ""

    station_filters = ["s.lat IS NOT NULL", "s.lon IS NOT NULL"]
    if country:
        station_filters.append("s.country = %(country)s")
        params["country"] = country
    station_where = f"WHERE {' AND '.join(station_filters)}" if station_filters else ""

    sql = f"""
        WITH latest_meas AS (
            SELECT DISTINCT ON (station_id, pollutant)
                station_id, source, pollutant, value, unit, ts, country, city, location_name, lat, lon
            FROM measurements m
            {meas_where}
            ORDER BY station_id, pollutant, ts DESC
        )
        SELECT
            s.station_id,
            s.source,
            s.country,
            s.city,
            s.location_name,
            s.lat,
            s.lon,
            JSON_AGG(
                JSON_BUILD_OBJECT(
                    'pollutant', lm.pollutant,
                    'value', lm.value,
                    'unit', lm.unit,
                    'timestamp', lm.ts
                )
            ) AS measurements
        FROM stations s
        JOIN latest_meas lm ON lm.station_id = s.station_id
        {station_where}
        GROUP BY s.station_id, s.source, s.country, s.city, s.location_name, s.lat, s.lon;
    """
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    result = []
    for row in rows:
        lon = row[6]
        lat = row[5]
        if lon is None or lat is None:
            continue
        measurements_raw = row[7] or []
        measurements = []
        for m in measurements_raw:
            ts = m.get("timestamp")
            if isinstance(ts, datetime):
                ts = ts.isoformat()
            measurements.append(
                {
                    "pollutant": m.get("pollutant"),
                    "value": m.get("value"),
                    "unit": m.get("unit"),
                    "timestamp": ts,
                }
            )
        result.append(
            {
                "wkt": f"POINT({lon} {lat})",
                "station_id": row[0],
                "source": row[1],
                "country": row[2],
                "city": row[3],
                "location_name": row[4],
                "measurements": measurements,
            }
        )
    return result
