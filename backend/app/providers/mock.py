"""Offline provider set used to exercise the voice loop without API keys.

These are not toys: they emit the same frame types as the real services, so
the pipeline, the turn handling, the latency instrumentation and the browser
can all be tested before a single vendor key exists. Select them with
``STT_PROVIDER=mock LLM_PROVIDER=mock TTS_PROVIDER=mock``.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    InterimTranscriptionFrame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.settings import TTSSettings
from pipecat.services.tts_service import TextAggregationMode, TTSService
from pipecat.transcriptions.language import Language
from pipecat.utils.time import time_now_iso8601

from app.config import Settings
from app.providers.base import LLMProvider, STTProvider, TTSProvider

_MOCK_PHRASE = "what is the weather like today"
_MOCK_REPLY = (
    "It is a clear evening, about eighteen degrees. "
    "A light wind from the west, and no rain until tomorrow."
)


class MockSTTProvider(STTProvider):
    """Builds a mock speech-to-text service."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build(self) -> FrameProcessor:
        return MockSTTService(sample_rate=self._settings.stt_sample_rate)


class MockLLMProvider(LLMProvider):
    """Builds a mock language-model service."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build(self) -> FrameProcessor:
        return MockLLMService()


class MockTTSProvider(TTSProvider):
    """Builds a mock text-to-speech service."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build(self) -> FrameProcessor:
        return MockTTSService(sample_rate=self._settings.tts_sample_rate)


class MockSTTService(FrameProcessor):
    """Emits a canned transcript, first as interims then as a final."""

    def __init__(self, *, sample_rate: int, phrase: str = _MOCK_PHRASE) -> None:
        super().__init__()
        self._sample_rate = sample_rate
        self._phrase = phrase
        self._words = phrase.split()
        self._heard_bytes = 0
        self._emitted_words = 0
        self._chunk_bytes = sample_rate * 2 // 4  # ~250 ms of 16-bit audio

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, InputAudioRawFrame):
            self._heard_bytes += len(frame.audio)
            while self._heard_bytes >= self._chunk_bytes and self._emitted_words < len(self._words):
                self._heard_bytes -= self._chunk_bytes
                self._emitted_words += 1
                await self.push_frame(
                    InterimTranscriptionFrame(
                        " ".join(self._words[: self._emitted_words]),
                        "mock-user",
                        time_now_iso8601(),
                    )
                )
        elif isinstance(frame, VADUserStoppedSpeakingFrame):
            await self.push_frame(
                TranscriptionFrame(
                    self._phrase,
                    "mock-user",
                    time_now_iso8601(),
                    finalized=True,
                )
            )
            self._heard_bytes = 0
            self._emitted_words = 0

        await self.push_frame(frame, direction)


class MockLLMService(FrameProcessor):
    """Streams a canned reply one word at a time."""

    def __init__(self, reply: str = _MOCK_REPLY) -> None:
        super().__init__()
        self._reply = reply

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        # The context aggregator asks for inference by pushing a context
        # frame, which is what the real LLM services react to.
        if isinstance(frame, LLMContextFrame):
            self.create_task(self._stream_reply(), "stream_reply")

        await self.push_frame(frame, direction)

    async def _stream_reply(self) -> None:
        await self.push_frame(LLMFullResponseStartFrame())
        for word in self._reply.split(" "):
            await asyncio.sleep(0.03)
            await self.push_frame(LLMTextFrame(word + " "))
        await self.push_frame(LLMFullResponseEndFrame())


@dataclass
class MockTTSSettings(TTSSettings):
    """Settings for the mock TTS service, which has no model or voice."""

    model: str | None = None
    voice: str | None = None
    language: Language | str | None = None


class MockTTSService(TTSService):
    """Speaks with a quiet sine tone, so playback is audible without a vendor.

    It extends Pipecat's own TTS service rather than rolling its own frame
    handling, so sentence aggregation and barge-in behave exactly as they do
    with the real providers.
    """

    Settings = MockTTSSettings
    _settings: Settings

    def __init__(self, *, sample_rate: int) -> None:
        super().__init__(
            sample_rate=sample_rate,
            push_start_frame=True,
            push_stop_frames=True,
            text_aggregation_mode=TextAggregationMode.SENTENCE,
            settings=self.Settings(),
        )
        self._phase = 0.0

    async def run_tts(
        self, text: str, context_id: str
    ) -> AsyncGenerator[Frame | None, None]:
        """Yield a tone whose length stands in for the length of the speech."""
        seconds = min(2.0, 0.25 + 0.05 * len(text))
        total = int(self.sample_rate * seconds)
        chunk = self.sample_rate // 20  # 50 ms per chunk
        written = 0
        while written < total:
            count = min(chunk, total - written)
            yield TTSAudioRawFrame(
                self._tone(count), sample_rate=self.sample_rate, num_channels=1
            )
            written += count
            await asyncio.sleep(0.02)

    def _tone(self, count: int) -> bytes:
        step = 2.0 * math.pi * 220.0 / self.sample_rate
        samples = bytearray()
        for _ in range(count):
            value = int(12000 * math.sin(self._phase))
            self._phase += step
            samples += value.to_bytes(2, byteorder="little", signed=True)
        return bytes(samples)
