"""
Weather CRUD router.

Endpoints
---------
POST   /weather/              Create a new weather record
GET    /weather/              List all records (with optional filters)
GET    /weather/locations     Search for candidate locations (autocomplete)
GET    /weather/{id}          Get a single record
PUT    /weather/{id}          Update a record
DELETE /weather/{id}          Delete a record
GET    /weather/{id}/export   Export one record (csv | excel | json)
GET    /weather/export/all    Export all records (csv | excel | json)
"""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.weather import WeatherRecord
from app.schemas.weather import (
    LocationSearchResult,
    WeatherQueryCreate,
    WeatherRecordOut,
    WeatherRecordUpdate,
)
from app.services.geocoding import resolve_location, search_locations
from app.services.weather_api import fetch_weather
from app.utils.export import export_records

router = APIRouter(prefix="/weather", tags=["weather"])


# ─── helpers ────────────────────────────────────────────────────────────────

def _get_or_404(record_id: int, db: Session) -> WeatherRecord:
    record = db.get(WeatherRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found.")
    return record


# ─── CREATE ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=WeatherRecordOut, status_code=201)
async def create_weather_record(payload: WeatherQueryCreate, db: Session = Depends(get_db)):
    """
    Resolve the location, fetch weather for the date range, and persist the result.
    """
    try:
        geo = await resolve_location(payload.location)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        weather = await fetch_weather(
            geo["latitude"], geo["longitude"], payload.date_from, payload.date_to
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch weather data: {exc}",
        )

    record = WeatherRecord(
        location_query=payload.location,
        location_name=geo["name"],
        latitude=geo["latitude"],
        longitude=geo["longitude"],
        country_code=geo["country_code"],
        date_from=payload.date_from,
        date_to=payload.date_to,
        weather_data=weather,
        label=payload.label,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ─── READ (list) ─────────────────────────────────────────────────────────────

@router.get("/", response_model=list[WeatherRecordOut])
def list_weather_records(
    location: str | None = Query(None, description="Filter by location name (partial match)"),
    from_date: date | None = Query(None, description="Records whose date_from >= this date"),
    to_date: date | None = Query(None, description="Records whose date_to <= this date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all stored weather records with optional filtering and pagination."""
    query = db.query(WeatherRecord)

    if location:
        query = query.filter(
            WeatherRecord.location_name.ilike(f"%{location}%")
        )
    if from_date:
        query = query.filter(WeatherRecord.date_from >= from_date)
    if to_date:
        query = query.filter(WeatherRecord.date_to <= to_date)

    return query.order_by(WeatherRecord.created_at.desc()).offset(skip).limit(limit).all()


# ─── Location autocomplete ────────────────────────────────────────────────────

@router.get("/locations", response_model=list[LocationSearchResult])
async def search_location_candidates(
    q: str = Query(..., min_length=2, description="Location search query"),
    count: int = Query(5, ge=1, le=10),
):
    """Search for matching locations without creating a record."""
    return await search_locations(q, count=count)


# ─── READ (single) ───────────────────────────────────────────────────────────

@router.get("/{record_id}", response_model=WeatherRecordOut)
def get_weather_record(record_id: int, db: Session = Depends(get_db)):
    """Retrieve a single stored weather record by ID."""
    return _get_or_404(record_id, db)


# ─── UPDATE ──────────────────────────────────────────────────────────────────

@router.put("/{record_id}", response_model=WeatherRecordOut)
async def update_weather_record(
    record_id: int,
    payload: WeatherRecordUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a weather record.

    - Changing `label` or `notes` is a metadata-only update.
    - Changing `location`, `date_from`, or `date_to` re-fetches weather data.
    """
    record = _get_or_404(record_id, db)

    new_location = payload.location or record.location_query
    new_from = payload.date_from or record.date_from
    new_to = payload.date_to or record.date_to

    # Validate the final date range regardless of what changed
    if new_from > new_to:
        raise HTTPException(status_code=422, detail="date_from must be on or before date_to.")

    needs_refetch = (
        payload.location is not None
        or payload.date_from is not None
        or payload.date_to is not None
    )

    if needs_refetch:
        try:
            geo = await resolve_location(new_location)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        try:
            weather = await fetch_weather(geo["latitude"], geo["longitude"], new_from, new_to)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Could not fetch weather data: {exc}")

        record.location_query = new_location
        record.location_name = geo["name"]
        record.latitude = geo["latitude"]
        record.longitude = geo["longitude"]
        record.country_code = geo["country_code"]
        record.date_from = new_from
        record.date_to = new_to
        record.weather_data = weather

    if payload.label is not None:
        record.label = payload.label
    if payload.notes is not None:
        record.notes = payload.notes

    db.commit()
    db.refresh(record)
    return record


# ─── DELETE ──────────────────────────────────────────────────────────────────

@router.delete("/{record_id}", status_code=204)
def delete_weather_record(record_id: int, db: Session = Depends(get_db)):
    """Permanently remove a stored weather record."""
    record = _get_or_404(record_id, db)
    db.delete(record)
    db.commit()


# ─── EXPORT (single record) ──────────────────────────────────────────────────

@router.get("/{record_id}/export")
def export_single_record(
    record_id: int,
    format: Literal["csv", "excel", "json"] = Query("csv"),
    db: Session = Depends(get_db),
):
    """Export one record to CSV, Excel, or JSON."""
    record = _get_or_404(record_id, db)
    content, media_type, filename = export_records([record], format)
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── EXPORT (all records) ────────────────────────────────────────────────────

@router.get("/export/all")
def export_all_records(
    format: Literal["csv", "excel", "json"] = Query("csv"),
    location: str | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """Export all (optionally filtered) records to CSV, Excel, or JSON."""
    query = db.query(WeatherRecord)
    if location:
        query = query.filter(WeatherRecord.location_name.ilike(f"%{location}%"))
    if from_date:
        query = query.filter(WeatherRecord.date_from >= from_date)
    if to_date:
        query = query.filter(WeatherRecord.date_to <= to_date)

    records = query.order_by(WeatherRecord.created_at.desc()).all()
    content, media_type, filename = export_records(records, format)
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
