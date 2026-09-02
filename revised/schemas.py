from typing import Any, Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Intent(BaseModel):
    user_query: str
    intent: str
    location: Location
    requested_parameters: list[str] = Field(default_factory=list)
    time_range: str = "current"
    region: Optional[str] = None


class DataPoint(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    timestamp: Optional[str] = None
    distance_km: Optional[float] = None
    confidence: float = 0.0
    status: str = "available"


class Conditions(BaseModel):
    sea_surface_temperature: DataPoint = Field(default_factory=DataPoint)
    wave_height: DataPoint = Field(default_factory=DataPoint)
    wave_period: DataPoint = Field(default_factory=DataPoint)
    wave_direction: DataPoint = Field(default_factory=DataPoint)
    current_speed: DataPoint = Field(default_factory=DataPoint)
    current_direction: DataPoint = Field(default_factory=DataPoint)
    sea_level: DataPoint = Field(default_factory=DataPoint)
    wind_speed: DataPoint = Field(default_factory=DataPoint)
    wind_direction: DataPoint = Field(default_factory=DataPoint)
    pressure: DataPoint = Field(default_factory=DataPoint)
    precipitation: DataPoint = Field(default_factory=DataPoint)
    weather_code: DataPoint = Field(default_factory=DataPoint)
    salinity: DataPoint = Field(default_factory=DataPoint)
    chlorophyll: DataPoint = Field(default_factory=DataPoint)
    mixed_layer_depth: DataPoint = Field(default_factory=DataPoint)


class SourceEvidence(BaseModel):
    title: str
    url: str
    source: str
    source_type: str
    snippet: str = ""
    timestamp: Optional[str] = None
    relevance: float = 0.0


class WebResearch(BaseModel):
    sources: list[SourceEvidence] = Field(default_factory=list)


class DataQuality(BaseModel):
    requested: int = 0
    available: int = 0
    completeness_percent: float = 0.0
    missing: list[str] = Field(default_factory=list)
    source_count: int = 0


class RiskAssessment(BaseModel):
    overall_status: str
    wave_risk: str
    wind_risk: str
    current_risk: str
    thermal_condition: str
    weather_risk: str
    marine_health_status: str
    confidence: float


class UnifiedData(BaseModel):
    intent: Intent
    location: Location
    conditions: Conditions
    web_research: WebResearch
    quality: DataQuality
    assessment: RiskAssessment
    sources: list[dict[str, Any]] = Field(default_factory=list)


class FinalLanguageOutput(BaseModel):
    status: str
    summary: str
    observations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
