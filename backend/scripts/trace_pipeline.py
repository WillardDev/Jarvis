"""Trace the frames that flow through the pipeline. Development aid."""

from __future__ import annotations

import asyncio
import os
import time

os.environ["STT_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["TTS_PROVIDER"] = "mock"

from pipecat.frames.frames import (  # noqa: E402
    EndFrame,
    InputAudioRawFrame,
    ProposedUserStartedSpeakingFrame,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed  # noqa: E402
from pipecat.pipeline.pipeline import Pipeline  # noqa: E402
from pipecat.pipeline.worker import PipelineParams, PipelineWorker  # noqa: E402
from pipecat.processors.aggregators.llm_context import LLMContext  # noqa: E402
from pipecat.processors.aggregators.llm_response_universal import (  # noqa: E402
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.turns.user_turn_strategies import ExternalUserTurnStrategies  # noqa: E402
from pipecat.workers.runner import WorkerRunner  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.pipeline.control import TurnControlProcessor  # noqa: E402
from app.pipeline.frames import JarvisTurnEndFrame  # noqa: E402
from app.providers.factory import build_llm, build_stt, build_tts  # noqa: E402

IGNORED = {"InputAudioRawFrame", "TTSAudioRawFrame", "OutputAudioRawFrame"}


class Tracer(BaseObserver):
    def __init__(self) -> None:
        super().__init__(observe_every_push=False)
        self.t0 = time.monotonic()

    async def on_push_frame(self, data: FramePushed) -> None:
        name = type(data.frame).__name__
        if name in IGNORED:
            return
        print(f"{(time.monotonic() - self.t0) * 1000:8.1f}ms {name}", flush=True)


async def main() -> None:
    settings = get_settings()
    aggregators = LLMContextAggregatorPair(
        LLMContext(),
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=ExternalUserTurnStrategies(),
        ),
    )
    pipeline = Pipeline(
        [
            TurnControlProcessor(),
            build_stt(settings),
            aggregators.user(),
            build_llm(settings),
            build_tts(settings),
            aggregators.assistant(),
        ]
    )
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True),
        observers=[Tracer()],
        idle_timeout_secs=None,
    )
    await worker.queue_frame(ProposedUserStartedSpeakingFrame())
    await worker.queue_frame(
        InputAudioRawFrame(b"\x00\x00" * 16000, sample_rate=16000, num_channels=1)
    )

    runner = WorkerRunner(handle_sigint=False)
    await runner.add_workers(worker)
    run_task = asyncio.create_task(runner.run())

    await asyncio.sleep(0.4)
    await worker.queue_frame(JarvisTurnEndFrame())
    await asyncio.sleep(4)
    await worker.queue_frame(EndFrame())
    await asyncio.sleep(0.5)
    await runner.cancel()
    await run_task


asyncio.run(main())
