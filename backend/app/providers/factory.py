"""Provider factory: turns environment configuration into Pipecat services."""

from __future__ import annotations

from typing import TypeVar

from pipecat.processors.frame_processor import FrameProcessor

from app.config import Settings
from app.providers.base import LLMProvider, STTProvider, TTSProvider
from app.providers.llm_anthropic import AnthropicLLMProvider
from app.providers.mock import MockLLMProvider, MockSTTProvider, MockTTSProvider
from app.providers.stt_deepgram import DeepgramSTTProvider
from app.providers.tts_cartesia import CartesiaTTSProvider
from app.providers.tts_elevenlabs import ElevenLabsTTSProvider

ProviderT = TypeVar("ProviderT", STTProvider, LLMProvider, TTSProvider)

_STT_PROVIDERS: dict[str, type[STTProvider]] = {
    "deepgram": DeepgramSTTProvider,
    "mock": MockSTTProvider,
}

_LLM_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicLLMProvider,
    "mock": MockLLMProvider,
}

_TTS_PROVIDERS: dict[str, type[TTSProvider]] = {
    "cartesia": CartesiaTTSProvider,
    "elevenlabs": ElevenLabsTTSProvider,
    "mock": MockTTSProvider,
}


def build_stt(settings: Settings) -> FrameProcessor:
    """Build the speech-to-text service named by ``STT_PROVIDER``."""
    return _resolve(_STT_PROVIDERS, settings.stt_provider, "STT_PROVIDER")(settings).build()


def build_llm(settings: Settings) -> FrameProcessor:
    """Build the language-model service named by ``LLM_PROVIDER``."""
    return _resolve(_LLM_PROVIDERS, settings.llm_provider, "LLM_PROVIDER")(settings).build()


def build_tts(settings: Settings) -> FrameProcessor:
    """Build the text-to-speech service named by ``TTS_PROVIDER``."""
    return _resolve(_TTS_PROVIDERS, settings.tts_provider, "TTS_PROVIDER")(settings).build()


def _resolve(registry: dict[str, type[ProviderT]], name: str, env_var: str) -> type[ProviderT]:
    key = name.strip().lower()
    if key not in registry:
        available = ", ".join(sorted(registry))
        raise ValueError(f"Unknown provider '{name}' for {env_var}. Available: {available}")
    return registry[key]
