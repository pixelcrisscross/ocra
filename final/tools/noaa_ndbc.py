import math
import requests
import xml.etree.ElementTree as ET

ACTIVE_URL = "https://www.ndbc.noaa.gov/activestations.xml"
REALTIME_URL = "https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))


def nearest_active_station(lat, lon, max_distance_km=500):
    r = requests.get(ACTIVE_URL, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    best = None
    for node in root.findall(".//station"):
        try:
            slat = float(node.attrib["lat"])
            slon = float(node.attrib["lon"])
        except (KeyError, ValueError):
            continue
        sid = node.attrib.get("id")
        if not sid:
            continue
        d = haversine_km(lat, lon, slat, slon)
        candidate = (d, sid, slat, slon, node.attrib.get("name", sid))
        if best is None or d < best[0]:
            best = candidate
    if best and best[0] <= max_distance_km:
        return best
    return None


def fetch_nearest_observation(lat, lon, max_distance_km=500):
    nearest = nearest_active_station(lat, lon, max_distance_km)
    if not nearest:
        return None
    distance, sid, slat, slon, name = nearest
    url = REALTIME_URL.format(station=sid)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    lines = [x for x in r.text.splitlines() if x.strip()]
    header = None
    data = None
    for line in lines:
        if line.startswith("#YY"):
            header = line.lstrip("#").split()
        elif not line.startswith("#"):
            data = line.split()
            break
    if not header or not data:
        return None
    row = {k: data[i] for i, k in enumerate(header) if i < len(data)}

    def num(k):
        v = row.get(k)
        if v in (None, "MM", "NaN", "nan"):
            return None
        try:
            return float(v)
        except ValueError:
            return None

    timestamp = None
    if all(row.get(k, "").isdigit() for k in ("YY", "MM", "DD", "hh", "mm")):
        timestamp = f"{row['YY']}-{row['MM'].zfill(2)}-{row['DD'].zfill(2)}T{row['hh'].zfill(2)}:{row['mm'].zfill(2)}:00Z"

    return {
        "station": sid,
        "name": name,
        "latitude": slat,
        "longitude": slon,
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
            "water_temperature": num("WTMP"),
        },
    }
