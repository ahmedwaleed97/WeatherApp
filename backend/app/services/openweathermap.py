"""
OpenWeatherMap integration.

Used for:
  - Geocoding / location validation  (Geo API)
  - Current weather conditions        (Current Weather API)
  - 5-day / 3-hour forecast           (Forecast API)
  - Air quality index                 (Air Pollution API)
"""

import httpx

from app.config import settings

_BASE = "https://api.openweathermap.org"
_KEY = settings.openweathermap_api_key

AQI_LABELS = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}


# ─── Geocoding ───────────────────────────────────────────────────────────────

async def geocode(query: str, limit: int = 5) -> list[dict]:
    """
    Forward-geocode a place name or ZIP code.
    Returns a list of candidate dicts with lat, lon, name, country, state.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_BASE}/geo/1.0/direct",
            params={"q": query, "limit": limit, "appid": _KEY},
        )
        resp.raise_for_status()
    return resp.json()


async def geocode_zip(zip_code: str, country_code: str = "US") -> dict | None:
    """Geocode a ZIP / postal code directly."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_BASE}/geo/1.0/zip",
            params={"zip": f"{zip_code},{country_code}", "appid": _KEY},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    return resp.json()


async def reverse_geocode(lat: float, lon: float) -> dict | None:
    """Reverse-geocode coordinates to a place name."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_BASE}/geo/1.0/reverse",
            params={"lat": lat, "lon": lon, "limit": 1, "appid": _KEY},
        )
        resp.raise_for_status()
    results = resp.json()
    return results[0] if results else None


# ─── Current weather ─────────────────────────────────────────────────────────

async def get_current_weather(lat: float, lon: float) -> dict:
    """
    Fetch live current conditions for a coordinate pair.
    Returns a structured dict ready to merge into weather_data.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_BASE}/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": _KEY, "units": "metric"},
        )
        resp.raise_for_status()
    raw = resp.json()

    return {
        "source": "OpenWeatherMap (live)",
        "temperature_c": raw["main"]["temp"],
        "feels_like_c": raw["main"]["feels_like"],
        "temp_min_c": raw["main"]["temp_min"],
        "temp_max_c": raw["main"]["temp_max"],
        "humidity_pct": raw["main"]["humidity"],
        "pressure_hpa": raw["main"]["pressure"],
        "visibility_m": raw.get("visibility"),
        "wind_speed_ms": raw["wind"]["speed"],
        "wind_direction_deg": raw["wind"].get("deg"),
        "cloud_cover_pct": raw["clouds"]["all"],
        "weather_description": raw["weather"][0]["description"].title(),
        "weather_icon": raw["weather"][0]["icon"],
        "sunrise_utc": raw["sys"]["sunrise"],
        "sunset_utc": raw["sys"]["sunset"],
    }


# ─── 5-day forecast ──────────────────────────────────────────────────────────

async def get_forecast(lat: float, lon: float) -> list[dict]:
    """
    Fetch the 5-day / 3-hour forecast and collapse it to daily summaries.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_BASE}/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": _KEY, "units": "metric"},
        )
        resp.raise_for_status()
    items = resp.json().get("list", [])

    # Collapse 3-hour slots into daily buckets
    by_day: dict[str, list[dict]] = {}
    for item in items:
        day = item["dt_txt"][:10]  # "YYYY-MM-DD"
        by_day.setdefault(day, []).append(item)

    daily = []
    for day, slots in sorted(by_day.items()):
        temps = [s["main"]["temp"] for s in slots]
        precip = sum(s.get("rain", {}).get("3h", 0) + s.get("snow", {}).get("3h", 0) for s in slots)
        wind = max(s["wind"]["speed"] for s in slots)
        pop = max(s.get("pop", 0) for s in slots)
        desc = slots[len(slots) // 2]["weather"][0]["description"].title()

        daily.append({
            "date": day,
            "source": "OpenWeatherMap (forecast)",
            "temp_max": round(max(temps), 1),
            "temp_min": round(min(temps), 1),
            "temp_mean": round(sum(temps) / len(temps), 1),
            "precipitation_mm": round(precip, 1),
            "windspeed_max_kmh": round(wind * 3.6, 1),
            "precipitation_probability_pct": round(pop * 100),
            "weather_description": desc,
            "weather_code": None,
        })
    return daily


# ─── Air quality ─────────────────────────────────────────────────────────────

async def get_air_quality(lat: float, lon: float) -> dict:
    """
    Fetch current air quality index and pollutant concentrations.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{_BASE}/data/2.5/air_pollution",
            params={"lat": lat, "lon": lon, "appid": _KEY},
        )
        resp.raise_for_status()
    data = resp.json()["list"][0]
    aqi = data["main"]["aqi"]
    components = data["components"]

    return {
        "aqi": aqi,
        "aqi_label": AQI_LABELS.get(aqi, "Unknown"),
        "co_ugm3": components.get("co"),
        "no2_ugm3": components.get("no2"),
        "o3_ugm3": components.get("o3"),
        "pm2_5_ugm3": components.get("pm2_5"),
        "pm10_ugm3": components.get("pm10"),
    }
