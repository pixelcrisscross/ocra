from schemas import (
    Intent,
    OceanAPIData,
    WebResearch,
    RiskAssessment,
    UnifiedOceanData
)


def classify_temperature(temp):

    if temp is None:
        return "unknown"

    if temp >= 30:
        return "high"

    if temp >= 28:
        return "moderate"

    return "normal"


def classify_wave(height):

    if height is None:
        return "unknown"

    if height >= 3:
        return "high"

    if height >= 1.5:
        return "moderate"

    return "low"


def classify_current(speed):

    if speed is None:
        return "unknown"

    if speed >= 3:
        return "high"

    if speed >= 1.5:
        return "moderate"

    return "low"


def build_assessment(
    api_data: OceanAPIData
):

    temp = (
        api_data.sea_surface_temperature.value
        if api_data.sea_surface_temperature
        else None
    )

    wave = (
        api_data.wave_height.value
        if api_data.wave_height
        else None
    )

    current = (
        api_data.ocean_current_speed.value
        if api_data.ocean_current_speed
        else None
    )

    thermal = classify_temperature(temp)
    wave_risk = classify_wave(wave)
    current_risk = classify_current(current)

    scores = []

    if thermal == "high":
        scores.append(2)

    elif thermal == "moderate":
        scores.append(1)

    else:
        scores.append(0)

    if wave_risk == "high":
        scores.append(2)

    elif wave_risk == "moderate":
        scores.append(1)

    else:
        scores.append(0)

    if current_risk == "high":
        scores.append(2)

    elif current_risk == "moderate":
        scores.append(1)

    else:
        scores.append(0)

    total = sum(scores)

    if total >= 5:
        overall = "high"

    elif total >= 2:
        overall = "moderate"

    else:
        overall = "low"

    marine_health = (
        "attention_required"
        if total >= 4
        else "normal"
    )

    return RiskAssessment(

        overall_status=overall,

        marine_health=marine_health,

        wave_risk=wave_risk,

        current_risk=current_risk,

        thermal_risk=thermal,

        weather_risk="unknown",

        confidence=0.85
    )


def fuse_data(
    intent: Intent,
    api_data,
    web_data
):

    assessment = build_assessment(api_data)

    return UnifiedOceanData(

        intent=intent,

        api_data=[api_data],

        web_data=web_data,

        assessment=assessment
    )