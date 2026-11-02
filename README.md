# Jarvis

A real-time AI voice assistant web app: Vue 3 + FastAPI + Pipecat + WebSocket + push-to-talk.

## Stack
- **Frontend:** Vue 3 (Composition API, `<script setup>`), TypeScript (strict), Vite, Pinia, Tailwind CSS, PWA
- **Backend:** Python 3.11+, FastAPI, WebSockets, Pipecat, asyncio
- **STT:** Deepgram streaming (behind `STTProvider`) or `mock`
- **LLM:** Anthropic Claude streaming (behind `LLMProvider`) — model via `LLM_MODEL`, default `claude-sonnet-5-5`; `mock` available
- **TTS:** Cartesia (default) or ElevenLabs (behind `TTSProvider`) or `mock`
- **Infra:** Docker Compose, PostgreSQL + pgvector, Redis (behind `data` profile)

## Quick start (local dev, no API keys needed)
1. Copy `.env.example` to `.env`
2. Start the backend with mock providers:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
STT_PROVIDER=mock LLM_PROVIDER=mock TTS_PROVIDER=mock uvicorn app.main:app --reload
```
3. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```
4. Open http://localhost:5173, hold the button, ask a question, hear the answer. The **Latency** panel shows stage boundaries.

## Run with Docker
```bash
docker compose up --build
```
Frontend is served on http://localhost:8080, backend on http://localhost:8000.

## Architecture notes (Phase 1)
- **Push-to-talk:** `record_start`/`record_stop` over JSON, binary PCM16 audio (16 kHz in / 24 kHz out).
- **Turn control:** `record_stop` emits `JarvisTurnEndFrame` → `TurnControlProcessor` → Pipecat `ExternalUserTurnStrategies` waits for the final transcript before starting the LLM. Phase 2 swaps this for Silero VAD.
- **Everything streams:** partial/interim STT, token-level LLM, TTS starts on sentence boundaries.
- **Barge-in:** `interrupt` or a new `record_start` stops audio and cancels in-flight work.
- **Latency:** `PipelineObserver` timestamps every boundary on the pipeline clock; the browser shows them in the debug panel.
- **Provider interfaces:** swap vendors by changing one file (`backend/app/providers/factory.py`) or env vars.
- **Wire protocol:** see [docs/protocol.md](docs/protocol.md).

## Verification (Phase 1)
```bash
cd backend && PYTHONPATH=. pytest tests/test_voice_loop.py -q
```

## Environment
See [.env.example](.env.example) for all settings.
