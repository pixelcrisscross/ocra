from schemas import Intent, OceanAPIData, OceanVariable, Location

from tools.open_meteo import fetch_marine_data


def get_api_data(intent: Intent):

    lat = intent.location.latitude
    lon = intent.location.longitude

    raw = fetch_marine_data(lat, lon)

    current = raw.get("current", {})

    def variable(name, unit):
        value = current.get(name)

        if value is None:
            return None

        return OceanVariable(
            value=value,
            unit=unit,
            source="Open-Meteo Marine",
            timestamp=current.get("time")
        )

    result = OceanAPIData(

        location=Location(
            latitude=lat,
            longitude=lon,
            name=intent.location.name
        ),

        source="Open-Meteo Marine",

        timestamp=current.get("time"),

        sea_surface_temperature=variable(
            "sea_surface_temperature",
            "°C"
        ),

        wave_height=variable(
            "wave_height",
            "m"
        ),

        wave_period=variable(
            "wave_period",
            "s"
        ),

        wave_direction=variable(
            "wave_direction",
            "°"
        ),

        ocean_current_speed=variable(
            "ocean_current_velocity",
            "km/h"
        ),

        ocean_current_direction=variable(
            "ocean_current_direction",
            "°"
        ),

        sea_level=variable(
            "sea_level_height_msl",
            "m"
        )
    )

    return result