"""
LLM Factory - Single Source of Truth for all LLM instantiation.

This module has NO dependencies on other project modules to avoid circular imports.
All code requiring an LLM should import from here.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Default model to use across all services
DEFAULT_MODEL = "gemini-3-pro-preview"


def get_llm(model: str = DEFAULT_MODEL, temperature: float = 0.7, api_key: Optional[str] = None):
    """
    Get an LLM instance based on model name - SINGLE SOURCE OF TRUTH for all LLM instantiation.

    Automatically detects the provider based on model name and returns the appropriate
    LLM class from browser-use.

    Args:
        model: Model name (e.g., "gemini-3-pro-preview", "gpt-4o", "claude-3-opus")
        temperature: Creativity/randomness of responses (0.0-1.0)
        api_key: Optional API key (falls back to environment variables)

    Returns:
        LLM instance (ChatGoogle, ChatOpenAI, or ChatAnthropic)

    Supported models:
        - Gemini/Gemma: Uses GEMINI_API_KEY or GOOGLE_API_KEY
        - GPT: Uses OPENAI_API_KEY
        - Claude: Uses ANTHROPIC_API_KEY
    """
    model_lower = model.lower()

    if 'gemini' in model_lower or 'gemma' in model_lower:
        from browser_use import ChatGoogle
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
        return ChatGoogle(model=model, temperature=temperature, api_key=key)

    elif 'gpt' in model_lower or 'openai' in model_lower:
        from browser_use.llm.openai.chat import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)

    elif 'claude' in model_lower or 'anthropic' in model_lower:
        from browser_use.llm.anthropic.chat import ChatAnthropic
        return ChatAnthropic(model=model, temperature=temperature)

    else:
        # Default to Gemini
        from browser_use import ChatGoogle
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
        return ChatGoogle(model=model, temperature=temperature, api_key=key)


def get_gemini_llm(model: str = DEFAULT_MODEL, temperature: float = 0.7):
    """
    DEPRECATED: Use get_llm() instead.

    This function is kept for backwards compatibility.
    """
    return get_llm(model=model, temperature=temperature)
