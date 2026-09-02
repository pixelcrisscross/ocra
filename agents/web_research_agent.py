from schemas import Intent, WebResearch, WebEvidence, Location

from tools.web_search import search_web
from tools.web_scraper import scrape_page


OFFICIAL_DOMAINS = [
    "incois.gov.in",
    "imd.gov.in",
    "noaa.gov",
    "ndbc.noaa.gov",
    "esa.int",
    "copernicus.eu"
]


def authority_score(url: str):

    for domain in OFFICIAL_DOMAINS:

        if domain in url.lower():
            return 1.0

    return 0.5


def research_web(intent: Intent):

    location = intent.location

    location_name = (
        location.name
        or f"{location.latitude}, {location.longitude}"
    )

    search_query = (
        f"{location_name} ocean sea temperature waves "
        f"currents marine conditions latest"
    )

    results = search_web(
        search_query,
        max_results=6
    )

    evidence = []

    for item in results:

        url = item["url"]

        score = authority_score(url)

        text = scrape_page(url)

        snippet = item["snippet"]

        if text:
            snippet = text[:1200]

        evidence.append(
            WebEvidence(
                title=item["title"],
                url=url,
                source=url.split("/")[2],
                snippet=snippet,
                relevance=score
            )
        )

    evidence.sort(
        key=lambda x: x.relevance,
        reverse=True
    )

    return WebResearch(
        location=Location(
            latitude=location.latitude,
            longitude=location.longitude,
            name=location.name
        ),
        sources=evidence[:5]
    )