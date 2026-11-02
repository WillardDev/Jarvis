"""Turn control: turning browser signals into pipeline frames."""

from __future__ import annotations

from pipecat.frames.frames import (
    Frame,
    ProposedUserStoppedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from app.pipeline.frames import JarvisTurnEndFrame


class TurnControlProcessor(FrameProcessor):
    """Expands the browser's turn-end signal into the frames the pipeline needs.

    It sits between the input transport and the speech-to-text service so the
    VAD frame it emits still reaches the STT service, which is what asks
    Deepgram to finalise the transcript.
    """

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, JarvisTurnEndFrame):
            # The VAD frame makes the STT service finalise; the proposal makes
            # the turn strategy close the user turn once that transcript lands.
            await self.push_frame(VADUserStoppedSpeakingFrame())
            await self.push_frame(ProposedUserStoppedSpeakingFrame())
            return

        await self.push_frame(frame, direction)
