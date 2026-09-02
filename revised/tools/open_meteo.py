import requests

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_marine(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "wave_height",
            "wave_direction",
            "wave_period",
            "wind_wave_height",
            "wind_wave_direction",
            "wind_wave_period",
            "swell_wave_height",
            "swell_wave_direction",
            "swell_wave_period",
            "sea_surface_temperature",
            "ocean_current_velocity",
            "ocean_current_direction",
            "sea_level_height_msl",
        ]),
        "hourly": ",".join([
            "wave_height",
            "wave_direction",
            "wave_period",
            "sea_surface_temperature",
            "ocean_current_velocity",
            "ocean_current_direction",
            "sea_level_height_msl",
        ]),
        "forecast_hours": 24,
        "timezone": "UTC",
    }
    r = requests.get(MARINE_URL, params=params, timeout=25)
    r.raise_for_status()
    return {"data": r.json(), "url": r.url}


def fetch_weather(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "pressure_msl",
            "precipitation",
            "weather_code",
        ]),
        "timezone": "UTC",
    }
    r = requests.get(WEATHER_URL, params=params, timeout=25)
    r.raise_for_status()
    return {"data": r.json(), "url": r.url}
