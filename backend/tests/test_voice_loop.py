"""End-to-end check of the voice loop, driven by the mock providers.

The mock providers emit the same frame types as the real ones, so this test
covers the parts that are easy to get wrong: the turn handshake, the order of
the transcript events, and the latency marks.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import AsyncIterator, Callable

import pytest
import uvicorn
from websockets.asyncio.client import connect

# The settings are read from the environment, so the providers have to be
# chosen before the application is built.
os.environ["STT_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["TTS_PROVIDER"] = "mock"

from app.main import create_app  # noqa: E402

Event = dict


@pytest.fixture
async def ws_url() -> AsyncIterator[str]:
    """Run the backend on an ephemeral port and yield its WebSocket URL."""
    config = uvicorn.Config(create_app(), host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    socket = config.bind_socket()
    port = socket.getsockname()[1]

    task = asyncio.create_task(server.serve(sockets=[socket]))
    for _ in range(200):
        if server.started:
            break
        await asyncio.sleep(0.05)

    try:
        yield f"ws://127.0.0.1:{port}/ws"
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(task, timeout=15)
        except TimeoutError:
            task.cancel()


async def _drain(
    ws,
    *,
    until: Callable[[Event], bool] | None = None,
    min_audio_bytes: int = 0,
    timeout: float = 20.0,
) -> tuple[list[Event], int]:
    """Collect events until the predicate holds and enough audio has arrived."""
    events: list[Event] = []
    audio_bytes = 0
    satisfied = until is None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=3.0)
        except TimeoutError:
            break
        if isinstance(message, bytes):
            audio_bytes += len(message)
        else:
            event = json.loads(message)
            events.append(event)
            if until is not None and until(event):
                satisfied = True
        if satisfied and audio_bytes >= min_audio_bytes:
            break
    return events, audio_bytes


async def _speak(ws) -> None:
    """Run one push-to-talk turn."""
    await ws.send(json.dumps({"type": "record_start"}))
    await ws.send(b"\x00\x00" * 16000)  # one second of 16 kHz mono PCM16
    await asyncio.sleep(0.4)
    await ws.send(json.dumps({"type": "record_stop"}))


async def test_voice_loop_returns_transcript_and_audio(ws_url: str) -> None:
    """A push-to-talk turn produces a transcript and an answer."""
    async with connect(ws_url) as ws:
        ready = json.loads(await ws.recv())
        assert ready["type"] == "ready"
        assert ready["input_sample_rate"] == 16000

        await _speak(ws)

        def saw_final_transcript(event: Event) -> bool:
            return event["type"] == "user_transcript" and event["final"]

        events, _ = await _drain(ws, until=saw_final_transcript)

    types = [event["type"] for event in events]
    assert "user_transcript" in types
    assert "state" in types

    finals = [e for e in events if e["type"] == "user_transcript" and e["final"]]
    assert finals[0]["text"] == "what is the weather like today"


async def test_voice_loop_emits_audio_and_latency_marks(ws_url: str) -> None:
    """The answer reaches the browser as audio, and every stage is timed."""
    async with connect(ws_url) as ws:
        await ws.recv()  # ready
        await _speak(ws)

        def finished(event: Event) -> bool:
            if event["type"] != "latency":
                return False
            return "tts_first_audio" in event["marks"]

        events, audio_bytes = await _drain(ws, until=finished, min_audio_bytes=1)

    assert audio_bytes > 0, "the server should stream answer audio"

    latency = [e for e in events if e["type"] == "latency"]
    marks = latency[-1]["marks"]
    for stage in ("speech_end", "stt_final", "llm_first_token", "tts_first_audio"):
        assert stage in marks, f"missing latency mark: {stage}"
    assert marks["speech_end"] <= marks["stt_final"] <= marks["llm_first_token"]
    assert marks["llm_first_token"] <= marks["tts_first_audio"]


async def test_voice_loop_reports_assistant_transcript(ws_url: str) -> None:
    """The assistant's answer is streamed back as text."""
    async with connect(ws_url) as ws:
        await ws.recv()  # ready
        await _speak(ws)

        def saw_final_answer(event: Event) -> bool:
            return event["type"] == "assistant_transcript" and event["final"]

        events, _ = await _drain(ws, until=saw_final_answer)

    deltas = [
        event["text"]
        for event in events
        if event["type"] == "assistant_transcript" and not event["final"]
    ]
    assert "".join(deltas).strip().endswith("tomorrow.")


async def test_session_ends_when_the_browser_disconnects(ws_url: str) -> None:
    """Hanging up tears the pipeline down instead of leaking it."""
    async with connect(ws_url) as ws:
        await ws.recv()  # ready
        await _speak(ws)
        await _drain(ws, until=lambda event: event["type"] == "user_transcript")
