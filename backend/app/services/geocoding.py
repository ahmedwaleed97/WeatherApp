"""
Location resolution using OpenWeatherMap (primary) with Open-Meteo as fallback.
Handles city names, landmarks, ZIP / postal codes, and raw GPS coordinates.
"""

import re
import httpx

from app.schemas.weather import LocationSearchResult

OPEN_METEO_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

_COORDINATE_RE = re.compile(
    r"^(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)$"
)
_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


def _parse_coordinates(query: str) -> tuple[float, float] | None:
    match = _COORDINATE_RE.match(query.strip())
    if not match:
        return None
    lat, lng = float(match.group(1)), float(match.group(2))
    if -90 <= lat <= 90 and -180 <= lng <= 180:
        return lat, lng
    return None


async def _owm_geocode(query: str, limit: int = 5) -> list[LocationSearchResult]:
    from app.services.openweathermap import geocode, geocode_zip

    results = []

    # Try ZIP code path first when the input looks like one
    if _ZIP_RE.match(query.strip()):
        try:
            data = await geocode_zip(query.strip())
            if data:
                results.append(
                    LocationSearchResult(
                        name=data.get("name", query),
                        latitude=data["lat"],
                        longitude=data["lon"],
                        country=data.get("country"),
                        country_code=data.get("country"),
                        admin1=None,
                    )
                )
                return results
        except Exception:
            pass  # Fall through to forward geocode

    try:
        raw = await geocode(query, limit=limit)
        for r in raw:
            results.append(
                LocationSearchResult(
                    name=r.get("name", query),
                    latitude=r["lat"],
                    longitude=r["lon"],
                    country=r.get("country"),
                    country_code=r.get("country"),
                    admin1=r.get("state"),
                )
            )
    except Exception:
        pass

    return results


async def _open_meteo_geocode(query: str, count: int = 5) -> list[LocationSearchResult]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            OPEN_METEO_GEO_URL,
            params={"name": query, "count": count, "language": "en"},
        )
        resp.raise_for_status()

    results = []
    for r in resp.json().get("results") or []:
        results.append(
            LocationSearchResult(
                name=r["name"],
                latitude=r["latitude"],
                longitude=r["longitude"],
                country=r.get("country"),
                country_code=r.get("country_code"),
                admin1=r.get("admin1"),
            )
        )
    return results


async def search_locations(query: str, count: int = 5) -> list[LocationSearchResult]:
    """
    Return candidate locations for a query string.
    OWM is tried first; Open-Meteo is the fallback.
    """
    coords = _parse_coordinates(query)
    if coords:
        lat, lng = coords
        return [
            LocationSearchResult(
                name=f"{lat}, {lng}",
                latitude=lat,
                longitude=lng,
                country=None,
                country_code=None,
                admin1=None,
            )
        ]

    results = await _owm_geocode(query, limit=count)
    if not results:
        results = await _open_meteo_geocode(query, count=count)
    return results


async def resolve_location(query: str) -> dict:
    """
    Resolve a location string to a single best match.
    Returns dict with: latitude, longitude, name, country_code.
    Raises ValueError if nothing matches.
    """
    coords = _parse_coordinates(query)
    if coords:
        lat, lng = coords
        # Try to get a human name for the coordinates via OWM reverse geocoding
        try:
            from app.services.openweathermap import reverse_geocode
            place = await reverse_geocode(lat, lng)
            if place:
                name_parts = [place.get("name", "")]
                if place.get("state"):
                    name_parts.append(place["state"])
                if place.get("country"):
                    name_parts.append(place["country"])
                return {
                    "latitude": lat,
                    "longitude": lng,
                    "name": ", ".join(p for p in name_parts if p),
                    "country_code": place.get("country"),
                }
        except Exception:
            pass
        return {
            "latitude": lat,
            "longitude": lng,
            "name": f"{lat:.4f}, {lng:.4f}",
            "country_code": None,
        }

    # Build a list of progressively simpler queries to try.
    # e.g. "Zawra District, Baghdad Governorate, IQ"
    #   → try full string, then "Zawra District", then "Baghdad Governorate"
    #   (skip bare country codes like "IQ" — too short to be reliable)
    parts = [p.strip() for p in query.split(",") if len(p.strip()) > 3]
    queries_to_try = list(dict.fromkeys([query] + parts))  # unique, order preserved

    candidates = []
    for attempt in queries_to_try:
        candidates = await search_locations(attempt, count=1)
        if candidates:
            break

    if not candidates:
        raise ValueError(
            f"Location '{query}' could not be found. "
            "Try a city name, postal code, or GPS coordinates (lat, lng)."
        )

    best = candidates[0]
    name_parts = [best.name]
    if best.admin1:
        name_parts.append(best.admin1)
    if best.country:
        name_parts.append(best.country)

    return {
        "latitude": best.latitude,
        "longitude": best.longitude,
        "name": ", ".join(name_parts),
        "country_code": best.country_code,
    }
