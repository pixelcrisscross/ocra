import requests

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

MARINE_VARS = [
    "wave_height", "wave_direction", "wave_period",
    "wind_wave_height", "wind_wave_direction", "wind_wave_period",
    "swell_wave_height", "swell_wave_direction", "swell_wave_period",
    "sea_surface_temperature", "ocean_current_velocity",
    "ocean_current_direction", "sea_level_height_msl",
]

WEATHER_VARS = [
    "temperature_2m", "wind_speed_10m", "wind_direction_10m",
    "pressure_msl", "precipitation", "weather_code",
]


def fetch_marine(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(MARINE_VARS),
        "hourly": ",".join(MARINE_VARS),
        "forecast_hours": 24,
        "timezone": "UTC",
    }
    r = requests.get(MARINE_URL, params=params, timeout=25)
    r.raise_for_status()
    return {"data": r.json(), "url": r.url}


def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(WEATHER_VARS),
        "timezone": "UTC",
    }
    r = requests.get(WEATHER_URL, params=params, timeout=25)
    r.raise_for_status()
    return {"data": r.json(), "url": r.url}
