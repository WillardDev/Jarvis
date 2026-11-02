"""Runtime configuration, loaded from the environment (and an optional .env file)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# The reply is spoken aloud, so the prompt bans anything the voice cannot say.
DEFAULT_SYSTEM_PROMPT = """\
You are Jarvis, a voice assistant.

Your replies are read aloud by a speech engine, so:
- Speak in short, natural sentences, one idea at a time.
- Never use markdown, bullet points, numbered lists, headings, emoji, or \
special characters that cannot be spoken.
- Never describe formatting, just say the words.
- Keep it brief: two or three sentences unless you are asked for more detail.
- Answer directly, then stop. Do not ask whether you can help with anything else.
"""


class Settings(BaseSettings):
    """Every knob the voice loop exposes, all overridable through the environment."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Provider selection -------------------------------------------------
    stt_provider: str = "deepgram"
    llm_provider: str = "anthropic"
    tts_provider: str = "cartesia"

    # --- Credentials ---------------------------------------------------------
    deepgram_api_key: str = ""
    anthropic_api_key: str = ""
    cartesia_api_key: str = ""
    elevenlabs_api_key: str = ""

    # --- Model and voice -----------------------------------------------------
    llm_model: str = "claude-sonnet-5-5"
    llm_max_tokens: int = 1024
    llm_effort: str = "low"
    stt_model: str = "nova-3-general"
    stt_language: str = "en"
    # TTS_MODEL / TTS_VOICE_ID override the per-vendor defaults below.
    tts_model: str = ""
    tts_voice_id: str = ""
    cartesia_model: str = "sonic-3"
    cartesia_voice_id: str = "86e30c1d-714b-4074-a1f2-1cb6b552fb49"
    elevenlabs_model: str = "eleven_flash_v2_5"
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # --- Audio format --------------------------------------------------------
    # The browser always uploads 16 kHz mono PCM16; the server answers at
    # tts_sample_rate and tells the client which rate to expect.
    stt_sample_rate: int = 16000
    tts_sample_rate: int = 24000
    # "sentence" waits for a full sentence before synthesising (natural prosody).
    # "token" starts speaking on the first token (lower latency, choppier).
    tts_aggregation_mode: str = "sentence"

    # --- Behaviour -----------------------------------------------------------
    # "push_to_talk" is Phase 1. "vad" is Phase 2 (hands-free turn detection).
    turn_mode: str = "vad"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    # How long the client may hold the push-to-talk button before the turn is
    # force-closed, in seconds.
    max_turn_secs: float = 120.0

    # --- Server --------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "*"
    log_level: str = "INFO"

    @property
    def allowed_origins(self) -> list[str]:
        """Origins permitted to open the voice WebSocket."""
        if self.cors_origins.strip() in ("", "*"):
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
