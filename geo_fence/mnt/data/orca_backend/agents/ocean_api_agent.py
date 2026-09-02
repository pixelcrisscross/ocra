from schemas import Location, Conditions, DataPoint
from tools.geocode import resolve_location
from tools.open_meteo import fetch_marine, fetch_weather
from tools.noaa_ndbc import fetch_nearest_observation
from tools.incois_erddap import fetch_satellite_points


def dp(value, unit, source, url, source_type, timestamp, confidence, distance=None):
    if value is None:
        return DataPoint(status="unavailable")
    return DataPoint(value=float(value), unit=unit, source=source, source_url=url,
                     source_type=source_type, timestamp=timestamp,
                     distance_km=distance, confidence=confidence, status="available")


def resolve_location_obj(location: Location):
    if location.latitude is not None and location.longitude is not None:
        return location
    if not location.name:
        raise ValueError("A place name or coordinates are required")
    result = resolve_location(location.name)
    return Location(name=result["name"], latitude=result["latitude"], longitude=result["longitude"])


def fetch_all(intent):
    location = resolve_location_obj(intent.location)
    marine = fetch_marine(location.latitude, location.longitude, 3)
    weather = fetch_weather(location.latitude, location.longitude, 3)
    mc = marine["data"].get("current", {})
    wc = weather["data"].get("current", {})
    mt, wt = mc.get("time"), wc.get("time")

    c = Conditions(
        sea_surface_temperature=dp(mc.get("sea_surface_temperature"), "°C", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        wave_height=dp(mc.get("wave_height"), "m", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        wave_period=dp(mc.get("wave_period"), "s", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        wave_direction=dp(mc.get("wave_direction"), "°", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.86),
        current_speed=dp(mc.get("ocean_current_velocity"), "km/h", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.80),
        current_direction=dp(mc.get("ocean_current_direction"), "°", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.80),
        sea_level=dp(mc.get("sea_level_height_msl"), "m", "Open-Meteo Marine", marine["url"], "model_current", mt, 0.78),
        wind_speed=dp(wc.get("wind_speed_10m"), "km/h", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        wind_direction=dp(wc.get("wind_direction_10m"), "°", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        pressure=dp(wc.get("pressure_msl"), "hPa", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        precipitation=dp(wc.get("precipitation"), "mm", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
        weather_code=dp(wc.get("weather_code"), "WMO code", "Open-Meteo Weather", weather["url"], "weather_current", wt, 0.87),
    )

    sources = [
        {"name": "Open-Meteo Marine", "url": marine["url"], "type": "marine_model"},
        {"name": "Open-Meteo Weather", "url": weather["url"], "type": "weather_model"},
        {"name": "OpenStreetMap Nominatim", "url": "https://nominatim.openstreetmap.org/", "type": "geocoder"},
    ]

    try:
        buoy = fetch_nearest_observation(location.latitude, location.longitude)
    except Exception:
        buoy = None
    if buoy:
        sources.append({"name": "NOAA NDBC", "url": buoy["source_url"], "type": "buoy_observation", "station": buoy["station"], "distance_km": buoy["distance_km"]})
        conf = min(0.98, 0.92 + max(0.0, 0.12 - buoy["distance_km"] / 5000))
        bd = buoy["data"]
        mappings = [
            ("wave_height", bd.get("wave_height"), "m"),
            ("wave_period", bd.get("wave_period"), "s"),
            ("wave_direction", bd.get("wave_direction"), "°"),
            ("wind_speed", bd.get("wind_speed"), "m/s"),
            ("wind_direction", bd.get("wind_direction"), "°"),
            ("pressure", bd.get("pressure"), "hPa"),
        ]
        for name, value, unit in mappings:
            if value is not None:
                setattr(c, name, dp(value, unit, "NOAA NDBC", buoy["source_url"], "observation", buoy["timestamp"], conf, buoy["distance_km"]))

    # Satellite/INCOIS ERDDAP enrichment.
    sat = fetch_satellite_points(location.latitude, location.longitude)
    if sat.get("chlorophyll"):
        x = sat["chlorophyll"]
        c.chlorophyll = dp(x["value"], "mg/m3", "INCOIS ERDDAP - satellite ocean colour", x["url"], "satellite", x.get("timestamp"), 0.82)
        sources.append({"name": "INCOIS ERDDAP - Chlorophyll", "url": x["url"], "type": "satellite_ocean_colour"})
    if sat.get("mixed_layer_depth"):
        x = sat["mixed_layer_depth"]
        c.mixed_layer_depth = dp(x["value"], "m", "INCOIS ERDDAP - value added products", x["url"], "ocean_model", x.get("timestamp"), 0.80)
        sources.append({"name": "INCOIS ERDDAP - MLD", "url": x["url"], "type": "ocean_model"})

    return location, c, sources, buoy
