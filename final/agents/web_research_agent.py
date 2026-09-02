from schemas import SourceEvidence, WebResearch
from tools.incois_web import research_incois


def research_web(location):
    items = research_incois(location.name or "",)
    return WebResearch(sources=[SourceEvidence.model_validate(x) for x in items])
