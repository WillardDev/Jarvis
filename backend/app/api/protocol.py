"""Wire protocol between the browser and the voice backend.

Two kinds of message travel over the WebSocket:

* **Binary** frames carry raw PCM16 mono audio (16 kHz up, 24 kHz down).
* **Text** frames carry JSON. The browser sends control messages, the server
  sends events.
"""

from __future__ import annotations

from enum import StrEnum


class ClientMessage(StrEnum):
    """Control messages the browser may send."""

    RECORD_START = "record_start"
    RECORD_STOP = "record_stop"
    INTERRUPT = "interrupt"
    PING = "ping"


class ServerEvent(StrEnum):
    """Events the backend pushes to the browser."""

    READY = "ready"
    STATE = "state"
    USER_TRANSCRIPT = "user_transcript"
    ASSISTANT_TRANSCRIPT = "assistant_transcript"
    LATENCY = "latency"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class SessionState(StrEnum):
    """Coarse assistant state, mirrored by the UI."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class LatencyMark(StrEnum):
    """Stage boundaries recorded for every turn."""

    SPEECH_END = "speech_end"
    STT_FINAL = "stt_final"
    LLM_FIRST_TOKEN = "llm_first_token"
    TTS_FIRST_AUDIO = "tts_first_audio"
    AUDIO_FIRST_SENT = "audio_first_sent"
    LLM_DONE = "llm_done"
    TTS_DONE = "tts_done"
