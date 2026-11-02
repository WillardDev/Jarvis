"""Deepgram streaming speech-to-text provider."""

from __future__ import annotations

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.deepgram.stt import DeepgramSTTService

from app.config import Settings
from app.providers.base import STTProvider


class DeepgramSTTProvider(STTProvider):
    """Streams microphone audio to Deepgram and returns interim + final transcripts.

    Endpointing is disabled on purpose: the turn boundary comes from the
    client (push-to-talk) or from VAD, and letting Deepgram cut the stream on
    its own would split a sentence in half.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.deepgram_api_key:
            raise ValueError("DEEPGRAM_API_KEY is required for the deepgram STT provider")
        self._settings = settings

    def build(self) -> FrameProcessor:
        return DeepgramSTTService(
            api_key=self._settings.deepgram_api_key,
            sample_rate=self._settings.stt_sample_rate,
            settings=DeepgramSTTService.Settings(
                model=self._settings.stt_model,
                language=self._settings.stt_language,
                interim_results=True,
                endpointing=False,
                utterance_end_ms=None,
                punctuate=True,
                smart_format=True,
            ),
        )
