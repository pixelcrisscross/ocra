from urllib.parse import parse_qs, unquote, urlparse
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://html.duckduckgo.com/html/?q={}"
INCOIS_OSF_URL = "https://www.incois.gov.in/oceanservices/osfforecast.jsp"
INCOIS_GC_URL = "https://incois.gov.in/oceanservices/osf_gc_rsmc.jsp"
INCOIS_LSF_URL = "https://iioe-2.incois.gov.in/oceanservices/LSF/index.html"


def canonical_result_url(href: str) -> str:
    if not href.startswith("http"):
        return href
    parsed = urlparse(href)
    params = parse_qs(parsed.query)
    uddg = params.get("uddg")
    if uddg:
        return unquote(uddg[0])
    return href


def search_web(query: str, max_results=6):
    from urllib.parse import quote_plus
    r = requests.get(
        SEARCH_URL.format(quote_plus(query)),
        headers={"User-Agent": "Mozilla/5.0 ORCA/1.0"},
        timeout=20,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for result in soup.select(".result")[:max_results]:
        a = result.select_one(".result__a")
        s = result.select_one(".result__snippet")
        if not a:
            continue
        out.append({
            "title": a.get_text(" ", strip=True),
            "url": canonical_result_url(a.get("href", "")),
            "snippet": s.get_text(" ", strip=True) if s else "",
        })
    return out


def research_incois(location_name: str):
    queries = [
        f'site:incois.gov.in "{location_name}" ocean state forecast',
        'site:incois.gov.in "Ocean State Forecast" wave current',
        'site:erddap.incois.gov.in ocean salinity chlorophyll mixed layer depth',
    ]
    seen = set()
    evidence = []
    for q in queries:
        try:
            items = search_web(q)
        except Exception:
            continue
        for item in items:
            url = item["url"]
            if "incois.gov.in" not in url or url in seen:
                continue
            seen.add(url)
            evidence.append({
                "title": item["title"],
                "url": url,
                "source": "INCOIS",
                "source_type": "official_web",
                "snippet": item["snippet"],
                "relevance": 0.9,
            })

    # Always include canonical official products as traceable sources.
    canonical = [
        ("INCOIS Ocean State Forecast", INCOIS_OSF_URL, "official_forecast"),
        ("INCOIS Ocean State Forecast - General Circulation", INCOIS_GC_URL, "official_model"),
        ("INCOIS Location Specific Forecast", INCOIS_LSF_URL, "official_forecast"),
    ]
    existing = {x["url"] for x in evidence}
    for title, url, stype in canonical:
        if url not in existing:
            evidence.append({
                "title": title,
                "url": url,
                "source": "INCOIS",
                "source_type": stype,
                "snippet": "Official INCOIS product page; values are not extracted unless a machine-readable value is available.",
                "relevance": 0.95,
            })
    return evidence[:10]
