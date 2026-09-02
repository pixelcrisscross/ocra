import uuid
from schemas import UnifiedData, ChatResponse, Evidence
from agents.conversation_agent import parse_user_query
from agents.planner import build_plan
from agents.ocean_api_agent import fetch_all
from agents.web_research_agent import research
from agents.hazard_agent import gather_hazards
from agents.fusion_agent import fuse
from agents.final_agent import generate_final
from agents.analytics_agent import fishing_productivity
from tools.geofence import check_geofences


class Orchestrator:
    def __init__(self, session_store):
        self.sessions = session_store

    def run(self, message, conversation_id, supplied_location=None):
        request_id = f"orca_{uuid.uuid4().hex[:10]}"
        history = self.sessions.get(conversation_id, [])
        context = "\n".join(x["message"] for x in history[-6:])
        enriched = f"Previous context:\n{context}\n\nCurrent request:\n{message}" if context else message

        intent = parse_user_query(enriched, supplied_location)
        plan = build_plan(intent)

        location, conditions, live_sources, buoy = fetch_all(intent)
        evidence, web_hazards, pfz = research(location, intent)
        hazard_evidence, runtime_hazards = gather_hazards(location, intent)
        evidence.extend(hazard_evidence)
        hazards = web_hazards + runtime_hazards

        geo_hits, geo_meta = check_geofences(location.latitude, location.longitude)
        route = None
        productivity = fishing_productivity(conditions) if intent.requires_productivity else {}

        quality, assessment = fuse(
            intent, location, conditions, hazards,
            pfz, geo_hits, route, evidence, live_sources,
        )

        unified = UnifiedData(
            intent=intent,
            location=location,
            conditions=conditions,
            hazards=hazards,
            pfz=pfz,
            geofences=geo_hits,
            route=route,
            productivity=productivity,
            quality=quality,
            assessment=assessment,
            evidence=evidence,
        )

        language = generate_final(unified)
        # Safety state is deterministic; Gemini only verbalizes it.
        language.status = assessment["safety_assessment"]

        sources = list(live_sources)
        for e in evidence:
            sources.append({
                "name": e.source,
                "title": e.title,
                "url": e.url,
                "type": e.type,
                "confidence": e.confidence,
                "note": e.note,
            })
        sources = _dedupe_sources(sources)
        if geo_meta.get("status") == "ok":
            sources.append({"name": "Configured GeoJSON geofences", "url": "local:data/geofences.geojson", "type": "geospatial_boundary"})

        final = ChatResponse(
            request_id=request_id,
            conversation_id=conversation_id,
            language=intent.language,
            location=location,
            intent={**intent.model_dump(), "plan": plan.tasks},
            answer=language.model_dump(),
            ocean={k: v for k, v in conditions.model_dump().items() if k in {"sea_surface_temperature","wave_height","wave_period","wave_direction","current_speed","current_direction","sea_level","salinity","chlorophyll","mixed_layer_depth"}},
            weather={k: v for k, v in conditions.model_dump().items() if k in {"wind_speed","wind_direction","pressure","precipitation","weather_code"}},
            pfz=[p.model_dump() for p in pfz],
            hazards=[h.model_dump() for h in hazards],
            geofencing=geo_hits,
            route=route.model_dump() if route else None,
            productivity=productivity,
            data_quality=quality.model_dump(),
            evidence=[e.model_dump() for e in evidence],
            sources=sources,
            map={
                "center": {"latitude": location.latitude, "longitude": location.longitude},
                "markers": [{"type": "location", "latitude": location.latitude, "longitude": location.longitude, "label": location.name or "Selected location"}],
                "route": [],
                "layers": ["ocean_conditions", "weather", "hazards", "pfz", "geofences"],
            },
        )

        history.extend([
            {"role": "user", "message": message},
            {"role": "assistant", "message": language.summary},
        ])
        self.sessions[conversation_id] = history[-20:]
        return final


def _dedupe_sources(items):
    result, seen = [], set()
    for item in items:
        key = item.get("url") or item.get("name")
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
