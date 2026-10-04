from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import wave
from array import array
from pathlib import Path
from typing import Any

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".m4v", ".webm"}


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required tool not found on PATH: {name}")
    return path


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown media error").strip()
        raise RuntimeError(detail) from exc


def _probe(path: Path) -> dict[str, Any]:
    result = _run([
        _require_tool("ffprobe"), "-v", "error",
        "-show_entries",
        "format=filename,duration,size,bit_rate,start_time:"
        "stream=index,codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels",
        "-of", "json", str(path),
    ])
    raw = json.loads(result.stdout)
    streams = raw.get("streams", [])
    fmt = raw.get("format", {})
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not video:
        raise RuntimeError(f"No video stream: {path}")
    return {
        "path": str(path),
        "duration": float(fmt.get("duration") or 0.0),
        "size": int(fmt.get("size") or 0),
        "bit_rate": int(fmt.get("bit_rate") or 0),
        "video": {
            "codec": video.get("codec_name"),
            "width": int(video.get("width") or 0),
            "height": int(video.get("height") or 0),
            "frame_rate": video.get("avg_frame_rate"),
        },
        "audio": None if not audio else {
            "codec": audio.get("codec_name"),
            "sample_rate": int(audio.get("sample_rate") or 0),
            "channels": int(audio.get("channels") or 0),
        },
    }


def _safe_id(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    return f"{path.stem[:48]}-{digest}"


def _extract_frames(
    source: Path,
    output_dir: Path,
    *,
    sample_every: float,
    max_frames: int,
    width: int = 640,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(output_dir.glob("frame_*.jpg"))
    times_file = output_dir / "times.json"
    if existing and times_file.exists():
        times = json.loads(times_file.read_text(encoding="utf-8"))
        return [
            {"time": float(t), "path": str(p)}
            for t, p in zip(times, existing)
        ]

    probe = _probe(source)
    duration = float(probe["duration"])
    if duration <= 0:
        return []

    count = max(1, min(max_frames, int(duration // sample_every) + 1))
    if count == 1:
        times = [0.0]
    else:
        times = [round(i * duration / count, 3) for i in range(count)]

    frames: list[dict[str, Any]] = []
    for index, second in enumerate(times, 1):
        out = output_dir / f"frame_{index:04d}.jpg"
        if not out.exists():
            _run([
                _require_tool("ffmpeg"), "-v", "error", "-y",
                "-ss", f"{second:.3f}", "-i", str(source),
                "-frames:v", "1",
                "-vf", f"scale={width}:-2:flags=fast_bilinear",
                "-q:v", "4", str(out),
            ])
        frames.append({"time": second, "path": str(out)})

    times_file.write_text(json.dumps(times, indent=2), encoding="utf-8")
    return frames


def _extract_audio(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        return
    _run([
        _require_tool("ffmpeg"), "-v", "error", "-y", "-i", str(source),
        "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(output),
    ])


def _local_whisper_model() -> str:
    root = Path.home() / ".cache/huggingface/hub/models--Systran--faster-whisper-small.en/snapshots"
    for model in sorted(root.glob("*/model.bin")):
        return str(model.parent)
    return "small.en"


def _transcribe_many(items: list[tuple[Path, Path]]) -> dict[str, Any]:
    if not items:
        return {}
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed; run ./setup.sh") from exc

    model = WhisperModel(_local_whisper_model(), device="cpu", compute_type="int8")
    results: dict[str, Any] = {}

    import numpy as np

    for source, wav in items:
        # We create these files ourselves as 16 kHz mono PCM WAV. Load the
        # samples directly and pass a float32 NumPy array to faster-whisper.
        # This intentionally bypasses PyAV's file decoder so transcription is
        # not coupled to PyAV's av.open keyword compatibility.
        with wave.open(str(wav), "rb") as audio_file:
            if (
                audio_file.getsampwidth() != 2
                or audio_file.getnchannels() != 1
                or audio_file.getframerate() != 16000
            ):
                raise RuntimeError(f"Unexpected cached WAV format: {wav}")
            samples = array("h")
            samples.frombytes(audio_file.readframes(audio_file.getnframes()))
        audio = np.asarray(samples, dtype=np.float32) / 32768.0

        iterator, info = model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            condition_on_previous_text=False,
        )
        segments = []
        for segment in iterator:
            segments.append({
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
            })
        results[str(source)] = {
            "language": info.language,
            "duration": float(info.duration),
            "segments": segments,
        }
    return results


def build_folder_index(
    project_root: str | Path,
    clips_root: str | Path,
    *,
    sample_every: float = 8.0,
    max_frames_per_video: int = 90,
    transcribe_specific: bool = True,
) -> dict[str, Any]:
    project = Path(project_root).expanduser().resolve()
    root = Path(clips_root).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"Clips root does not exist: {root}")
    if sample_every <= 0 or max_frames_per_video <= 0:
        raise ValueError("Sampling values must be positive")

    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )
    if not files:
        raise RuntimeError(f"No video files found under: {root}")

    cache_root = project / "cache" / "folder-index"
    frame_root = cache_root / "frames"
    audio_root = cache_root / "audio"
    transcript_path = cache_root / "specific-transcripts.json"
    cache_root.mkdir(parents=True, exist_ok=True)

    rows = []
    transcript_jobs: list[tuple[Path, Path]] = []

    for number, path in enumerate(files, 1):
        relative = path.relative_to(root)
        top_folder = relative.parts[0] if len(relative.parts) > 1 else ""
        category = (
            "fit" if top_folder.lower() == "fit"
            else "rusher" if top_folder.lower() == "rusher"
            else "general"
        )
        print(f"[{number}/{len(files)}] {category}: {relative}", flush=True)

        try:
            probe = _probe(path)
            item_id = _safe_id(path)
            frames = _extract_frames(
                path,
                frame_root / item_id,
                sample_every=sample_every,
                max_frames=max_frames_per_video,
            )

            transcript_file = None
            should_transcribe = transcribe_specific and category in {"fit", "rusher"} and probe.get("audio")
            if should_transcribe:
                wav = audio_root / f"{item_id}.wav"
                _extract_audio(path, wav)
                transcript_jobs.append((path, wav))
                transcript_file = str(wav)

            rows.append({
                "id": item_id,
                "path": str(path),
                "relative_path": str(relative),
                "category": category,
                "probe": probe,
                "frames": frames,
                "transcript_audio": transcript_file,
                "error": None,
            })
        except Exception as exc:
            rows.append({
                "id": _safe_id(path),
                "path": str(path),
                "relative_path": str(relative),
                "category": category,
                "probe": None,
                "frames": [],
                "transcript_audio": None,
                "error": str(exc),
            })

    transcripts: dict[str, Any] = {}
    if transcript_jobs:
        if transcript_path.exists():
            try:
                transcripts.update(json.loads(transcript_path.read_text(encoding="utf-8")))
            except Exception:
                pass
        missing = [(src, wav) for src, wav in transcript_jobs if str(src) not in transcripts]
        if missing:
            print(f"[transcribe] {len(missing)} Fit/Rusher source videos", flush=True)
            transcripts.update(_transcribe_many(missing))
            transcript_path.write_text(json.dumps(transcripts, indent=2), encoding="utf-8")

    for row in rows:
        if row["path"] in transcripts:
            row["transcript"] = transcripts[row["path"]]

    counts = {
        "total": len(rows),
        "fit": sum(1 for r in rows if r["category"] == "fit"),
        "rusher": sum(1 for r in rows if r["category"] == "rusher"),
        "general": sum(1 for r in rows if r["category"] == "general"),
        "errors": sum(1 for r in rows if r["error"]),
    }

    payload = {
        "clips_root": str(root),
        "sample_every_seconds": sample_every,
        "max_frames_per_video": max_frames_per_video,
        "transcribed_specific_folders": transcribe_specific,
        "counts": counts,
        "videos": rows,
    }

    reports = project / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    output = reports / "footage-index.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
