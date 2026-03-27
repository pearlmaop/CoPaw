# -*- coding: utf-8 -*-
"""Factory for creating LangChain chat models from CoPaw provider configuration.

CoPaw stores provider/model settings in ``config.json`` under each agent's
workspace (or the global config).  This module reads that configuration and
returns the appropriate :class:`langchain_core.language_models.BaseChatModel`
so that the LangGraph agent can call any provider CoPaw supports.

Supported mappings:

* ``OpenAIChatModel``   → :class:`langchain_openai.ChatOpenAI`
* ``AnthropicChatModel``→ :class:`langchain_anthropic.ChatAnthropic`
  (requires optional ``langchain-anthropic`` package)
* ``GeminiChatModel``  → :class:`langchain_google_genai.ChatGoogleGenerativeAI`
  (requires optional ``langchain-google-genai`` package)
* All other types      → ``ChatOpenAI`` treating the endpoint as
  OpenAI-compatible (Ollama, LiteLLM, etc.)
"""
from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

# Module-level imports so tests can patch them via
# ``patch("copaw.agents.langgraph_agent.llm_factory.load_agent_config", ...)``.
from copaw.config.config import load_agent_config
from copaw.providers.provider_manager import ProviderManager

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def create_langchain_llm(
    agent_id: str = "default",
    max_tokens: Optional[int] = None,
    temperature: float = 0.0,
) -> "BaseChatModel":
    """Create a LangChain ``BaseChatModel`` from CoPaw's provider config.

    Reads the active provider and model from the agent's configuration file
    (``config.json``) and instantiates the corresponding LangChain model.

    Args:
        agent_id: CoPaw agent identifier used to load ``AgentProfileConfig``.
        max_tokens: Optional maximum token limit for completions.
        temperature: Sampling temperature (default ``0.0`` for determinism).

    Returns:
        A ready-to-use :class:`~langchain_core.language_models.BaseChatModel`.

    Raises:
        ValueError: If no active model is configured or the provider is not found.
        ImportError: If the required LangChain provider package is not installed.
    """
    agent_config = load_agent_config(agent_id)
    active_model = agent_config.active_model

    if active_model is None:
        raise ValueError(
            f"No active model configured for agent '{agent_id}'. "
            "Set an active model in the agent configuration."
        )

    manager = ProviderManager()
    provider = manager.get_provider(active_model.provider_id)

    if provider is None:
        raise ValueError(
            f"Provider '{active_model.provider_id}' not found. "
            "Check the provider configuration."
        )

    model_id: str = active_model.model
    chat_model_type: str = provider.chat_model

    logger.info(
        "Creating LangChain LLM: provider=%s model=%s type=%s",
        active_model.provider_id,
        model_id,
        chat_model_type,
    )

    if chat_model_type == "AnthropicChatModel":
        return _create_anthropic(model_id, provider.api_key, temperature, max_tokens)

    if chat_model_type == "GeminiChatModel":
        return _create_gemini(
            model_id, provider.api_key, provider.base_url, temperature, max_tokens
        )

    # OpenAIChatModel or any unknown type → ChatOpenAI
    return _create_openai(
        model_id, provider.api_key, provider.base_url, temperature, max_tokens
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _create_openai(
    model: str,
    api_key: Optional[str],
    base_url: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> "BaseChatModel":
    from langchain_openai import ChatOpenAI

    kwargs: dict = {
        "model": model,
        "api_key": api_key or "dummy",
        "temperature": temperature,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)


def _create_anthropic(
    model: str,
    api_key: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> "BaseChatModel":
    try:
        from langchain_anthropic import ChatAnthropic  # type: ignore[import]

        kwargs: dict = {
            "model": model,
            "api_key": api_key or "dummy",
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        return ChatAnthropic(**kwargs)
    except ImportError:
        logger.warning(
            "langchain-anthropic is not installed. "
            "Falling back to ChatOpenAI for Anthropic provider. "
            "Install with: pip install langchain-anthropic"
        )
        return _create_openai(
            model,
            api_key,
            "https://api.anthropic.com/v1",
            temperature,
            max_tokens,
        )


def _create_gemini(
    model: str,
    api_key: Optional[str],
    base_url: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> "BaseChatModel":
    try:
        from langchain_google_genai import (  # type: ignore[import]
            ChatGoogleGenerativeAI,
        )

        kwargs: dict = {
            "model": model,
            "google_api_key": api_key or "dummy",
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_output_tokens"] = max_tokens
        return ChatGoogleGenerativeAI(**kwargs)
    except ImportError:
        logger.warning(
            "langchain-google-genai is not installed. "
            "Falling back to ChatOpenAI for Gemini provider (OpenAI-compatible endpoint). "
            "Install with: pip install langchain-google-genai"
        )
        openai_base = (
            base_url
            or "https://generativelanguage.googleapis.com/v1beta/openai"
        )
        return _create_openai(model, api_key, openai_base, temperature, max_tokens)
