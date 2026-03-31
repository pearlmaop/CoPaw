import pytest

from testpaw.app import MultiAgentManager


@pytest.mark.asyncio
async def test_multi_agent_manager_lifecycle() -> None:
    manager = MultiAgentManager()

    ws_a = await manager.get_agent("default")
    ws_b = await manager.get_agent("qa")

    assert ws_a.agent_id == "default"
    assert ws_b.agent_id == "qa"
    assert manager.list_loaded_agents() == ["default", "qa"]

    await manager.stop_all()
    assert manager.list_loaded_agents() == []
