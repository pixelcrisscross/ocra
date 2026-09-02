from schemas import SourceEvidence, WebResearch
from tools.incois_web import research_incois


def research_web(location):
    raw = research_incois(location.name, location.latitude, location.longitude)
    return WebResearch(sources=[SourceEvidence.model_validate(x) for x in raw])
