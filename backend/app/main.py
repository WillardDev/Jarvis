"""Jarvis backend: a streaming voice loop built on FastAPI and Pipecat."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start-up and shut-down hooks."""
    settings = get_settings()
    logger.info(
        f"Jarvis backend starting with STT={settings.stt_provider} "
        f"LLM={settings.llm_provider} ({settings.llm_model}) TTS={settings.tts_provider}"
    )
    yield
    logger.info("Jarvis backend stopped")


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title="Jarvis voice backend", version="0.1.0", lifespan=lifespan)

    origins = settings.allowed_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
