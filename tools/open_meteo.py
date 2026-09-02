import requests


OPEN_METEO_URL = "https://marine-api.open-meteo.com/v1/marine"


def fetch_marine_data(
    latitude: float,
    longitude: float,
    forecast_days: int = 2
):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "wave_height",
            "wave_direction",
            "wave_period",
            "sea_surface_temperature",
            "ocean_current_velocity",
            "ocean_current_direction",
            "sea_level_height_msl"
        ]),

        "hourly": ",".join([
            "wave_height",
            "wave_direction",
            "wave_period",
            "sea_surface_temperature",
            "ocean_current_velocity",
            "ocean_current_direction",
            "sea_level_height_msl"
        ]),

        "forecast_days": forecast_days,

        "timezone": "UTC"
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()