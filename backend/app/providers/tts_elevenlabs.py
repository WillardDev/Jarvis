"""ElevenLabs streaming text-to-speech provider."""

from __future__ import annotations

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.tts_service import TextAggregationMode

from app.config import Settings
from app.providers.base import TTSProvider


class ElevenLabsTTSProvider(TTSProvider):
    """Synthesises speech over ElevenLabs' WebSocket API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY is required for the elevenlabs TTS provider")
        self._settings = settings

    def build(self) -> FrameProcessor:
        return ElevenLabsTTSService(
            api_key=self._settings.elevenlabs_api_key,
            voice_id=self._settings.tts_voice_id or self._settings.elevenlabs_voice_id,
            model=self._settings.tts_model or self._settings.elevenlabs_model,
            sample_rate=self._settings.tts_sample_rate,
            text_aggregation_mode=TextAggregationMode(self._settings.tts_aggregation_mode),
        )
