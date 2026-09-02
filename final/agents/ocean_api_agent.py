from schemas import Conditions, DataPoint, Location
from tools.geocode import resolve_location
from tools.open_meteo import fetch_marine, fetch_weather
from tools.noaa_ndbc import fetch_nearest_observation


def dp(value, unit, source, url, stype, ts, conf, distance=None, note=None):
    if value is None:
        return DataPoint(status="unavailable", note=note)
    return DataPoint(
        value=float(value), unit=unit, source=source, source_url=url,
        source_type=stype, timestamp=ts, distance_km=distance,
        confidence=conf, status="available", note=note,
    )


def resolve_location_from_intent(intent):
    loc = intent.location
    if loc.latitude is not None and loc.longitude is not None:
        return Location(name=loc.name, latitude=loc.latitude, longitude=loc.longitude)
    if not loc.name:
        raise ValueError("No location provided")
    r = resolve_location(loc.name)
    return Location(name=r["name"], latitude=r["latitude"], longitude=r["longitude"])


def fetch_live_conditions(intent):
    location = resolve_location_from_intent(intent)
    marine = fetch_marine(location.latitude, location.longitude)
    weather = fetch_weather(location.latitude, location.longitude)
    mc = marine["data"].get("current", {})
    wc = weather["data"].get("current", {})
    mt = mc.get("time")
    wt = wc.get("time")

    c = Conditions(
        sea_surface_temperature=dp(mc.get("sea_surface_temperature"), "°C", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        wave_height=dp(mc.get("wave_height"), "m", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        wave_period=dp(mc.get("wave_period"), "s", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        wave_direction=dp(mc.get("wave_direction"), "°", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        current_speed=dp(mc.get("ocean_current_velocity"), "km/h", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.80,
                         note="Modeled ocean current; coastal accuracy is limited."),
        current_direction=dp(mc.get("ocean_current_direction"), "°", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.80),
        sea_level=dp(mc.get("sea_level_height_msl"), "m", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.78,
                     note="Modeled sea level including tides; not for coastal navigation."),
        wind_speed=dp(wc.get("wind_speed_10m"), "km/h", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        wind_direction=dp(wc.get("wind_direction_10m"), "°", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        pressure=dp(wc.get("pressure_msl"), "hPa", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        precipitation=dp(wc.get("precipitation"), "mm", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        weather_code=dp(wc.get("weather_code"), "WMO code", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
    )

    buoy = None
    try:
        buoy = fetch_nearest_observation(location.latitude, location.longitude)
    except Exception:
        pass

    if buoy:
        b = buoy["data"]
        ts, url, d, conf = buoy["timestamp"], buoy["source_url"], buoy["distance_km"], 0.94
        if b.get("wave_height") is not None:
            c.wave_height = dp(b["wave_height"], "m", "NOAA NDBC", url, "observation", ts, conf, d)
        if b.get("wave_period") is not None:
            c.wave_period = dp(b["wave_period"], "s", "NOAA NDBC", url, "observation", ts, conf, d)
        if b.get("wave_direction") is not None:
            c.wave_direction = dp(b["wave_direction"], "°", "NOAA NDBC", url, "observation", ts, conf, d)
        if b.get("wind_speed") is not None:
            c.wind_speed = dp(b["wind_speed"], "m/s", "NOAA NDBC", url, "observation", ts, conf, d)
        if b.get("wind_direction") is not None:
            c.wind_direction = dp(b["wind_direction"], "°", "NOAA NDBC", url, "observation", ts, conf, d)
        if b.get("pressure") is not None:
            c.pressure = dp(b["pressure"], "hPa", "NOAA NDBC", url, "observation", ts, conf, d)
        if b.get("water_temperature") is not None:
            c.sea_surface_temperature = dp(b["water_temperature"], "°C", "NOAA NDBC", url, "observation", ts, conf, d)

    sources = [
        {"name": "Open-Meteo Marine", "url": marine["url"], "type": "marine_model"},
        {"name": "Open-Meteo Weather", "url": weather["url"], "type": "weather_model"},
        {"name": "OpenStreetMap Nominatim", "url": "https://nominatim.openstreetmap.org/", "type": "geocoder"},
    ]
    if buoy:
        sources.append({"name": "NOAA NDBC", "url": buoy["source_url"], "type": "buoy_observation", "station": buoy["station"], "distance_km": buoy["distance_km"]})
    return location, c, sources, buoy
