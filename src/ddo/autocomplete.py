import requests


LIVESEARCH_URL = "https://ws.dsl.dk/ddo/livesearch"


def get_completions(ctx, args, incomplete) -> list:
    """
    Fetch word completions from the livesearch endpoint

    :param ctx: Click context (ignored)
    :param args: Command arguments (ignored)
    :param incomplete: Partial word to complete
    :return: List of suggested completions
    """
    try:
        # Send request to livesearch endpoint
        response = requests.get(
            LIVESEARCH_URL,
            params={"text": incomplete, "format": "json", "app": "ios", "size": 30},
        )
        response.raise_for_status()

        # Parse JSON response
        suggestions = response.json()

        # Return only the words, filtering those that start with the incomplete part
        return [
            suggestion
            for suggestion in suggestions
            if suggestion.lower().startswith(incomplete.lower())
        ]

    except (requests.RequestException, ValueError):
        # Return empty list if request fails or response is not JSON
        return []
