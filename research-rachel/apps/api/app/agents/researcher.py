from typing import Any

from app.tools.demo_context import get_demo_context


def build_researcher() -> Any:
    """Build a small research agent with one deterministic local tool."""

    from agents import Agent, function_tool

    return Agent(
        name="Researcher",
        instructions="Gather relevant context with the available tools and report sources.",
        tools=[function_tool(get_demo_context)],
    )
