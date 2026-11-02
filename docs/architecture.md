# Jarvis Architecture

## Monorepo
```
frontend/   # Vue 3 PWA
backend/    # FastAPI + Pipecat
docker/     # build contexts
docs/       # protocol, architecture
```

## Backend modules
- `app/api/` — WebSocket routes, session management, serializer, wire protocol
- `app/pipeline/` — Pipecat pipeline assembly, turn control, latency observer
- `app/providers/` — STT/LLM/TTS provider interfaces and implementations (Deepgram/Anthropic/Cartesia/ElevenLabs/mock)
- `app/tools/` — tool registry (Phase 2)
- `app/memory/` — conversation memory (Phase 2)

## Pipeline (Phase 1)
```
transport.input() -> TurnControlProcessor -> STT -> user_aggregator
                   -> LLM -> TTS -> assistant_aggregator -> transport.output()
```
- `TurnControlProcessor` converts browser `record_stop` into Pipecat turn-closing signals.
- `ExternalUserTurnStrategies(wait_for_transcript=True)` holds the turn open until `TranscriptionFrame` arrives.
- All frame flow is observed by `PipelineObserver` for latency instrumentation.

## Latency
Stage boundaries are timestamped on the pipeline clock and published as `latency` events. The browser renders them in a debug panel and measures "first audio played" itself.

## Barge-in
`interrupt` or a new `record_start` triggers `InterruptionFrame`. The output transport stops playback immediately and the serializer emits `{"type":"interrupted"}` so the browser clears its audio queue.

## Provider swap
Implement the `STTProvider`/`LLMProvider`/`TTSProvider` interfaces in `app/providers/base.py` and register in `app/providers/factory.py`. No pipeline code changes needed.
