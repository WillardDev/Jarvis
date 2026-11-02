"""HTTP and WebSocket endpoints."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket
from loguru import logger
from pipecat.workers.runner import WorkerRunner

from app.api.protocol import ServerEvent
from app.api.session import JarvisSession, SessionWriter
from app.config import Settings, get_settings
from app.pipeline.builder import build_voice_pipeline

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/config")
async def config() -> dict[str, object]:
    """Expose the few settings the browser needs to know about."""
    settings: Settings = get_settings()
    return {
        "input_sample_rate": settings.stt_sample_rate,
        "output_sample_rate": settings.tts_sample_rate,
        "turn_mode": settings.turn_mode,
    }


@router.websocket("/ws")
async def voice_session(websocket: WebSocket) -> None:
    """Run one voice session for the lifetime of the WebSocket."""
    settings = get_settings()
    await websocket.accept()

    writer = SessionWriter(websocket)
    session = JarvisSession(
        writer,
        input_sample_rate=settings.stt_sample_rate,
        output_sample_rate=settings.tts_sample_rate,
    )

    await session.emit(
        ServerEvent.READY,
        input_sample_rate=session.input_sample_rate,
        output_sample_rate=session.output_sample_rate,
    )

    pipeline = build_voice_pipeline(settings, session, writer)
    runner = WorkerRunner(handle_sigint=False)
    await runner.add_workers(pipeline.worker)

    logger.info("Voice session started")
    try:
        await runner.run()
    except Exception as exc:  # noqa: BLE001 - the socket is gone either way
        logger.exception(f"Voice session failed: {exc}")
        try:
            await session.emit(ServerEvent.ERROR, message=str(exc))
        except Exception:  # noqa: BLE001 - best effort, the socket may be gone
            pass
    finally:
        await runner.cancel()
        logger.info("Voice session ended")
