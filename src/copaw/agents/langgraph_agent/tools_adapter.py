# -*- coding: utf-8 -*-
"""Adapter utilities to convert CoPaw tool functions to LangChain tools.

CoPaw tools are async Python functions that return :class:`ToolResponse`
objects (from agentscope).  LangChain/LangGraph expects tool callables that
return plain strings.  This module bridges the gap without modifying the
original tool implementations.
"""
from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, List

from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


def tool_response_to_str(result: Any) -> str:
    """Convert a CoPaw ``ToolResponse`` (or any value) to a plain string.

    Extracts ``text`` from each block in ``ToolResponse.content``.
    Blocks may be plain dicts (``{"type": "text", "text": "..."}``), or objects
    with a ``text`` attribute.  Falls back to ``str(result)`` for unknown types.
    """
    try:
        from agentscope.tool import ToolResponse  # type: ignore[import]

        if isinstance(result, ToolResponse):
            parts: list[str] = []
            for block in result.content:
                if isinstance(block, dict):
                    text = block.get("text")
                    url = block.get("url")
                    if text:
                        parts.append(str(text))
                    elif url:
                        parts.append(f"[image: {url}]")
                elif hasattr(block, "text"):
                    parts.append(block.text)
                elif hasattr(block, "url"):
                    parts.append(f"[image: {block.url}]")
            return "\n".join(parts) if parts else "Done."
    except ImportError:
        pass
    return str(result)


def copaw_tool_to_langchain(fn: Callable) -> StructuredTool:
    """Convert a single CoPaw async tool function to a LangChain ``StructuredTool``.

    Builds an explicit Pydantic ``args_schema`` from the original function's
    type annotations so that LangGraph's ``ToolNode`` can correctly parse and
    validate tool arguments.

    Args:
        fn: An async CoPaw tool function that returns ``ToolResponse``.

    Returns:
        A ``StructuredTool`` usable by LangGraph's ``ToolNode``.

    Raises:
        Exception: If the args schema cannot be derived from the signature.
    """
    import typing
    from pydantic import create_model
    from pydantic.fields import FieldInfo

    sig = inspect.signature(fn)
    doc = inspect.getdoc(fn) or fn.__name__
    name = fn.__name__

    # Build a Pydantic model for the tool arguments
    try:
        type_hints = typing.get_type_hints(fn)
    except Exception:
        type_hints = {}

    fields: dict[str, Any] = {}
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        annotation = type_hints.get(param_name, Any)
        if param.default is inspect.Parameter.empty:
            fields[param_name] = (annotation, FieldInfo(description=""))
        else:
            fields[param_name] = (annotation, param.default)

    args_schema = create_model(f"{name}_schema", **fields)

    async def _wrapper(**kwargs: Any) -> str:
        result = await fn(**kwargs)
        return tool_response_to_str(result)

    return StructuredTool(
        name=name,
        description=doc,
        coroutine=_wrapper,
        args_schema=args_schema,
    )


def adapt_tools(tool_functions: List[Callable]) -> List[StructuredTool]:
    """Convert a list of CoPaw tool functions to LangChain ``StructuredTool`` objects.

    Skips any function that fails to convert, logging a warning.

    Args:
        tool_functions: List of async CoPaw tool functions.

    Returns:
        List of ``StructuredTool`` instances ready for use in LangGraph.
    """
    tools: list[StructuredTool] = []
    for fn in tool_functions:
        try:
            tools.append(copaw_tool_to_langchain(fn))
        except Exception as exc:
            logger.warning(
                "Failed to adapt tool '%s': %s",
                getattr(fn, "__name__", str(fn)),
                exc,
            )
    return tools
