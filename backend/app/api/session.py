"""Per-connection session state.

The browser gets one WebSocket, one Pipecat pipeline and one session object.
Everything the server wants to say to the browser goes through here.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.api.protocol import LatencyMark, ServerEvent, SessionState
from app.pipeline.latency import TurnLatency, TurnLatencyTracker


class SessionWriter:
    """Serialises every write to the browser behind a single lock.

    Pipecat writes audio from its own task while the application writes
    events from the observer's task. Two concurrent writes on one WebSocket
    can interleave on the wire, so they share one lock.
    """

    def __init__(self, websocket: WebSocket) -> None:
        self._websocket = websocket
        self._lock = asyncio.Lock()

    async def send_bytes(self, data: bytes) -> None:
        """Send a binary message."""
        async with self._lock:
            await self._websocket.send_bytes(data)

    async def send_text(self, data: str) -> None:
        """Send a text message."""
        async with self._lock:
            await self._websocket.send_text(data)

    def __getattr__(self, name: str) -> Any:
        """Forward everything else (headers, state, close) to the real socket."""
        return getattr(self._websocket, name)


class JarvisSession:
    """Owns the events and the latency measurements of one browser connection."""

    def __init__(
        self,
        writer: SessionWriter,
        *,
        input_sample_rate: int,
        output_sample_rate: int,
    ) -> None:
        self._writer = writer
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self.tracker = TurnLatencyTracker()
        self.last_turn: TurnLatency | None = None
        self._state = SessionState.IDLE
        self._closed = False

    @property
    def state(self) -> SessionState:
        """The state the assistant is currently in."""
        return self._state

    @property
    def closed(self) -> bool:
        """True once the browser has gone away."""
        return self._closed

    def begin_turn(self, timestamp_ns: int) -> None:
        """Start measuring a new turn."""
        self.tracker.begin_turn(timestamp_ns)

    async def mark(self, name: str, timestamp_ns: int) -> None:
        """Record a stage boundary and publish the updated measurements.

        Only the first reading of a stage counts, and nothing is published
        when a stage repeats: ``audio_first_sent`` is offered every audio
        chunk, and only the first one is interesting.
        """
        if name in self.tracker.marks:
            return
        self.tracker.mark(name, timestamp_ns)
        await self.publish_latency()

    async def publish_latency(self) -> None:
        """Send the current turn's stage boundaries to the browser."""
        snapshot = self.tracker.snapshot()
        await self.emit(
            ServerEvent.LATENCY, turn=snapshot.turn, marks=snapshot.as_payload()
        )

    async def mark_audio_sent(self, timestamp_ns: int) -> None:
        """Record when the first answer audio byte went out on the wire."""
        await self.mark(LatencyMark.AUDIO_FIRST_SENT.value, timestamp_ns)

    async def emit(self, event: ServerEvent, **payload: Any) -> None:
        """Send one event to the browser.

        A browser that hangs up mid-turn is normal, not an error: the send
        fails and the session stops trying to talk to it.
        """
        if self._closed:
            return
        message = {"type": event.value, **payload}
        try:
            await self._writer.send_text(json.dumps(message))
        except (OSError, RuntimeError, WebSocketDisconnect) as exc:
            self._closed = True
            logger.debug(f"Session closed while sending {event.value}: {exc}")

    async def set_state(self, state: SessionState) -> None:
        """Move to a new state and tell the browser about it."""
        if state is self._state:
            return
        self._state = state
        await self.emit(ServerEvent.STATE, state=state.value)
