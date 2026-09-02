import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

SEARCH_URL = "https://html.duckduckgo.com/html/?q={}"

INCOIS_HINTS = [
    "site:incois.gov.in ocean state forecast",
    "site:erddap.incois.gov.in ERDDAP ocean data",
]


def search_web(query: str, max_results: int = 5):
    url = SEARCH_URL.format(quote_plus(query))
    headers = {"User-Agent": "Mozilla/5.0 ORCA/1.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for result in soup.select(".result")[:max_results]:
        a = result.select_one(".result__a")
        snippet = result.select_one(".result__snippet")
        if not a:
            continue
        href = a.get("href", "")
        results.append({
            "title": a.get_text(" ", strip=True),
            "url": href,
            "snippet": snippet.get_text(" ", strip=True) if snippet else "",
        })
    return results


def research_incois(location_name: str, latitude: float, longitude: float):
    queries = [
        f'site:incois.gov.in "{location_name}" ocean forecast wave current',
        f'site:erddap.incois.gov.in "sea surface temperature" "salinity" ocean',
        f'site:incois.gov.in "Ocean State Forecast"',
    ]
    evidence = []
    seen = set()
    for q in queries:
        try:
            items = search_web(q, 5)
        except Exception as exc:
            evidence.append({
                "title": "INCOIS web search unavailable",
                "url": "https://www.incois.gov.in/",
                "source": "INCOIS",
                "source_type": "official_web",
                "snippet": str(exc),
                "relevance": 0.2,
            })
            continue
        for item in items:
            url = item["url"]
            if url in seen:
                continue
            seen.add(url)
            if "incois.gov.in" not in url:
                continue
            evidence.append({
                "title": item["title"],
                "url": url,
                "source": "INCOIS",
                "source_type": "official_web",
                "snippet": item["snippet"],
                "relevance": 0.9,
            })
    return evidence[:8]
