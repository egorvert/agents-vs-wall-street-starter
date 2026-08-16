from typing import Any


def build_critic() -> Any:
    """Build a placeholder agent for checking evidence and assumptions."""

    from agents import Agent

    return Agent(
        name="Critic",
        instructions="Check claims, assumptions, and missing evidence. Be concise.",
    )
