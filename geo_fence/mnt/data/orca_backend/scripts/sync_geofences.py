import json, math, os, re
from pathlib import Path
import requests
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import transform
from pyproj import Transformer

OUT = Path(os.getenv('ORCA_GEOFENCE_FILE', 'data/geofences.geojson'))
OUT.parent.mkdir(parents=True, exist_ok=True)

EEZ_URL = 'https://services1.arcgis.com/ZdmoaKLXhx5EdwBs/ArcGIS/rest/services/MarineRegions_EEZ/FeatureServer/0/query'
OVERPASS_URL = 'https://overpass-api.de/api/interpreter'


def fetch_eez():
    params = {
        'where': "SOVEREIGN1 IN ('India','Bangladesh','Myanmar','Sri Lanka','Pakistan','Maldives')",
        'outFields': 'GEONAME,SOVEREIGN1,ISO_SOV1,MRGID,AREA_KM2',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'geojson',
    }
    r = requests.get(EEZ_URL, params=params, timeout=90)
    r.raise_for_status()
    return r.json().get('features', [])


def fetch_marine_protected_areas():
    # OSM geometry is used only as a practical geometry feed. Designation/source
    # metadata is retained so the UI can clearly distinguish it from legal charts.
    q = r'''[out:json][timeout:90];
    (
      way["boundary"="protected_area"]
        ["name"~"Marine|marine|Gulf|Sundarbans|Gahirmatha|Bhitarkanika|Mahatma Gandhi|Rani Jhansi"]
        (6,68,24,92);
      way["protect_class"~"1|2|3|4|5"]
        ["name"](6,68,24,92);
    );
    out tags geom;'''
    r = requests.post(OVERPASS_URL, data=q, timeout=120)
    r.raise_for_status()
    elements = r.json().get('elements', [])
    out = []
    for e in elements:
        geom = e.get('geometry') or []
        coords = [(p['lon'], p['lat']) for p in geom]
        if len(coords) < 4 or coords[0] != coords[-1]:
            continue
        try:
            poly = Polygon(coords).buffer(0)
            if poly.is_empty:
                continue
            out.append({
                'type': 'Feature',
                'properties': {
                    'name': (e.get('tags') or {}).get('name', 'Protected area'),
                    'type': 'marine_protected_area',
                    'status': 'protected_area_candidate',
                    'source': 'OpenStreetMap geometry; verify designation against WII/MoEFCC/notification',
                    'source_url': 'https://www.openstreetmap.org/',
                    'legal_authority': 'VERIFY_OFFICIAL_NOTICE',
                },
                'geometry': mapping(poly),
            })
        except Exception:
            continue
    return out


def normalize_eez(features):
    out = []
    for f in features:
        p = f.get('properties', {})
        sovereign = p.get('SOVEREIGN1') or p.get('GEONAME') or 'Unknown'
        zone_type = 'indian_eez' if sovereign == 'India' else 'foreign_eez'
        out.append({
            'type': 'Feature',
            'properties': {
                'name': f"{sovereign} EEZ",
                'type': zone_type,
                'status': 'jurisdictional_reference',
                'source': 'Flanders Marine Institute / Marine Regions EEZ v12',
                'source_url': 'https://www.marineregions.org/downloads.php',
                'legal_authority': 'REFERENCE_ONLY_VERIFY_NATIONAL_CHART',
                'sovereign': sovereign,
                'mrgid': p.get('MRGID'),
            },
            'geometry': f.get('geometry'),
        })
    return out


def main():
    features = []
    try:
        features.extend(normalize_eez(fetch_eez()))
        print(f'EEZ features: {len(features)}')
    except Exception as e:
        print(f'EEZ sync failed: {e}')

    try:
        mpas = fetch_marine_protected_areas()
        features.extend(mpas)
        print(f'Protected-area geometries: {len(mpas)}')
    except Exception as e:
        print(f'Protected-area sync failed: {e}')

    payload = {
        'type': 'FeatureCollection',
        'name': 'ORCA Geofence Registry',
        'metadata': {
            'generated_by': 'scripts/sync_geofences.py',
            'warning': 'This registry is a decision-support layer, not a substitute for official nautical charts, notices, or legal boundary determinations.',
            'sources': [
                {'name': 'Marine Regions EEZ v12', 'url': 'https://www.marineregions.org/downloads.php'},
                {'name': 'India Code maritime-zone legislation/notifications', 'url': 'https://www.indiacode.nic.in/handle/123456789/1484'},
                {'name': 'Wildlife Institute of India ENVIS protected areas', 'url': 'https://www.wii.gov.in/envis/database.html'},
                {'name': 'OpenStreetMap geometry feed', 'url': 'https://www.openstreetmap.org/'},
            ],
        },
        'features': features,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(features)} features to {OUT}')

if __name__ == '__main__':
    main()
