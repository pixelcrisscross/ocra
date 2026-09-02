from schemas import DataQuality, RiskAssessment, UnifiedData


def risk_from_wave(v):
    if v is None: return "unknown"
    if v >= 3.0: return "high"
    if v >= 1.5: return "moderate"
    return "low"


def risk_from_wind(v):
    if v is None: return "unknown"
    # Open-Meteo is km/h unless replaced by NDBC, which is converted below by field source handling if needed.
    if v >= 45: return "high"
    if v >= 25: return "moderate"
    return "low"


def risk_from_current(v):
    if v is None: return "unknown"
    if v >= 3: return "high"
    if v >= 1.5: return "moderate"
    return "low"


def thermal(v):
    if v is None: return "unknown"
    if v >= 30: return "warm"
    if v >= 28: return "moderately_warm"
    return "normal"


def fuse(intent, location, conditions, web_research, sources):
    params = [
        "sea_surface_temperature", "wave_height", "wave_period", "wave_direction",
        "current_speed", "current_direction", "sea_level", "wind_speed",
        "wind_direction", "pressure", "precipitation", "weather_code",
        "salinity", "chlorophyll", "mixed_layer_depth",
    ]
    available = []
    missing = []
    for p in params:
        dp = getattr(conditions, p)
        if dp.value is None:
            missing.append(p)
        else:
            available.append(p)

    quality = DataQuality(
        requested=len(params),
        available=len(available),
        completeness_percent=round(100 * len(available) / len(params), 1),
        missing=missing,
        source_count=len(sources),
    )

    wave_risk = risk_from_wave(conditions.wave_height.value)
    wind_risk = risk_from_wind(conditions.wind_speed.value)
    current_risk = risk_from_current(conditions.current_speed.value)
    thermal_condition = thermal(conditions.sea_surface_temperature.value)

    weather_risk = "high" if conditions.weather_code.value in {95, 96, 99} else "moderate" if conditions.precipitation.value and conditions.precipitation.value > 5 else "low"

    risks = [wave_risk, wind_risk, current_risk, weather_risk]
    overall = "high" if "high" in risks else "moderate" if "moderate" in risks or quality.completeness_percent < 70 else "low"

    # This is intentionally not a biological-health diagnosis.
    health = "not_assessed" if conditions.salinity.value is None and conditions.chlorophyll.value is None else "partial_assessment"

    confidence_values = [getattr(conditions, p).confidence for p in available]
    confidence = round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else 0.0

    assessment = RiskAssessment(
        overall_status=overall,
        wave_risk=wave_risk,
        wind_risk=wind_risk,
        current_risk=current_risk,
        thermal_condition=thermal_condition,
        weather_risk=weather_risk,
        marine_health_status=health,
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
