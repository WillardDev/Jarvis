"""Conversion between the browser wire format and Pipecat frames."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from pipecat.clocks.base_clock import BaseClock
from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    InterruptionFrame,
    OutputAudioRawFrame,
    ProposedUserStartedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameProcessorSetup
from pipecat.serializers.base_serializer import FrameSerializer

from app.api.protocol import ClientMessage, ServerEvent
from app.pipeline.frames import JarvisTurnEndFrame

# Called with the pipeline clock reading of the first audio byte handed to the
# transport, so the debug panel can separate "TTS was slow" from "the transport
# was slow".
AudioSentCallback = Callable[[int], Awaitable[None]]


class JarvisSerializer(FrameSerializer):
    """Reads browser messages and writes browser messages.

    Audio crosses the wire as raw PCM16 in binary frames. Everything else is
    JSON in text frames.
    """

    def __init__(
        self,
        *,
        input_sample_rate: int,
        output_sample_rate: int,
        on_audio_sent: AudioSentCallback | None = None,
    ) -> None:
        super().__init__()
        self._input_sample_rate = input_sample_rate
        self._output_sample_rate = output_sample_rate
        self._on_audio_sent = on_audio_sent
        self._clock: BaseClock | None = None

    @property
    def output_sample_rate(self) -> int:
        """Sample rate of the audio this serializer writes."""
        return self._output_sample_rate

    async def setup(self, setup: FrameProcessorSetup) -> None:
        """Remember the clock, so audio marks line up with the observer's."""
        await super().setup(setup)
        self._clock = setup.clock

    async def serialize(self, frame: Frame) -> str | bytes | None:
        """Turn an outgoing frame into a wire message."""
        if isinstance(frame, OutputAudioRawFrame):
            if self._on_audio_sent is not None and self._clock is not None:
                await self._on_audio_sent(self._clock.get_time())
            return frame.audio
        if isinstance(frame, InterruptionFrame):
            # The browser uses this to stop playback immediately.
            return json.dumps({"type": ServerEvent.INTERRUPTED.value})
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        """Turn a wire message into a frame the pipeline can act on."""
        if isinstance(data, (bytes, bytearray, memoryview)):
            return InputAudioRawFrame(
                audio=bytes(data),
                sample_rate=self._input_sample_rate,
                num_channels=1,
            )

        message = _parse_json(data)
        if message is None:
            return None

        kind = message.get("type")
        if kind == ClientMessage.RECORD_START.value:
            return ProposedUserStartedSpeakingFrame()
        if kind == ClientMessage.RECORD_STOP.value:
            return JarvisTurnEndFrame()
        if kind == ClientMessage.INTERRUPT.value:
            return InterruptionFrame()
        return None


def _parse_json(data: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(data)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None
