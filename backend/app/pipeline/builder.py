"""Assembles the Pipecat pipeline for one browser session.

The shape of the pipeline is deliberately fixed for Phase 1:

    transport.input() -> turn control -> STT -> user aggregator
                      -> LLM -> TTS -> assistant aggregator -> transport.output()

The turn-control processor is the only piece that Phase 2 replaces: hands-free
turn detection swaps the browser's ``record_stop`` for a VAD signal.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.turns.user_turn_strategies import UserTurnStrategies

from app.api.serializer import JarvisSerializer
from app.api.session import JarvisSession, SessionWriter
from app.config import Settings
from app.pipeline.control import TurnControlProcessor
from app.pipeline.latency import PipelineObserver
from app.providers.factory import build_llm, build_stt, build_tts


@dataclass
class VoicePipeline:
    """The pieces of one running voice session."""

    worker: PipelineWorker
    transport: FastAPIWebsocketTransport
    observer: PipelineObserver


def build_voice_pipeline(
    settings: Settings,
    session: JarvisSession,
    writer: SessionWriter,
) -> VoicePipeline:
    """Build the pipeline that serves one browser connection."""
    serializer = JarvisSerializer(
        input_sample_rate=settings.stt_sample_rate,
        output_sample_rate=settings.tts_sample_rate,
        on_audio_sent=session.mark_audio_sent,
    )
    transport = FastAPIWebsocketTransport(
        websocket=writer,
        params=FastAPIWebsocketParams(
            serializer=serializer,
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=settings.stt_sample_rate,
            audio_out_sample_rate=settings.tts_sample_rate,
            # One 10 ms chunk per WebSocket message: the default of four adds
            # 40 ms to every reply.
            audio_out_10ms_chunks=1,
        ),
    )

    # Phase 2: Use VAD for hands-free turn detection
    vad_analyzer = SileroVADAnalyzer(
        params=VADParams(
            confidence=0.7,
            start_secs=0.2,
            stop_secs=0.8,  # Tune to avoid cutting off mid-thought
            min_volume=0.6,
        )
    )
    vad_processor = VADProcessor(vad_analyzer=vad_analyzer)

    aggregators = LLMContextAggregatorPair(
        LLMContext(),
        user_params=LLMUserAggregatorParams(
            # Use VAD-based turn strategies for hands-free operation
            user_turn_strategies=UserTurnStrategies(),
        ),
    )

    observer = PipelineObserver(session)

    if settings.turn_mode == "vad":
        pipeline = Pipeline(
            [
                transport.input(),
                vad_processor,
                build_stt(settings),
                aggregators.user(),
                build_llm(settings),
                build_tts(settings),
                aggregators.assistant(),
                transport.output(),
            ]
        )
    else:
        pipeline = Pipeline(
            [
                transport.input(),
                TurnControlProcessor(),
                build_stt(settings),
                aggregators.user(),
                build_llm(settings),
                build_tts(settings),
                aggregators.assistant(),
                transport.output(),
            ]
        )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=settings.stt_sample_rate,
            audio_out_sample_rate=settings.tts_sample_rate,
            enable_metrics=True,
        ),
        observers=[observer],
        # A voice session is idle whenever the user is thinking, so the default
        # idle timeout would kill the conversation.
        idle_timeout_secs=None,
    )

    @transport.event_handler("on_client_disconnected")
    async def _on_client_disconnected(transport, websocket) -> None:
        # Without this the pipeline would keep running after the browser is
        # gone, holding the provider connections open.
        await worker.queue_frame(EndFrame())

    return VoicePipeline(worker=worker, transport=transport, observer=observer)


    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=settings.stt_sample_rate,
            audio_out_sample_rate=settings.tts_sample_rate,
            enable_metrics=True,
        ),
        observers=[observer],
        # A voice session is idle whenever the user is thinking, so the default
        # idle timeout would kill the conversation.
        idle_timeout_secs=None,
    )

    @transport.event_handler("on_client_disconnected")
    async def _on_client_disconnected(transport, websocket) -> None:
        # Without this the pipeline would keep running after the browser is
        # gone, holding the provider connections open.
        await worker.queue_frame(EndFrame())

    return VoicePipeline(worker=worker, transport=transport, observer=observer)
