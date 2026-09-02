from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 5):

    results = []

    with DDGS() as ddgs:

        for item in ddgs.text(
            query,
            max_results=max_results
        ):

            results.append({
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })

    return results