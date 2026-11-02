"""Per-turn latency instrumentation.

Every stage boundary of the voice loop is timestamped on the pipeline clock,
so the numbers in the debug panel add up to real elapsed time rather than to
however long the observer took to wake up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    InterimTranscriptionFrame,
    LLMFullResponseEndFrame,
    LLMTextFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    TTSStoppedFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed

from app.api.protocol import LatencyMark, ServerEvent, SessionState


@dataclass
class TurnLatency:
    """Stage boundaries of a single turn, in milliseconds since the turn began."""

    turn: int
    marks: dict[str, float] = field(default_factory=dict)

    def as_payload(self) -> dict[str, float]:
        """Return the marks as plain JSON-friendly floats."""
        return {name: round(value, 1) for name, value in self.marks.items()}


class TurnLatencyTracker:
    """Collects the stage boundaries of the turn that is currently running."""

    def __init__(self) -> None:
        self._turn = 0
        self._origin_ns: int | None = None
        self._marks: dict[str, float] = {}

    @property
    def turn(self) -> int:
        """Number of the turn currently being measured."""
        return self._turn

    @property
    def marks(self) -> dict[str, float]:
        """Stage boundaries of the current turn, in milliseconds."""
        return dict(self._marks)

    def begin_turn(self, timestamp_ns: int) -> int:
        """Start a new turn; returns its number."""
        self._turn += 1
        self._origin_ns = timestamp_ns
        self._marks = {}
        return self._turn

    def mark(self, name: str, timestamp_ns: int) -> None:
        """Record a stage boundary. Later marks of the same name are ignored."""
        if name in self._marks:
            return
        if self._origin_ns is None:
            self._origin_ns = timestamp_ns
        self._marks[name] = (timestamp_ns - self._origin_ns) / 1_000_000

    def snapshot(self) -> TurnLatency:
        """Return an immutable view of the current turn's measurements."""
        return TurnLatency(turn=self._turn, marks=dict(self._marks))


class PipelineObserver(BaseObserver):
    """Turns frame flow into browser events and latency marks.

    Observers see every frame that moves through the pipeline without
    interfering with it, which is what makes them the right place to measure
    stage boundaries without changing how the pipeline behaves.
    """

    def __init__(self, session) -> None:
        super().__init__(observe_every_push=False)
        self._session = session

    async def on_push_frame(self, data: FramePushed) -> None:
        frame = data.frame
        timestamp_ns = data.timestamp

        if isinstance(frame, UserStartedSpeakingFrame):
            self._session.begin_turn(timestamp_ns)
            await self._session.set_state(SessionState.LISTENING)
        elif isinstance(frame, VADUserStoppedSpeakingFrame):
            await self._session.mark(LatencyMark.SPEECH_END.value, timestamp_ns)
        elif isinstance(frame, InterimTranscriptionFrame):
            await self._session.emit(
                ServerEvent.USER_TRANSCRIPT, text=frame.text, final=False
            )
        elif isinstance(frame, TranscriptionFrame):
            await self._session.mark(LatencyMark.STT_FINAL.value, timestamp_ns)
            await self._session.emit(
                ServerEvent.USER_TRANSCRIPT, text=frame.text, final=True
            )
        elif isinstance(frame, UserStoppedSpeakingFrame):
            await self._session.set_state(SessionState.THINKING)
        elif isinstance(frame, LLMTextFrame):
            await self._session.mark(LatencyMark.LLM_FIRST_TOKEN.value, timestamp_ns)
            await self._session.emit(
                ServerEvent.ASSISTANT_TRANSCRIPT, text=frame.text, final=False
            )
        elif isinstance(frame, LLMFullResponseEndFrame):
            await self._session.mark(LatencyMark.LLM_DONE.value, timestamp_ns)
            await self._session.emit(
                ServerEvent.ASSISTANT_TRANSCRIPT, text="", final=True
            )
        elif isinstance(frame, TTSAudioRawFrame):
            await self._session.mark(LatencyMark.TTS_FIRST_AUDIO.value, timestamp_ns)
        elif isinstance(frame, TTSStoppedFrame):
            await self._session.mark(LatencyMark.TTS_DONE.value, timestamp_ns)
        elif isinstance(frame, BotStartedSpeakingFrame):
            await self._session.set_state(SessionState.SPEAKING)
        elif isinstance(frame, BotStoppedSpeakingFrame):
            if self._session.state is SessionState.SPEAKING:
                await self._session.set_state(SessionState.IDLE)
