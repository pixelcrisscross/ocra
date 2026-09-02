from schemas import DataPoint, Conditions, Location
from tools.geocode import resolve_location
from tools.open_meteo import fetch_marine, fetch_weather
from tools.noaa_ndbc import fetch_nearest_observation


def dp(value, unit, source, source_url, source_type, timestamp, confidence, distance_km=None):
    if value is None:
        return DataPoint(status="unavailable")
    return DataPoint(
        value=float(value), unit=unit, source=source, source_url=source_url,
        source_type=source_type, timestamp=timestamp, confidence=confidence,
        distance_km=distance_km,
    )


def resolve_intent_location(intent):
    loc = intent.location
    if loc.latitude is not None and loc.longitude is not None:
        return Location(name=loc.name, latitude=loc.latitude, longitude=loc.longitude)
    if not loc.name:
        raise ValueError("Level 1 did not provide a usable location name")
    resolved = resolve_location(loc.name)
    return Location(
        name=resolved["name"],
        latitude=resolved["latitude"],
        longitude=resolved["longitude"],
    )


def fetch_live_conditions(intent):
    location = resolve_intent_location(intent)
    marine = fetch_marine(location.latitude, location.longitude)
    weather = fetch_weather(location.latitude, location.longitude)
    buoy = None
    try:
        buoy = fetch_nearest_observation(location.latitude, location.longitude)
    except Exception:
        buoy = None

    mc = marine["data"].get("current", {})
    wc = weather["data"].get("current", {})
    marine_time = mc.get("time")
    weather_time = wc.get("time")

    c = Conditions(
        sea_surface_temperature=dp(mc.get("sea_surface_temperature"), "°C", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.86),
        wave_height=dp(mc.get("wave_height"), "m", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.86),
        wave_period=dp(mc.get("wave_period"), "s", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.86),
        wave_direction=dp(mc.get("wave_direction"), "°", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.86),
        current_speed=dp(mc.get("ocean_current_velocity"), "km/h", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.80),
        current_direction=dp(mc.get("ocean_current_direction"), "°", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.80),
        sea_level=dp(mc.get("sea_level_height_msl"), "m", "Open-Meteo Marine", marine["url"], "model_current", marine_time, 0.78),
        wind_speed=dp(wc.get("wind_speed_10m"), "km/h", "Open-Meteo Weather", weather["url"], "weather_current", weather_time, 0.87),
        wind_direction=dp(wc.get("wind_direction_10m"), "°", "Open-Meteo Weather", weather["url"], "weather_current", weather_time, 0.87),
        pressure=dp(wc.get("pressure_msl"), "hPa", "Open-Meteo Weather", weather["url"], "weather_current", weather_time, 0.87),
        precipitation=dp(wc.get("precipitation"), "mm", "Open-Meteo Weather", weather["url"], "weather_current", weather_time, 0.87),
        weather_code=dp(wc.get("weather_code"), "WMO code", "Open-Meteo Weather", weather["url"], "weather_current", weather_time, 0.87),
    )

    if buoy:
        b = buoy["data"]
        # Use a nearby measured buoy value only when it exists and is reasonably close.
        bonus = max(0.0, 0.12 - buoy["distance_km"] / 5000.0)
        conf = min(0.98, 0.92 + bonus)
        if b.get("wave_height") is not None:
            c.wave_height = dp(b["wave_height"], "m", "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"])
        if b.get("wave_period") is not None:
            c.wave_period = dp(b["wave_period"], "s", "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"])
        if b.get("wave_direction") is not None:
            c.wave_direction = dp(b["wave_direction"], "°", "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"])
        if b.get("wind_speed") is not None:
            c.wind_speed = dp(b["wind_speed"], "m/s", "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"])
        if b.get("wind_direction") is not None:
            c.wind_direction = dp(b["wind_direction"], "°", "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"])
        if b.get("pressure") is not None:
            c.pressure = dp(b["pressure"], "hPa", "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"])

    sources = [
        {"name": "Open-Meteo Marine", "url": marine["url"], "type": "marine_model"},
        {"name": "Open-Meteo Weather", "url": weather["url"], "type": "weather_model"},
    ]
    if buoy:
        sources.append({
            "name": "NOAA NDBC",
            "url": buoy["source_url"],
            "type": "buoy_observation",
            "station": buoy["station"],
            "distance_km": buoy["distance_km"],
        })

    return location, c, sources, buoy
