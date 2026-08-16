import asyncio

import pytest

from app.agents.coordinator import AgentUnavailableError, build_coordinator, run_coordinator
from app.config.settings import get_settings


def test_agent_run_fails_cleanly_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    with pytest.raises(AgentUnavailableError, match="disabled"):
        asyncio.run(run_coordinator("hello"))

    get_settings.cache_clear()


def test_agent_graph_can_be_built_without_api_key() -> None:
    coordinator = build_coordinator()

    assert coordinator.name == "Coordinator"
    assert len(coordinator.handoffs) == 3
