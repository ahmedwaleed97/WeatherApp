"""
Weather data fetching strategy:

  Past dates      → Open-Meteo historical archive  (free, unlimited history)
  Today (live)    → OpenWeatherMap current weather  (rich live conditions)
  Future dates    → OpenWeatherMap 5-day forecast   (up to 5 days out)
  Far future      → Open-Meteo forecast             (beyond OWM's 5-day window)

Air quality is always fetched from OpenWeatherMap and attached to the record.
"""

from datetime import date, timedelta

import httpx

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

ARCHIVE_LAG_DAYS = 5   # archive is available up to ~5 days before today
OWM_FORECAST_DAYS = 5  # OWM free forecast window

DAILY_ARCHIVE_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "windspeed_10m_max",
    "weathercode",
    "uv_index_max",
]

WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _wmo_label(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WMO_DESCRIPTIONS.get(int(code), f"Code {code}")


async def _fetch_open_meteo(url: str, lat: float, lng: float, start: date, end: date, extra_vars: list[str] | None = None) -> dict:
    vars_ = DAILY_ARCHIVE_VARS + (extra_vars or [])
    params = {
        "latitude": lat, "longitude": lng,
        "daily": ",".join(vars_),
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "timezone": "UTC", "temperature_unit": "celsius",
        "windspeed_unit": "kmh", "precipitation_unit": "mm",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
    return resp.json()


def _parse_open_meteo_daily(raw: dict, include_precip_prob: bool = False) -> list[dict]:
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    rows = []
    for i, d in enumerate(dates):
        code = (daily.get("weathercode") or [None] * (i + 1))[i]
        rows.append({
            "date": d,
            "source": "Open-Meteo (historical archive)",
            "temp_max": (daily.get("temperature_2m_max") or [None] * (i + 1))[i],
            "temp_min": (daily.get("temperature_2m_min") or [None] * (i + 1))[i],
            "temp_mean": (daily.get("temperature_2m_mean") or [None] * (i + 1))[i],
            "precipitation_mm": (daily.get("precipitation_sum") or [None] * (i + 1))[i],
            "windspeed_max_kmh": (daily.get("windspeed_10m_max") or [None] * (i + 1))[i],
            "weather_code": code,
            "weather_description": _wmo_label(code),
            "precipitation_probability_pct": (
                (daily.get("precipitation_probability_max") or [None] * (i + 1))[i]
                if include_precip_prob else None
            ),
            "uv_index_max": (daily.get("uv_index_max") or [None] * (i + 1))[i],
        })
    return rows


def _compute_summary(days: list[dict]) -> dict:
    temps = [d["temp_mean"] for d in days if d.get("temp_mean") is not None]
    precip = [d["precipitation_mm"] for d in days if d.get("precipitation_mm") is not None]
    wind = [d["windspeed_max_kmh"] for d in days if d.get("windspeed_max_kmh") is not None]
    return {
        "avg_temp_c": round(sum(temps) / len(temps), 1) if temps else None,
        "max_temp_c": max(temps) if temps else None,
        "min_temp_c": min(temps) if temps else None,
        "total_precipitation_mm": round(sum(precip), 1) if precip else None,
        "avg_windspeed_kmh": round(sum(wind) / len(wind), 1) if wind else None,
    }


async def fetch_weather(lat: float, lng: float, start: date, end: date) -> dict:
    """
    Fetch daily weather for the given coordinate and date range.

    Stitches together OpenWeatherMap (live + forecast) and Open-Meteo
    (historical archive) to cover any date range requested.
    """
    from app.services.openweathermap import get_current_weather, get_forecast, get_air_quality

    today = date.today()
    archive_cutoff = today - timedelta(days=ARCHIVE_LAG_DAYS)
    owm_forecast_end = today + timedelta(days=OWM_FORECAST_DAYS)

    days: list[dict] = []

    # 1. Historical: Open-Meteo archive
    if start <= archive_cutoff:
        hist_end = min(end, archive_cutoff)
        raw = await _fetch_open_meteo(OPEN_METEO_ARCHIVE_URL, lat, lng, start, hist_end)
        days.extend(_parse_open_meteo_daily(raw))

    # 2. Today: OWM live current conditions (single day, richest data)
    if start <= today <= end:
        try:
            current = await get_current_weather(lat, lng)
            # UV index not available from OWM current — grab from Open-Meteo forecast
            try:
                uv_raw = await _fetch_open_meteo(OPEN_METEO_FORECAST_URL, lat, lng, today, today)
                uv_val = (uv_raw.get("daily", {}).get("uv_index_max") or [None])[0]
            except Exception:
                uv_val = None
            days.append({
                "date": today.isoformat(),
                "source": "OpenWeatherMap (live)",
                "temp_max": current["temp_max_c"],
                "temp_min": current["temp_min_c"],
                "temp_mean": current["temperature_c"],
                "precipitation_mm": None,
                "windspeed_max_kmh": round(current["wind_speed_ms"] * 3.6, 1),
                "weather_code": None,
                "weather_description": current["weather_description"],
                "precipitation_probability_pct": None,
                "humidity_pct": current["humidity_pct"],
                "pressure_hpa": current["pressure_hpa"],
                "feels_like_c": current["feels_like_c"],
                "cloud_cover_pct": current["cloud_cover_pct"],
                "visibility_m": current.get("visibility_m"),
                "uv_index_max": uv_val,
            })
        except Exception:
            # Fallback: get from Open-Meteo forecast if OWM fails
            raw = await _fetch_open_meteo(
                OPEN_METEO_FORECAST_URL, lat, lng, today, today,
                extra_vars=["precipitation_probability_max"]
            )
            days.extend(_parse_open_meteo_daily(raw, include_precip_prob=True))

    # 3. Near future (within OWM's 5-day window): OWM forecast
    owm_fc_start = max(start, today + timedelta(days=1))
    owm_fc_end = min(end, owm_forecast_end)
    if owm_fc_start <= owm_fc_end:
        try:
            all_fc = await get_forecast(lat, lng)
            owm_dates = {d["date"] for d in days}
            for fc_day in all_fc:
                if owm_fc_start.isoformat() <= fc_day["date"] <= owm_fc_end.isoformat():
                    if fc_day["date"] not in owm_dates:
                        days.append(fc_day)
        except Exception:
            raw = await _fetch_open_meteo(
                OPEN_METEO_FORECAST_URL, lat, lng, owm_fc_start, owm_fc_end,
                extra_vars=["precipitation_probability_max"]
            )
            days.extend(_parse_open_meteo_daily(raw, include_precip_prob=True))

    # 4. Far future (beyond OWM window): Open-Meteo forecast
    far_future_start = max(start, owm_forecast_end + timedelta(days=1))
    if far_future_start <= end:
        raw = await _fetch_open_meteo(
            OPEN_METEO_FORECAST_URL, lat, lng, far_future_start, end,
            extra_vars=["precipitation_probability_max"]
        )
        new_days = _parse_open_meteo_daily(raw, include_precip_prob=True)
        for d in new_days:
            d["source"] = "Open-Meteo (forecast)"
        days.extend(new_days)

    # Deduplicate and sort
    seen: set[str] = set()
    unique: list[dict] = []
    for d in days:
        if d["date"] not in seen:
            seen.add(d["date"])
            unique.append(d)
    unique.sort(key=lambda d: d["date"])

    # 5. Air quality from OWM (current conditions, attached at record level)
    air_quality = None
    try:
        air_quality = await get_air_quality(lat, lng)
    except Exception:
        pass

    return {
        "units": {
            "temperature": "°C",
            "precipitation": "mm",
            "windspeed": "km/h",
        },
        "daily": unique,
        "summary": _compute_summary(unique),
        "air_quality": air_quality,
    }
