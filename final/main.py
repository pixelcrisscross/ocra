import json
import sys

from agents.conversation_agent import parse_user_query
from agents.ocean_api_agent import fetch_live_conditions
from agents.web_research_agent import research_web
from agents.fusion_agent import fuse
from agents.final_agent import generate_final


def run_orca(user_query: str):
    print("\n[LEVEL 1] Conversational AI...\n")
    intent = parse_user_query(user_query)
    print(json.dumps(intent.model_dump(), indent=2, ensure_ascii=False))

    print("\n[LEVEL 2] Live data acquisition...\n")
    location, conditions, live_sources, buoy = fetch_live_conditions(intent)
    print(json.dumps({
        "location": location.model_dump(),
        "conditions": conditions.model_dump(),
        "sources": live_sources,
        "nearest_buoy": buoy,
    }, indent=2, ensure_ascii=False))

    print("\n[LEVEL 3] Independent official-source research...\n")
    web_data = research_web(location)
    print(json.dumps(web_data.model_dump(), indent=2, ensure_ascii=False))

    print("\n[LEVEL 4] Validation + fusion + provenance...\n")
    unified = fuse(intent, location, conditions, web_data, live_sources)
    print(json.dumps(unified.model_dump(), indent=2, ensure_ascii=False))

    print("\n[LEVEL 5] Gemini ocean intelligence...\n")
    language = generate_final(unified)

    # Deterministic final assembly: measurements and sources NEVER come from Gemini.
    final = {
        "location": unified.location.model_dump(),
        "status": language.status,
        "summary": language.summary,
        "current_conditions": unified.conditions.model_dump(),
        "risks": unified.assessment.model_dump(),
        "data_quality": unified.quality.model_dump(),
        "observations": language.observations,
        "recommendations": language.recommendations,
        "sources": unified.sources + [
            {
                "name": s.source,
                "title": s.title,
                "url": s.url,
                "type": s.source_type,
                "relevance": s.relevance,
                "snippet": s.snippet,
            }
            for s in web_data.sources
        ],
    }

    print("\n========== FINAL ORCA JSON ==========\n")
    print(json.dumps(final, indent=2, ensure_ascii=False))
    return final


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("\nAsk ORCA: ").strip()
    if not query:
        raise SystemExit("Please enter a question.")
    run_orca(query)
