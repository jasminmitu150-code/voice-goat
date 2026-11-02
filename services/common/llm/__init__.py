"""
LLM client utilities - Multi-provider support.

Supported providers:
- mock: Simulated responses (free, no API calls)
- openai: OpenAI API (GPT-4, GPT-4o-mini)
- bedrock: AWS Bedrock (Claude, Titan)

Planned:
- ollama: Local models via Ollama
"""

from services.common.llm.bedrock import BedrockClient
from services.common.llm.openai_client import OpenAIClient
from services.common.llm.provider import (
    get_llm_client,
    invoke_llm,
    MockLLMClient,
    LLMClient,
    clear_client_cache,
)
from services.common.llm.prompts import SystemPrompt, build_prompt

__all__ = [
    # Providers
    "get_llm_client",
    "invoke_llm",
    "LLMClient",
    "MockLLMClient",
    "clear_client_cache",
    # Legacy clients (direct access)
    "BedrockClient",
    "OpenAIClient",
    # Prompts
    "SystemPrompt",
    "build_prompt",
]
