"""Processor to handle tool confirmations."""

from __future__ import annotations

from loguru import logger
from pipecat.frames.frames import Frame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class ToolConfirmationProcessor(FrameProcessor):
    """Handles tool execution confirmations."""

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        # Pass through for now - confirmation logic will be added
        await self.push_frame(frame, direction)
