from typing import Any

from app.agents.critic import build_critic
from app.agents.forecaster import build_forecaster
from app.agents.researcher import build_researcher
from app.config.settings import get_settings


class AgentUnavailableError(RuntimeError):
    """Raised when optional agent functionality is used without configuration."""


def build_coordinator() -> Any:
    """Wire specialist placeholders with the OpenAI Agents SDK."""

    from agents import Agent

    return Agent(
        name="Coordinator",
        instructions="Delegate only when useful, then return a short synthesized answer.",
        handoffs=[build_researcher(), build_forecaster(), build_critic()],
    )


async def run_coordinator(prompt: str) -> str:
    """Run the optional coordinator without coupling it to routes or persistence."""

    if not get_settings().agents_enabled:
        raise AgentUnavailableError(
            "Agent functionality is disabled. Set OPENAI_API_KEY to enable it."
        )

    from agents import Runner

    result = await Runner.run(build_coordinator(), prompt)
    return str(result.final_output)
