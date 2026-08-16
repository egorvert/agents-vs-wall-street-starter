from typing import Any


def build_forecaster() -> Any:
    """Build a placeholder agent for producing structured projections."""

    from agents import Agent

    return Agent(
        name="Forecaster",
        instructions="Produce a concise projection and state uncertainty clearly.",
    )
