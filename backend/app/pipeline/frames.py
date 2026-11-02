"""Frames that only exist inside Jarvis."""

from __future__ import annotations

from dataclasses import dataclass

from pipecat.frames.frames import ControlFrame


@dataclass
class JarvisTurnEndFrame(ControlFrame):
    """The browser says the user has stopped speaking.

    One browser message has to become two pipeline frames: the VAD frame that
    makes the speech-to-text service finalise its transcript, and the proposal
    that closes the user turn. A frame is the only way to keep both in order
    relative to the audio that came before them.
    """
