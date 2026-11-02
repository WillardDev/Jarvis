"""Wake word detection using openWakeWord for "Hey Jarvis"."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Callable

import numpy as np
from loguru import logger

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import ai_edge_litert.interpreter as tflite
        import sys

        sys.modules.setdefault("tflite_runtime", type(sys)("tflite_runtime"))
        sys.modules["tflite_runtime"].interpreter = tflite
        sys.modules["tflite_runtime.interpreter"] = tflite
    except ImportError:
        tflite = None

from openwakeword.model import Model


class WakeWordDetector:
    """Detect "Hey Jarvis" wake word."""

    def __init__(
        self,
        model_dir: str | Path | None = None,
        threshold: float = 0.5,
        on_detected: Callable[[], None] | None = None,
    ):
        self.threshold = threshold
        self.on_detected = on_detected
        self.model = None
        self._running = False
        self._lock = asyncio.Lock()

        if model_dir is None:
            model_dir = Path(__file__).parent.parent.parent
        self.model_dir = Path(model_dir)

    async def start(self) -> None:
        """Initialize the wake word model."""
        if self.model is not None:
            return

        wakeword_path = self.model_dir / "hey_jarvis_v0.1.tflite"
        melspec_path = self.model_dir / "melspectrogram.tflite"
        embedding_path = self.model_dir / "embedding_model.tflite"

        if not wakeword_path.exists():
            logger.warning(f"Wake word model not found at {wakeword_path}")
            return

        try:
            self.model = Model(
                wakeword_models=[str(wakeword_path)],
                inference_framework="tflite",
                melspec_model_path=str(melspec_path) if melspec_path.exists() else None,
                embedding_model_path=str(embedding_path) if embedding_path.exists() else None,
            )
            logger.info("Wake word detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            self.model = None

    def process_audio(self, audio: bytes) -> bool:
        """Process audio chunk and return True if wake word detected."""
        if self.model is None or self._running is False:
            return False

        try:
            # Convert bytes to int16 numpy array
            audio_array = np.frombuffer(audio, dtype=np.int16)
            prediction = self.model.predict(audio_array)
            for name, score in prediction.items():
                if score >= self.threshold:
                    logger.info(f"Wake word detected: {name} ({score:.3f})")
                    if self.on_detected:
                        self.on_detected()
                    self.model.reset()
                    return True
            return False
        except Exception as e:
            logger.debug(f"Wake word processing error: {e}")
            return False

    async def stop(self) -> None:
        """Stop the wake word detector."""
        self._running = False
        if self.model:
            try:
                self.model.reset()
            except Exception:
                pass
