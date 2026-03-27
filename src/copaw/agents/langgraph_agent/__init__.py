# -*- coding: utf-8 -*-
"""CoPaw LangGraph agent package.

This package provides a LangGraph-based implementation of the CoPaw agent
that replaces the AgentScope ReActAgent backend.

Exports
-------
:class:`CoPawLangGraphAgent`
    Main agent class with ``reply`` / ``astream`` / ``approve_tool_call``
    methods.
:class:`LangGraphAgentRunner`
    Higher-level runner that drives the agent from incoming user queries,
    including ToolGuard approval flow.
:func:`create_copaw_graph`
    Low-level graph factory for constructing and compiling the LangGraph
    ReAct graph.
:func:`create_langchain_llm`
    Factory that creates a ``BaseChatModel`` from CoPaw's provider config.
:func:`adapt_tools`
    Converts CoPaw ``ToolResponse``-returning async functions to LangChain
    ``StructuredTool`` objects.
"""

from .agent import CoPawLangGraphAgent
from .runner import LangGraphAgentRunner
from .graph import create_copaw_graph
from .llm_factory import create_langchain_llm
from .tools_adapter import adapt_tools, copaw_tool_to_langchain, tool_response_to_str
from .state import CoPawAgentState

__all__ = [
    "CoPawLangGraphAgent",
    "LangGraphAgentRunner",
    "create_copaw_graph",
    "create_langchain_llm",
    "adapt_tools",
    "copaw_tool_to_langchain",
    "tool_response_to_str",
    "CoPawAgentState",
]
