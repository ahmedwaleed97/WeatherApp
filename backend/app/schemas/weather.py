from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


MAX_DATE_RANGE_DAYS = 365


class WeatherQueryCreate(BaseModel):
    """Input for creating a new weather record."""
    location: str
    date_from: date
    date_to: date
    label: str | None = None
    notes: str | None = None

    @field_validator("location")
    @classmethod
    def location_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Location cannot be empty.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "WeatherQueryCreate":
        if self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to.")
        span = (self.date_to - self.date_from).days
        if span > MAX_DATE_RANGE_DAYS:
            raise ValueError(f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days.")
        return self


class WeatherRecordUpdate(BaseModel):
    """
    Fields the user may change on an existing record.
    Changing location or dates triggers a fresh weather fetch.
    """
    location: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    label: str | None = None
    notes: str | None = None

    @field_validator("location")
    @classmethod
    def location_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Location cannot be empty.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "WeatherRecordUpdate":
        if self.date_from is not None and self.date_to is not None:
            if self.date_from > self.date_to:
                raise ValueError("date_from must be on or before date_to.")
            span = (self.date_to - self.date_from).days
            if span > MAX_DATE_RANGE_DAYS:
                raise ValueError(f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days.")
        return self


class WeatherRecordOut(BaseModel):
    """Full record returned from the API."""
    id: int
    location_query: str
    location_name: str
    latitude: float
    longitude: float
    country_code: str | None
    date_from: date
    date_to: date
    weather_data: dict[str, Any]
    label: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LocationSearchResult(BaseModel):
    """A candidate location returned by the geocoding search."""
    name: str
    latitude: float
    longitude: float
    country: str | None
    country_code: str | None
    admin1: str | None  # state / province
