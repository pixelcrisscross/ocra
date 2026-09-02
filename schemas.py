from typing import Optional, List
from pydantic import BaseModel


class Location(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None


class Intent(BaseModel):
    user_query: str
    intent: str
    location: Location
    requested_parameters: List[str]
    time_range: str
    region: Optional[str] = None


class OceanVariable(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    timestamp: Optional[str] = None


class OceanAPIData(BaseModel):
    location: Location
    source: str
    timestamp: Optional[str] = None

    sea_surface_temperature: Optional[OceanVariable] = None
    wave_height: Optional[OceanVariable] = None
    wave_period: Optional[OceanVariable] = None
    wave_direction: Optional[OceanVariable] = None

    ocean_current_speed: Optional[OceanVariable] = None
    ocean_current_direction: Optional[OceanVariable] = None

    sea_level: Optional[OceanVariable] = None


class WebEvidence(BaseModel):
    title: str
    url: str
    source: str
    snippet: str
    relevance: float = 0.0


class WebResearch(BaseModel):
    location: Location
    sources: List[WebEvidence]


class RiskAssessment(BaseModel):
    overall_status: str
    marine_health: str
    wave_risk: str
    current_risk: str
    thermal_risk: str
    weather_risk: str
    confidence: float


class UnifiedOceanData(BaseModel):
    intent: Intent
    api_data: List[OceanAPIData]
    web_data: WebResearch
    assessment: RiskAssessment


class FinalResponse(BaseModel):
    location: Location
    status: str
    summary: str

    current_conditions: dict
    risks: dict
    observations: List[str]
    recommendations: List[str]

    sources: List[dict]