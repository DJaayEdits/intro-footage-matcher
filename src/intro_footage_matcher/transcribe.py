from __future__ import annotations

from pathlib import Path
from typing import Any


class TranscriptionError(RuntimeError):
    pass


def transcribe_audio(
    audio_path: str | Path,
    model: str | Path,
    *,
    device: str = "cpu",
    compute_type: str = "int8",
) -> dict[str, Any]:
    """Transcribe locally with faster-whisper, retaining word timestamps."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TranscriptionError(
            "faster-whisper is not installed; run the project setup command first"
        ) from exc

    path = Path(audio_path).expanduser().resolve()
    if not path.is_file():
        raise TranscriptionError(f"Audio file does not exist: {path}")
    whisper = WhisperModel(str(model), device=device, compute_type=compute_type)
    iterator, info = whisper.transcribe(
        str(path),
        language="en",
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
        condition_on_previous_text=False,
    )
    segments: list[dict[str, Any]] = []
    for segment in iterator:
        segments.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
            "words": [
                {
                    "start": float(word.start),
                    "end": float(word.end),
                    "text": word.word,
                    "probability": float(word.probability),
                }
                for word in (segment.words or [])
            ],
        })
    return {
        "language": info.language,
        "language_probability": float(info.language_probability),
        "duration": float(info.duration),
        "segments": segments,
    }
