"""Cartesia streaming text-to-speech provider."""

from __future__ import annotations

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.tts_service import TextAggregationMode

from app.config import Settings
from app.providers.base import TTSProvider


class CartesiaTTSProvider(TTSProvider):
    """Synthesises speech over Cartesia's WebSocket API.

    Audio starts flowing on the first complete sentence, so the reply is
    audible long before the model has finished writing it.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.cartesia_api_key:
            raise ValueError("CARTESIA_API_KEY is required for the cartesia TTS provider")
        self._settings = settings

    def build(self) -> FrameProcessor:
        return CartesiaTTSService(
            api_key=self._settings.cartesia_api_key,
            sample_rate=self._settings.tts_sample_rate,
            text_aggregation_mode=TextAggregationMode(self._settings.tts_aggregation_mode),
            settings=CartesiaTTSService.Settings(
                model=self._settings.tts_model or self._settings.cartesia_model,
                voice=self._settings.tts_voice_id or self._settings.cartesia_voice_id,
            ),
        )
