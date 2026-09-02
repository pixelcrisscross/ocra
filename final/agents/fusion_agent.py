from schemas import DataQuality, RiskAssessment, UnifiedData

ALL_PARAMETERS = [
    "sea_surface_temperature", "wave_height", "wave_period", "wave_direction",
    "current_speed", "current_direction", "sea_level", "wind_speed",
    "wind_direction", "pressure", "precipitation", "weather_code",
    "salinity", "chlorophyll", "mixed_layer_depth",
]
CORE_SAFETY = ["wave_height", "wind_speed", "wave_period"]
BIO = ["salinity", "chlorophyll", "mixed_layer_depth"]


def wave_risk(x):
    if x is None: return "unknown"
    if x >= 3.0: return "high"
    if x >= 1.5: return "moderate"
    return "low"


def wind_risk(x):
    if x is None: return "unknown"
    if x >= 45: return "high"
    if x >= 25: return "moderate"
    return "low"


def current_risk(x):
    if x is None: return "unknown"
    if x >= 3: return "high"
    if x >= 1.5: return "moderate"
    return "low"


def thermal(x):
    if x is None: return "unknown"
    if x >= 30: return "warm"
    if x >= 28: return "moderately_warm"
    return "normal"


def fuse(intent, location, conditions, web_research, sources):
    missing = []
    available = []
    for p in ALL_PARAMETERS:
        item = getattr(conditions, p)
        if item.value is None:
            missing.append(p)
        else:
            available.append(p)

    critical_missing = [p for p in CORE_SAFETY if p in missing]
    completeness = round(100 * len(available) / len(ALL_PARAMETERS), 1)

    wr = wave_risk(conditions.wave_height.value)
    wdr = wind_risk(conditions.wind_speed.value)
    cr = current_risk(conditions.current_speed.value)
    tc = thermal(conditions.sea_surface_temperature.value)

    code = conditions.weather_code.value
    precip = conditions.precipitation.value
    if code in {95, 96, 99}:
        weather_risk = "high"
    elif precip is not None and precip > 5:
        weather_risk = "moderate"
    else:
        weather_risk = "low" if code is not None else "unknown"

    risks = [wr, wdr, cr, weather_risk]
    if "high" in risks:
        overall = "high"
    elif "moderate" in risks:
        overall = "moderate"
    else:
        overall = "low"

    if critical_missing:
        safety = "insufficient_data_for_safety_assessment"
        # Do not label the result low-risk when a critical safety input is missing.
        if overall == "low":
            overall = "unknown"
    else:
        safety = "screening_assessment_only"

    bio_available = any(
        getattr(conditions, p).value is not None for p in BIO
    )
    health = "partial_assessment" if bio_available else "not_assessed"

    vals = [getattr(conditions, p).confidence for p in available]
    confidence = round(sum(vals) / len(vals), 2) if vals else 0.0

    quality = DataQuality(
        requested=len(ALL_PARAMETERS),
        available=len(available),
        completeness_percent=completeness,
        missing=missing,
        critical_missing=critical_missing,
        source_count=len(sources) + len(web_research.sources),
    )

    assessment = RiskAssessment(
        overall_status=overall,
        wave_risk=wr,
        wind_risk=wdr,
        current_risk=cr,
        thermal_condition=tc,
        weather_risk=weather_risk,
        marine_health_status=health,
        safety_assessment=safety,
        confidence=confidence,
    )

    return UnifiedData(
        intent=intent,
        location=location,
        conditions=conditions,
        web_research=web_research,
        quality=quality,
        assessment=assessment,
        sources=sources,
    )
