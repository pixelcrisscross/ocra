import csv
import io
import math
import requests
import xml.etree.ElementTree as ET

ACTIVE_URL = "https://www.ndbc.noaa.gov/activestations.xml"
REALTIME_URL = "https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_active_station(latitude: float, longitude: float):
    r = requests.get(ACTIVE_URL, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    stations = []
    for node in root.findall(".//station"):
        try:
            lat = float(node.attrib["lat"])
            lon = float(node.attrib["lon"])
        except (KeyError, ValueError):
            continue
        station_id = node.attrib.get("id")
        if not station_id:
            continue
        d = haversine_km(latitude, longitude, lat, lon)
        stations.append((d, station_id, lat, lon, node.attrib.get("name", station_id)))
    if not stations:
        return None
    return min(stations, key=lambda x: x[0])


def fetch_nearest_observation(latitude: float, longitude: float, max_distance_km: float = 500.0):
    nearest = nearest_active_station(latitude, longitude)
    if not nearest or nearest[0] > max_distance_km:
        return None

    distance, station_id, st_lat, st_lon, st_name = nearest
    url = REALTIME_URL.format(station=station_id)
    r = requests.get(url, timeout=20)
    r.raise_for_status()

    lines = [line for line in r.text.splitlines() if line.strip()]
    if len(lines) < 3:
        return None

    header = None
    units = None
    data_line = None
    for line in lines:
        if line.startswith("#YY"):
            header = line.lstrip("#").split()
        elif line.startswith("#yr"):
            units = line.lstrip("#").split()
        elif not line.startswith("#"):
            data_line = line.split()
            break

    if not header or not data_line:
        return None

    values = {}
    for i, key in enumerate(header):
        if i < len(data_line):
            values[key] = data_line[i]

    def num(key):
        v = values.get(key)
        if v in (None, "MM", "NaN", "nan"):
            return None
        try:
            return float(v)
        except ValueError:
            return None

    year = values.get("YY")
    month = values.get("MM")
    day = values.get("DD")
    hour = values.get("hh")
    minute = values.get("mm")
    timestamp = None
    if all(x and x.isdigit() for x in [year, month, day, hour, minute]):
        timestamp = f"{year}-{month.zfill(2)}-{day.zfill(2)}T{hour.zfill(2)}:{minute.zfill(2)}:00Z"

    return {
        "station": station_id,
        "name": st_name,
        "latitude": st_lat,
        "longitude": st_lon,
        "distance_km": round(distance, 2),
        "timestamp": timestamp,
        "source": "NOAA NDBC",
        "source_url": url,
        "data": {
            "wind_speed": num("WSPD"),
            "wind_direction": num("WDIR"),
            "wave_height": num("WVHT"),
            "wave_period": num("DPD"),
            "wave_direction": num("MWD"),
            "pressure": num("PRES"),
            "air_temperature": num("ATMP"),
            "water_temperature": num("WTMP"),
        },
    }
