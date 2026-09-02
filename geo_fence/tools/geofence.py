import json
import math
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer
from config import ORCA_GEOFENCE_FILE

_TO_3857 = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True).transform


def check_geofences(lat, lon, proximity_km=25.0):
    path = Path(ORCA_GEOFENCE_FILE)
    if not path.exists():
        return [], {
            'status': 'no_geofence_dataset_configured',
            'feature_count': 0,
        }

    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return [], {
            'status': 'geofence_dataset_error',
            'error': str(exc),
        }

    p_ll = Point(float(lon), float(lat))
    p_m = transform(_TO_3857, p_ll)
    hits = []

    for feature in payload.get('features', []):
        try:
            geom = shape(feature['geometry'])
            if geom.is_empty:
                continue
            projected = transform(_TO_3857, geom)
            inside = geom.contains(p_ll) or geom.touches(p_ll)
            distance_km = 0.0 if inside else projected.distance(p_m) / 1000.0
            if inside or distance_km <= proximity_km:
                props = feature.get('properties', {})
                hits.append({
                    'name': props.get('name', 'Unnamed zone'),
                    'zone_type': props.get('type', 'reference_zone'),
                    'inside': bool(inside),
                    'distance_km': round(float(distance_km), 3),
                    'source': props.get('source', 'Configured GeoJSON'),
                    'source_url': props.get('source_url'),
                    'legal_authority': props.get('legal_authority', 'VERIFY'),
                    'status': props.get('status', 'reference'),
                })
        except Exception:
            continue

    hits.sort(key=lambda x: (not x['inside'], x['distance_km']))
    return hits, {
        'status': 'ok',
        'count': len(hits),
        'dataset_features': len(payload.get('features', [])),
        'proximity_km': proximity_km,
        'dataset_warning': payload.get('metadata', {}).get('warning'),
        'dataset_sources': payload.get('metadata', {}).get('sources', []),
    }
