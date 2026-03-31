import pytest

from testpaw.runtime.workspace import Workspace


@pytest.mark.asyncio
async def test_workspace_lifecycle_and_chat() -> None:
    ws = Workspace(agent_id="default")
    await ws.start()
    out = await ws.handle_user_message("hello")
    assert "mock/mock-chat-1" in out
    assert out.endswith("hello")
    await ws.stop()


@pytest.mark.asyncio
async def test_workspace_tool_branch() -> None:
    ws = Workspace(agent_id="default")
    await ws.start()
    out = await ws.handle_user_message("/calc 1+2*3")
    assert out == "Result: 7"
    await ws.stop()


@pytest.mark.asyncio
async def test_workspace_blocked_branch() -> None:
    ws = Workspace(agent_id="default")
    await ws.start()
    out = await ws.handle_user_message("please run rm -rf / now")
    assert out.startswith("Request blocked by policy")
    await ws.stop()
