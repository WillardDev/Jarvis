"""Anthropic Claude language-model provider."""

from __future__ import annotations

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.anthropic.llm import AnthropicLLMService

from app.config import Settings
from app.providers.base import LLMProvider


class AnthropicLLMProvider(LLMProvider):
    """Streams Claude replies token by token.

    The model id comes from ``LLM_MODEL`` so a fast model and a strong model
    are a one-line change. ``effort`` is kept low because every millisecond of
    thinking is a millisecond the user is left waiting.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the anthropic LLM provider")
        self._settings = settings

    def build(self) -> FrameProcessor:
        return AnthropicLLMService(
            api_key=self._settings.anthropic_api_key,
            settings=AnthropicLLMService.Settings(
                model=self._settings.llm_model,
                system_instruction=self._settings.system_prompt,
                max_tokens=self._settings.llm_max_tokens,
                effort=self._settings.llm_effort or None,
            ),
        )
