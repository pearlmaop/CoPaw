# -*- coding: utf-8 -*-
"""Unit tests for the CoPaw LangGraph agent implementation.

All tests are fully self-contained: they use mock LLMs and do not require
any real API keys, external services, or filesystem agent configurations.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------


class _MockLLM(BaseChatModel):
    """Deterministic mock LLM for unit tests.

    Cycles through ``responses`` in order, repeating from the start when
    exhausted.  Call ``reset()`` between independent test cases.
    """

    responses: list[Any] = ["Hello!"]
    _call_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: list,
        stop: Optional[list] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        idx = self._call_count % len(self.responses)
        self._call_count += 1
        response = self.responses[idx]
        if isinstance(response, AIMessage):
            msg = response
        else:
            msg = AIMessage(content=str(response))
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def bind_tools(self, tools: list, **kwargs: Any) -> "_MockLLM":  # type: ignore[override]
        return self

    def reset(self) -> None:
        self._call_count = 0


def _make_tool_calling_llm(
    tool_calls: list[dict],
    final_response: str = "Done.",
) -> _MockLLM:
    """Create a mock LLM that first emits tool calls, then gives a final answer."""
    first_msg = AIMessage(content="", tool_calls=tool_calls)
    second_msg = AIMessage(content=final_response)
    return _MockLLM(responses=[first_msg, second_msg])


@tool
def _echo_tool(text: str) -> str:
    """Echo the input text back."""
    return f"echo: {text}"


@tool
def _fail_tool(text: str) -> str:
    """Always raises an exception."""
    raise RuntimeError("intentional tool failure")


# ---------------------------------------------------------------------------
# 1. Module imports
# ---------------------------------------------------------------------------


class TestModuleImports:
    """Verify that all public exports can be imported without errors."""

    def test_package_imports(self) -> None:
        from copaw.agents.langgraph_agent import (  # noqa: F401
            CoPawAgentState,
            CoPawLangGraphAgent,
            LangGraphAgentRunner,
            adapt_tools,
            copaw_tool_to_langchain,
            create_copaw_graph,
            create_langchain_llm,
            tool_response_to_str,
        )

    def test_state_module(self) -> None:
        from copaw.agents.langgraph_agent.state import CoPawAgentState

        assert "messages" in CoPawAgentState.__annotations__

    def test_tools_adapter_module(self) -> None:
        from copaw.agents.langgraph_agent.tools_adapter import (
            adapt_tools,
            copaw_tool_to_langchain,
            tool_response_to_str,
        )

        assert callable(adapt_tools)
        assert callable(copaw_tool_to_langchain)
        assert callable(tool_response_to_str)

    def test_graph_module(self) -> None:
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        assert callable(create_copaw_graph)

    def test_llm_factory_module(self) -> None:
        from copaw.agents.langgraph_agent.llm_factory import create_langchain_llm

        assert callable(create_langchain_llm)

    def test_agent_module(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        assert callable(CoPawLangGraphAgent)

    def test_runner_module(self) -> None:
        from copaw.agents.langgraph_agent.runner import LangGraphAgentRunner

        assert callable(LangGraphAgentRunner)


# ---------------------------------------------------------------------------
# 2. tools_adapter.py
# ---------------------------------------------------------------------------


class TestToolsAdapter:
    """Tests for CoPaw→LangChain tool conversion."""

    def test_tool_response_to_str_with_text_block(self) -> None:
        """Extracts text from ToolResponse.content text blocks."""
        from agentscope.message import TextBlock  # type: ignore[import]
        from agentscope.tool import ToolResponse  # type: ignore[import]

        from copaw.agents.langgraph_agent.tools_adapter import tool_response_to_str

        tr = ToolResponse(content=[TextBlock(type="text", text="hello world")])
        assert tool_response_to_str(tr) == "hello world"

    def test_tool_response_to_str_multiple_blocks(self) -> None:
        from agentscope.message import TextBlock  # type: ignore[import]
        from agentscope.tool import ToolResponse  # type: ignore[import]

        from copaw.agents.langgraph_agent.tools_adapter import tool_response_to_str

        tr = ToolResponse(
            content=[
                TextBlock(type="text", text="line 1"),
                TextBlock(type="text", text="line 2"),
            ]
        )
        assert tool_response_to_str(tr) == "line 1\nline 2"

    def test_tool_response_to_str_empty_content(self) -> None:
        from agentscope.tool import ToolResponse  # type: ignore[import]

        from copaw.agents.langgraph_agent.tools_adapter import tool_response_to_str

        tr = ToolResponse(content=[])
        assert tool_response_to_str(tr) == "Done."

    def test_tool_response_to_str_plain_string(self) -> None:
        from copaw.agents.langgraph_agent.tools_adapter import tool_response_to_str

        assert tool_response_to_str("plain string") == "plain string"

    def test_tool_response_to_str_other_type(self) -> None:
        from copaw.agents.langgraph_agent.tools_adapter import tool_response_to_str

        assert tool_response_to_str(42) == "42"

    async def test_copaw_tool_to_langchain_returns_structured_tool(self) -> None:
        from langchain_core.tools import StructuredTool

        from copaw.agents.langgraph_agent.tools_adapter import copaw_tool_to_langchain

        async def _dummy_tool(x: str) -> str:
            """A dummy tool."""
            return x

        lc_tool = copaw_tool_to_langchain(_dummy_tool)
        assert isinstance(lc_tool, StructuredTool)
        assert lc_tool.name == "_dummy_tool"

    async def test_copaw_tool_to_langchain_converts_tool_response(self) -> None:
        from agentscope.message import TextBlock  # type: ignore[import]
        from agentscope.tool import ToolResponse  # type: ignore[import]

        from copaw.agents.langgraph_agent.tools_adapter import copaw_tool_to_langchain

        async def _responding_tool(value: str) -> ToolResponse:
            """Return value as ToolResponse."""
            return ToolResponse(content=[TextBlock(type="text", text=value)])

        lc_tool = copaw_tool_to_langchain(_responding_tool)
        result = await lc_tool.ainvoke({"value": "test output"})
        assert result == "test output"

    def test_adapt_tools_returns_list(self) -> None:
        from copaw.agents.langgraph_agent.tools_adapter import adapt_tools

        async def _t1(a: str) -> str:
            """Tool 1."""
            return a

        async def _t2(b: int) -> str:
            """Tool 2."""
            return str(b)

        tools = adapt_tools([_t1, _t2])
        assert len(tools) == 2
        assert all(hasattr(t, "name") for t in tools)

    def test_adapt_tools_skips_bad_functions(self) -> None:
        from copaw.agents.langgraph_agent.tools_adapter import adapt_tools

        class _BadCallable:
            pass

        # adapt_tools must not raise even if a callable fails to convert
        tools = adapt_tools([_BadCallable()])  # type: ignore[list-item]
        assert isinstance(tools, list)


# ---------------------------------------------------------------------------
# 3. graph.py – create_copaw_graph
# ---------------------------------------------------------------------------


class TestCreateCopawGraph:
    """Tests for the LangGraph graph builder."""

    def test_graph_compiles(self) -> None:
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        llm = _MockLLM(responses=["hi"])
        graph = create_copaw_graph(llm=llm, tools=[], system_prompt="")
        # A compiled graph should have an ainvoke method
        assert hasattr(graph, "ainvoke")

    def test_graph_compiles_with_tools(self) -> None:
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        llm = _MockLLM(responses=["hi"])
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            system_prompt="You are helpful.",
        )
        assert hasattr(graph, "ainvoke")

    def test_graph_compiles_with_checkpointer(self) -> None:
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        llm = _MockLLM(responses=["hi"])
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[],
            checkpointer=checkpointer,
        )
        assert hasattr(graph, "ainvoke")

    async def test_graph_simple_reply(self) -> None:
        """Graph returns the mock LLM's response for a plain user message."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        llm = _MockLLM(responses=["Simple answer."])
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[],
            system_prompt="You are helpful.",
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": "t1"}}
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Hello")],
                "session_id": "t1",
                "agent_id": "default",
            },
            config=config,
        )
        messages = state["messages"]
        ai_msgs = [m for m in messages if isinstance(m, AIMessage)]
        assert ai_msgs[-1].content == "Simple answer."

    async def test_graph_tool_call_flow(self) -> None:
        """Agent uses a tool and then provides a final answer."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        tool_call = {
            "id": "call_abc",
            "name": "_echo_tool",
            "args": {"text": "hello"},
        }
        llm = _make_tool_calling_llm([tool_call], final_response="Done echoing.")
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": "t2"}}
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Echo hello")],
                "session_id": "t2",
                "agent_id": "default",
            },
            config=config,
        )
        messages = state["messages"]
        # Should have: HumanMessage, AIMessage(tool_call), ToolMessage(result),
        # AIMessage(final)
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1
        assert "echo: hello" in tool_msgs[0].content

        ai_msgs = [m for m in messages if isinstance(m, AIMessage)]
        assert ai_msgs[-1].content == "Done echoing."

    async def test_graph_no_guard_when_engine_is_none(self) -> None:
        """Tool calls execute normally when tool_guard_engine is None."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        tool_call = {
            "id": "call_xyz",
            "name": "_echo_tool",
            "args": {"text": "world"},
        }
        llm = _make_tool_calling_llm([tool_call], "Reply after tool.")
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            tool_guard_engine=None,
        )
        config = {"configurable": {"thread_id": "t3"}}
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Do it")],
                "session_id": "t3",
                "agent_id": "default",
            },
            config=config,
        )
        tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1

    async def test_graph_tool_guard_auto_denies(self) -> None:
        """Tool guard auto-denies a permanently blocked tool."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        # Build a mock guard engine that always auto-denies
        mock_guard_engine = MagicMock()
        mock_guard_engine._enabled = True

        mock_finding = MagicMock()
        mock_finding.description = "Dangerous operation"
        mock_guard_result = MagicMock()
        mock_guard_result.findings = [mock_finding]
        mock_guard_result.max_severity = MagicMock(value="critical")

        mock_guard_engine.guard.return_value = mock_guard_result
        mock_guard_engine.is_denied.return_value = True

        tool_call = {
            "id": "call_deny",
            "name": "_echo_tool",
            "args": {"text": "bad"},
        }
        llm = _make_tool_calling_llm([tool_call], "Understood, tool was blocked.")
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            tool_guard_engine=mock_guard_engine,
        )
        config = {"configurable": {"thread_id": "t4"}}
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Do blocked thing")],
                "session_id": "t4",
                "agent_id": "default",
            },
            config=config,
        )
        tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
        assert any("blocked" in m.content.lower() for m in tool_msgs)

    async def test_graph_tool_guard_safe_passes_through(self) -> None:
        """Tool guard with no findings allows the tool to execute."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        mock_guard_engine = MagicMock()
        mock_guard_engine._enabled = True
        mock_guard_engine.guard.return_value = None  # No findings
        mock_guard_engine.is_denied.return_value = False

        tool_call = {
            "id": "call_safe",
            "name": "_echo_tool",
            "args": {"text": "safe"},
        }
        llm = _make_tool_calling_llm([tool_call], "Tool executed successfully.")
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            tool_guard_engine=mock_guard_engine,
        )
        config = {"configurable": {"thread_id": "t5"}}
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Do safe thing")],
                "session_id": "t5",
                "agent_id": "default",
            },
            config=config,
        )
        tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1
        assert "echo: safe" in tool_msgs[0].content

    async def test_graph_system_prompt_injected(self) -> None:
        """System prompt is injected into LLM calls."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        received_messages: list = []

        class _SpyLLM(BaseChatModel):
            @property
            def _llm_type(self) -> str:
                return "spy"

            def _generate(
                self, messages: list, stop=None, run_manager=None, **kwargs
            ) -> ChatResult:
                received_messages.extend(messages)
                return ChatResult(
                    generations=[
                        ChatGeneration(message=AIMessage(content="spy response"))
                    ]
                )

            def bind_tools(self, tools, **kwargs):
                return self

        graph = create_copaw_graph(
            llm=_SpyLLM(),
            tools=[],
            system_prompt="MY SYSTEM PROMPT",
        )
        config = {"configurable": {"thread_id": "t6"}}
        await graph.ainvoke(
            {
                "messages": [HumanMessage(content="ping")],
                "session_id": "t6",
                "agent_id": "default",
            },
            config=config,
        )
        from langchain_core.messages import SystemMessage

        sys_msgs = [m for m in received_messages if isinstance(m, SystemMessage)]
        assert any("MY SYSTEM PROMPT" in m.content for m in sys_msgs)

    async def test_graph_multi_turn_memory(self) -> None:
        """Checkpointer preserves conversation across multiple turns."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        llm = _MockLLM(responses=["Turn 1 answer.", "Turn 2 answer."])
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[],
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": "session-memory"}}

        # First turn
        state1 = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Question 1")],
                "session_id": "session-memory",
                "agent_id": "default",
            },
            config=config,
        )
        assert any(
            isinstance(m, AIMessage) and "Turn 1" in m.content
            for m in state1["messages"]
        )

        # Second turn – history should include first turn
        state2 = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Question 2")],
                "session_id": "session-memory",
                "agent_id": "default",
            },
            config=config,
        )
        # Accumulated messages include both turns
        assert len(state2["messages"]) > len(state1["messages"])

    async def test_graph_streaming(self) -> None:
        """astream yields state snapshots."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph

        llm = _MockLLM(responses=["Streaming answer."])
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[],
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": "stream-test"}}

        snapshots = []
        async for snapshot in graph.astream(
            {
                "messages": [HumanMessage(content="stream test")],
                "session_id": "stream-test",
                "agent_id": "default",
            },
            config=config,
            stream_mode="values",
        ):
            snapshots.append(snapshot)

        assert len(snapshots) > 0
        # Last snapshot should contain the final AIMessage
        last = snapshots[-1]
        ai_msgs = [m for m in last["messages"] if isinstance(m, AIMessage)]
        assert ai_msgs[-1].content == "Streaming answer."


# ---------------------------------------------------------------------------
# 4. CoPawLangGraphAgent
# ---------------------------------------------------------------------------


class TestCoPawLangGraphAgent:
    """Integration tests for the main agent class."""

    def _make_agent_config(self) -> Any:
        """Return a minimal AgentProfileConfig suitable for tests."""
        from copaw.config.config import AgentProfileConfig

        return AgentProfileConfig(
            id="test-agent",
            name="Test Agent",
            description="Agent for unit testing",
        )

    def test_agent_initialises_with_mock_llm(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["hi"]),
        )
        assert agent is not None
        assert hasattr(agent, "_graph")

    def test_agent_tools_property(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["hi"]),
        )
        assert isinstance(agent.tools, list)

    def test_agent_system_prompt_property(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["hi"]),
        )
        assert isinstance(agent.system_prompt, str)

    async def test_agent_reply_returns_string(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["Agent answer."]),
        )
        reply = await agent.reply("What is the capital of France?")
        assert isinstance(reply, str)
        assert len(reply) > 0

    async def test_agent_reply_content(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["Paris!"]),
        )
        reply = await agent.reply("Capital of France?")
        assert reply == "Paris!"

    async def test_agent_reply_with_session_id(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["Hello from session."]),
        )
        reply = await agent.reply("Hello", session_id="my-session")
        assert isinstance(reply, str)

    async def test_agent_astream_yields_snapshots(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["Streamed response."]),
        )
        snapshots = []
        async for snapshot in agent.astream("Stream me"):
            snapshots.append(snapshot)
        assert len(snapshots) > 0

    async def test_agent_multi_turn_conversation(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["First.", "Second."]),
        )
        r1 = await agent.reply("Turn 1", session_id="conv")
        r2 = await agent.reply("Turn 2", session_id="conv")
        assert r1 == "First."
        assert r2 == "Second."

    async def test_agent_request_context(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["ctx reply"]),
            request_context={"session_id": "ctx-session", "user_id": "u1"},
        )
        # session_id from request_context should be used as thread_id
        reply = await agent.reply("test")
        assert reply == "ctx reply"

    def test_agent_get_state_returns_none_or_snapshot(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["hi"]),
        )
        # Before any interaction, get_state should return an empty/None state
        state = agent.get_state("nonexistent-session")
        # Either None or a snapshot with empty messages
        if state is not None:
            msgs = state.values.get("messages", [])
            assert isinstance(msgs, list)

    def test_extract_last_ai_text_with_string(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        result = CoPawLangGraphAgent._extract_last_ai_text(
            [
                HumanMessage(content="hi"),
                AIMessage(content="hello"),
            ]
        )
        assert result == "hello"

    def test_extract_last_ai_text_with_list_content(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        ai_msg = AIMessage(
            content=[
                {"type": "text", "text": "Part 1"},
                {"type": "text", "text": "Part 2"},
            ]
        )
        result = CoPawLangGraphAgent._extract_last_ai_text([ai_msg])
        assert "Part 1" in result
        assert "Part 2" in result

    def test_extract_last_ai_text_empty_messages(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        result = CoPawLangGraphAgent._extract_last_ai_text([])
        assert result == ""

    def test_extract_last_ai_text_no_ai_message(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        result = CoPawLangGraphAgent._extract_last_ai_text(
            [HumanMessage(content="only human")]
        )
        assert result == ""


# ---------------------------------------------------------------------------
# 5. CoPawAgentState
# ---------------------------------------------------------------------------


class TestCoPawAgentState:
    """Tests for the agent state TypedDict."""

    def test_state_has_required_keys(self) -> None:
        from copaw.agents.langgraph_agent.state import CoPawAgentState

        state: CoPawAgentState = {
            "messages": [],
            "session_id": "s1",
            "agent_id": "a1",
        }
        assert state["messages"] == []
        assert state["session_id"] == "s1"
        assert state["agent_id"] == "a1"

    def test_state_optional_fields(self) -> None:
        from copaw.agents.langgraph_agent.state import CoPawAgentState

        state: CoPawAgentState = {
            "messages": [HumanMessage(content="hi")],
            "session_id": None,
            "agent_id": None,
        }
        assert state["session_id"] is None
        assert state["agent_id"] is None


# ---------------------------------------------------------------------------
# 6. LangGraphAgentRunner
# ---------------------------------------------------------------------------


class TestLangGraphAgentRunner:
    """Tests for the LangGraph agent runner."""

    def test_runner_initialises(self) -> None:
        from copaw.agents.langgraph_agent.runner import LangGraphAgentRunner

        runner = LangGraphAgentRunner(agent_id="default")
        assert runner.agent_id == "default"
        assert runner._agent is None  # Lazy init

    def test_runner_with_custom_workspace(self, tmp_path: Any) -> None:
        from copaw.agents.langgraph_agent.runner import LangGraphAgentRunner

        runner = LangGraphAgentRunner(
            agent_id="default",
            workspace_dir=tmp_path,
        )
        assert runner.workspace_dir == tmp_path

    async def test_runner_query_handler_yields_text(self) -> None:
        """query_handler yields the agent's text response."""
        from copaw.agents.langgraph_agent.runner import LangGraphAgentRunner
        from copaw.config.config import AgentProfileConfig
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        runner = LangGraphAgentRunner(agent_id="default")

        # Inject a pre-built agent so we don't touch the filesystem
        cfg = AgentProfileConfig(id="default", name="Test", description="")
        mock_agent = CoPawLangGraphAgent(
            agent_config=cfg,
            llm=_MockLLM(responses=["runner reply"]),
        )
        runner._agent = mock_agent

        responses = []
        async for chunk in runner.query_handler("Hello", session_id="r1"):
            responses.append(chunk)

        assert len(responses) > 0
        assert any("runner reply" in r for r in responses)

    def test_is_approval_helper(self) -> None:
        from copaw.agents.langgraph_agent.runner import _is_approval

        assert _is_approval("approve") is True
        assert _is_approval("APPROVE") is True
        assert _is_approval("/approve") is True
        assert _is_approval("/daemon approve") is True
        assert _is_approval("yes") is False
        assert _is_approval("deny") is False
        assert _is_approval("") is False
        assert _is_approval("  approve  ") is True  # stripped whitespace

# ---------------------------------------------------------------------------
# 7. llm_factory.py
# ---------------------------------------------------------------------------


class TestLlmFactory:
    """Tests for the LangChain LLM factory."""

    def test_create_openai_llm(self) -> None:
        from copaw.agents.langgraph_agent.llm_factory import _create_openai

        llm = _create_openai(
            model="gpt-4o",
            api_key="sk-test",
            base_url=None,
            temperature=0.0,
            max_tokens=None,
        )
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)

    def test_create_openai_llm_with_base_url(self) -> None:
        from copaw.agents.langgraph_agent.llm_factory import _create_openai

        llm = _create_openai(
            model="gpt-4o",
            api_key="sk-test",
            base_url="https://custom.endpoint/v1",
            temperature=0.7,
            max_tokens=512,
        )
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)

    def test_create_langchain_llm_no_active_model_raises(self) -> None:
        """Raises ValueError when no active model is configured."""
        from copaw.config.config import AgentProfileConfig
        from copaw.agents.langgraph_agent.llm_factory import create_langchain_llm

        cfg = AgentProfileConfig(id="no-model-agent", name="No Model")
        # No active_model configured → should raise

        with patch(
            "copaw.agents.langgraph_agent.llm_factory.load_agent_config",
            return_value=cfg,
        ):
            with pytest.raises(ValueError, match="No active model"):
                create_langchain_llm("no-model-agent")

    def test_create_langchain_llm_unknown_provider_raises(self) -> None:
        """Raises ValueError when the provider is not found in ProviderManager."""
        from copaw.config.config import AgentProfileConfig
        from copaw.providers.models import ModelSlotConfig
        from copaw.agents.langgraph_agent.llm_factory import create_langchain_llm

        cfg = AgentProfileConfig(
            id="agent-x",
            name="X",
            active_model=ModelSlotConfig(provider_id="ghost-provider", model="m1"),
        )

        mock_manager = MagicMock()
        mock_manager.get_provider.return_value = None  # Provider not found

        with patch(
            "copaw.agents.langgraph_agent.llm_factory.load_agent_config",
            return_value=cfg,
        ), patch(
            "copaw.agents.langgraph_agent.llm_factory.ProviderManager",
            return_value=mock_manager,
        ):
            with pytest.raises(ValueError, match="Provider 'ghost-provider' not found"):
                create_langchain_llm("agent-x")

    def test_create_langchain_llm_openai_provider(self) -> None:
        """Creates a ChatOpenAI model for an OpenAI provider."""
        from copaw.config.config import AgentProfileConfig
        from copaw.providers.models import ModelSlotConfig
        from copaw.agents.langgraph_agent.llm_factory import create_langchain_llm
        from langchain_openai import ChatOpenAI

        cfg = AgentProfileConfig(
            id="agent-openai",
            name="OpenAI Agent",
            active_model=ModelSlotConfig(
                provider_id="openai", model="gpt-4o-mini"
            ),
        )

        mock_provider = MagicMock()
        mock_provider.chat_model = "OpenAIChatModel"
        mock_provider.api_key = "sk-test"
        mock_provider.base_url = ""

        mock_manager = MagicMock()
        mock_manager.get_provider.return_value = mock_provider

        with patch(
            "copaw.agents.langgraph_agent.llm_factory.load_agent_config",
            return_value=cfg,
        ), patch(
            "copaw.agents.langgraph_agent.llm_factory.ProviderManager",
            return_value=mock_manager,
        ):
            llm = create_langchain_llm("agent-openai")

        assert isinstance(llm, ChatOpenAI)


# ---------------------------------------------------------------------------
# 8. End-to-end agent flow
# ---------------------------------------------------------------------------


class TestEndToEndFlow:
    """End-to-end tests exercising the full agent→graph→tools pipeline."""

    def _make_agent_config(self, agent_id: str = "test") -> Any:
        from copaw.config.config import AgentProfileConfig

        return AgentProfileConfig(
            id=agent_id,
            name="E2E Test Agent",
            description="",
        )

    async def test_agent_no_tools_single_turn(self) -> None:
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent

        agent = CoPawLangGraphAgent(
            agent_config=self._make_agent_config(),
            llm=_MockLLM(responses=["Hi there!"]),
        )
        reply = await agent.reply("Greet me")
        assert reply == "Hi there!"

    async def test_agent_with_tools_executes_tool(self) -> None:
        """Agent makes a real tool call and incorporates the result."""
        from copaw.agents.langgraph_agent.agent import CoPawLangGraphAgent
        from copaw.agents.langgraph_agent.graph import create_copaw_graph
        from langgraph.checkpoint.memory import MemorySaver

        tool_call = {
            "id": "c1",
            "name": "_echo_tool",
            "args": {"text": "ping"},
        }
        llm = _make_tool_calling_llm([tool_call], "Tool said: echo: ping")

        # Build agent manually with the echo tool
        cfg = self._make_agent_config("e2e-tools")
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            checkpointer=checkpointer,
        )

        agent = CoPawLangGraphAgent.__new__(CoPawLangGraphAgent)
        agent._agent_config = cfg
        agent._tools = [_echo_tool]
        agent._system_prompt = ""
        agent._llm = llm
        agent._checkpointer = checkpointer
        agent._tool_guard_engine = None
        agent._request_context = {}
        agent._graph = graph

        reply = await agent.reply("Call the echo tool", session_id="e2e-1")
        assert isinstance(reply, str)
        assert len(reply) > 0

    async def test_agent_guard_disabled_when_no_engine(self) -> None:
        """Setting tool_guard_engine=None skips guarding entirely."""
        from copaw.agents.langgraph_agent.graph import create_copaw_graph
        from langgraph.checkpoint.memory import MemorySaver

        tool_call = {
            "id": "c2",
            "name": "_echo_tool",
            "args": {"text": "allowed"},
        }
        llm = _make_tool_calling_llm([tool_call], "Guard skipped.")
        checkpointer = MemorySaver()
        graph = create_copaw_graph(
            llm=llm,
            tools=[_echo_tool],
            tool_guard_engine=None,
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": "e2e-2"}}
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="Go")],
                "session_id": "e2e-2",
                "agent_id": "test",
            },
            config=config,
        )
        tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1
        assert "echo: allowed" in tool_msgs[0].content

    async def test_runner_approval_tracking(self) -> None:
        """Runner correctly tracks pending approval sessions."""
        from copaw.agents.langgraph_agent.runner import LangGraphAgentRunner, _is_approval

        runner = LangGraphAgentRunner(agent_id="default")

        # Simulate a pending approval
        runner._pending_approvals["sess-1"] = True
        assert "sess-1" in runner._pending_approvals

        # A normal query does not affect other sessions
        assert "sess-2" not in runner._pending_approvals

        # is_approval correctly classifies messages
        assert _is_approval("approve")
        assert not _is_approval("yes please")
