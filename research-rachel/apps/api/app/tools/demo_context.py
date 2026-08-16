from typing import Any


def get_demo_context(query: str) -> dict[str, Any]:
    """Return deterministic context; replace or extend this with sponsor API calls.

    Tool functions should validate inputs, return serializable data, and avoid hidden
    side effects. API credentials and retry behavior belong in integration services.
    """

    normalized_query = query.strip()
    return {
        "query": normalized_query,
        "context": f"Placeholder context for: {normalized_query}",
        "source": "local-demo",
    }
