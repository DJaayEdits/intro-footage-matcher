from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path
from typing import Any


def _ffmpeg_decode_to_wav(source: Path, target: Path) -> None:
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(source),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target),
    ], check=True)


def _local_whisper_model() -> str:
    root = Path.home() / ".cache/huggingface/hub/models--Systran--faster-whisper-small.en/snapshots"
    for model in sorted(root.glob("*/model.bin")):
        return str(model.parent)
    return "small.en"


def transcribe_voiceover(source: str | Path) -> dict[str, Any]:
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise RuntimeError(f"Voiceover does not exist: {source_path}")

    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper/numpy missing; run ./setup.sh") from exc

    with tempfile.TemporaryDirectory(prefix="ifm-voiceover-") as tmp:
        wav_path = Path(tmp) / "voiceover.wav"
        _ffmpeg_decode_to_wav(source_path, wav_path)

        with wave.open(str(wav_path), "rb") as audio_file:
            if audio_file.getsampwidth() != 2 or audio_file.getnchannels() != 1:
                raise RuntimeError("Unexpected decoded WAV format")
            samples = array("h")
            samples.frombytes(audio_file.readframes(audio_file.getnframes()))

        audio = np.asarray(samples, dtype=np.float32) / 32768.0

    model = WhisperModel(_local_whisper_model(), device="cpu", compute_type="int8")
    iterator, info = model.transcribe(
        audio,
        language="en",
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
        condition_on_previous_text=False,
    )

    segments = []
    words = []
    for segment in iterator:
        seg_words = []
        for word in segment.words or []:
            row = {
                "start": float(word.start),
                "end": float(word.end),
                "text": word.word.strip(),
                "probability": float(word.probability),
            }
            seg_words.append(row)
            words.append(row)
        segments.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
            "words": seg_words,
        })

    return {
        "source": str(source_path),
        "language": info.language,
        "language_probability": float(info.language_probability),
        "duration": float(info.duration),
        "segments": segments,
        "words": words,
    }


def write_voiceover_outputs(project_root: str | Path, source: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    report = transcribe_voiceover(source)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    transcript_json = reports / "fitmc-voiceover-transcript.json"
    transcript_txt = reports / "fitmc-voiceover-transcript.txt"

    transcript_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    transcript_txt.write_text(
        "\n".join(
            f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}"
            for seg in report["segments"]
        ) + "\n",
        encoding="utf-8",
    )
    return {
        "json": str(transcript_json),
        "text": str(transcript_txt),
        "segments": len(report["segments"]),
        "duration": report["duration"],
    }
