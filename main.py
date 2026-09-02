import json

from agents.conversation_agent import parse_user_query
from agents.ocean_api_agent import get_api_data
from agents.web_research_agent import research_web
from agents.fusion_agent import fuse_data
from agents.final_agent import generate_final_response


def run_orca(user_query: str):

    print("\n[LEVEL 1] Understanding user...\n")

    intent = parse_user_query(
        user_query
    )

    print(
        json.dumps(
            intent.model_dump(),
            indent=2
        )
    )

    print("\n[LEVEL 2] Fetching live ocean data...\n")

    api_data = get_api_data(
        intent
    )

    print(
        json.dumps(
            api_data.model_dump(),
            indent=2
        )
    )

    print("\n[LEVEL 3] Researching web sources...\n")

    web_data = research_web(
        intent
    )

    print(
        json.dumps(
            web_data.model_dump(),
            indent=2
        )
    )

    print("\n[LEVEL 4] Fusing data...\n")

    unified = fuse_data(
        intent,
        api_data,
        web_data
    )

    print(
        json.dumps(
            unified.model_dump(),
            indent=2
        )
    )

    print("\n[LEVEL 5] Gemini ocean intelligence...\n")

    final = generate_final_response(
        unified
    )

    print(
        json.dumps(
            final.model_dump(),
            indent=2
        )
    )

    return final


if __name__ == "__main__":

    query = input(
        "\nAsk ORCA: "
    )

    result = run_orca(
        query
    )