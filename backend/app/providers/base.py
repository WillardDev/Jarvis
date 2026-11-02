"""Vendor-neutral provider interfaces.

Each provider wraps a Pipecat service so the rest of the app never imports a
vendor SDK. Swapping a vendor means editing (or adding) a single file in this
package and pointing the matching environment variable at it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pipecat.processors.frame_processor import FrameProcessor


class Provider(ABC):
    """Common shape for every provider: build a Pipecat processor."""

    @abstractmethod
    def build(self) -> FrameProcessor:
        """Return the Pipecat processor implementing this provider."""
        raise NotImplementedError


class STTProvider(Provider):
    """Speech-to-text provider."""

    @abstractmethod
    def build(self) -> FrameProcessor:
        """Return a processor that turns audio frames into transcription frames."""
        raise NotImplementedError


class LLMProvider(Provider):
    """Language-model provider."""

    @abstractmethod
    def build(self) -> FrameProcessor:
        """Return a processor that turns a run frame into streamed text frames."""
        raise NotImplementedError


class TTSProvider(Provider):
    """Text-to-speech provider."""

    @abstractmethod
    def build(self) -> FrameProcessor:
        """Return a processor that turns text frames into audio frames."""
        raise NotImplementedError
