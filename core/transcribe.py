"""Speech-to-text module: faster-whisper with RTX 3050 GPU budgeting and CPU fallback."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import config

logger = logging.getLogger("VideoShorts.Transcribe")


class WhisperTranscriber:
    """Manages audio transcription with word-level timestamps and GPU VRAM protection."""

    def __init__(
        self,
        model_size: str = None,
        device: str = None,
        compute_type: str = None,
    ):
        self.model_size = model_size or config.ASR_MODEL_SIZE
        self.device = device or config.ASR_DEVICE
        self.compute_type = compute_type or config.ASR_COMPUTE_TYPE
        self._model = None

    def _load_model(self, force_cpu: bool = False):
        """Loads faster-whisper model."""
        from faster_whisper import WhisperModel

        target_device = "cpu" if force_cpu else self.device
        target_compute = "int8" if force_cpu else self.compute_type

        logger.info(
            "Loading faster-whisper model '%s' on device '%s' (%s)",
            self.model_size,
            target_device,
            target_compute,
        )

        return WhisperModel(
            self.model_size,
            device=target_device,
            compute_type=target_compute,
        )

    def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        """Transcribes audio file with automatic CPU fallback on CUDA/cuBLAS errors."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            if self._model is None:
                self._model = self._load_model(force_cpu=False)
            return self._run_transcription(self._model, audio_path)
        except Exception as e:
            if config.ASR_CPU_FALLBACK and self.device == "cuda":
                logger.warning(
                    "CUDA transcription failed (%s). Gracefully falling back to CPU int8 mode...",
                    e,
                )
                self.device = "cpu"
                self.compute_type = "int8"
                self._model = self._load_model(force_cpu=True)
                return self._run_transcription(self._model, audio_path)
            raise

    def _run_transcription(self, model, audio_path: Path) -> Dict[str, Any]:
        """Executes the transcription stream."""
        logger.info("Transcribing audio: %s", audio_path.name)

        segments_iter, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            word_timestamps=True,
            vad_filter=False,  # Avoid aggressive VAD removal on short/demo audio
        )

        segments: List[Dict[str, Any]] = []
        all_words: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for seg in segments_iter:
            full_text_parts.append(seg.text.strip())
            seg_dict = {
                "id": seg.id,
                "start": float(seg.start),
                "end": float(seg.end),
                "text": seg.text.strip(),
                "words": [],
            }

            if seg.words:
                for w in seg.words:
                    word_entry = {
                        "word": w.word,
                        "start": float(w.start),
                        "end": float(w.end),
                        "probability": float(w.probability),
                    }
                    seg_dict["words"].append(word_entry)
                    all_words.append(word_entry)

            segments.append(seg_dict)

        result = {
            "language": info.language,
            "language_probability": float(info.language_probability),
            "duration": float(info.duration),
            "text": " ".join(full_text_parts),
            "segments": segments,
            "words": all_words,
        }

        logger.info(
            "Transcription complete: language='%s' (prob=%.2f), segments=%d, words=%d",
            result["language"],
            result["language_probability"],
            len(segments),
            len(all_words),
        )
        return result
