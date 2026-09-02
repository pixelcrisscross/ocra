import requests
import trafilatura


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/140 Safari/537.36"
    )
}


def scrape_page(url: str):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        text = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True
        )

        return text or ""

    except Exception:
        return ""