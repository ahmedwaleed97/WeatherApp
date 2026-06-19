from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, Text
from sqlalchemy.sql import func

from app.database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)

    # What the user typed in
    location_query = Column(String(255), nullable=False)

    # Resolved location details
    location_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country_code = Column(String(10), nullable=True)

    # The date range requested
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)

    # Full daily weather data stored as JSON
    weather_data = Column(JSON, nullable=False)

    # Optional label the user can set
    label = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
