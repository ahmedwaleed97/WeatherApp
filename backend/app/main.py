from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers.weather import router as weather_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on first start; no-op if they already exist
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Weather API",
    description=(
        "Store, retrieve, update, and export weather data for any location and date range. "
        "Powered by Open-Meteo (no API key required)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(weather_router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
