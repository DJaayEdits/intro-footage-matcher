from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from .beats import build_intro_beats
from .cache import StageCache, source_fingerprint
from .media import extract_audio, extract_sampled_frames, probe_media
from .models import Beat, Match, Moment
from .model_setup import ensure_required_models
from .moments import build_moments
from .ranking import build_embeddings, rank_matches
from .report import build_report_data, write_report_files
from .signals import measure_audio_windows, measure_frame_metrics, select_representatives
from .transcribe import transcribe_audio
from .vision import DEFAULT_VISUAL_LABELS, calibrate_label_scores, describe_frames

T = TypeVar("T")


def cached_stage(
    cache: StageCache,
    name: str,
    inputs: dict[str, Any],
    producer: Callable[[], T],
    *,
    force: bool = False,
) -> T:
    if not force:
        found = cache.load(name, inputs)
        if found is not None:
            print(f"[cache] {name}", flush=True)
            return found
    print(f"[run]   {name}", flush=True)
    value = producer()
    cache.write(name, inputs, value)
    return value


def _local_whisper_model() -> str:
    root = Path.home() / ".cache/huggingface/hub/models--Systran--faster-whisper-small.en/snapshots"
    for model in sorted(root.glob("*/model.bin")):
        return str(model.parent)
    return "small.en"


def _beats(items: list[dict[str, Any]]) -> list[Beat]:
    return [Beat(**item) for item in items]


def _moments(items: list[dict[str, Any]]) -> list[Moment]:
    return [Moment(**item) for item in items]


def _matches(items: dict[str, list[dict[str, Any]]]) -> dict[str, list[Match]]:
    return {beat_id: [Match(**item) for item in values] for beat_id, values in items.items()}


STAGES = ["probe", "audio", "transcript", "beats", "frames", "signals", "vision", "moments", "embeddings", "matches", "report"]


def build_stage_signatures(
    sources: dict[str, str],
    whisper_model: str,
    *,
    sample_fps: float,
    max_visual_frames: int,
    editorial_policy_version: int = 7,
) -> dict[str, dict[str, Any]]:
    """Describe every stage by all upstream data that can affect its output."""
    signatures: dict[str, dict[str, Any]] = {}
    signatures["probe"] = {**sources, "version": 1}
    signatures["audio"] = {**sources, "rate": 16000, "channels": 1, "version": 1}
    signatures["transcript"] = {
        "audio": signatures["audio"],
        "model": whisper_model,
        "version": 2,
    }
    signatures["beats"] = {"transcript": signatures["transcript"], "version": 5}
    signatures["frames"] = {
        "gameplay": sources["gameplay"],
        "fps": sample_fps,
        "width": 640,
        "version": 1,
    }
    signatures["signals"] = {
        "frames": signatures["frames"],
        "audio": signatures["audio"],
        "audio_window": 0.5,
        "version": 3,
    }
    signatures["vision"] = {
        "signals": signatures["signals"],
        "transcript": signatures["transcript"],
        "max_frames": max_visual_frames,
        "model": "openai/clip-vit-base-patch32",
        "labels": DEFAULT_VISUAL_LABELS,
        "version": 4,
    }
    signatures["moments"] = {
        "vision": signatures["vision"],
        "signals": signatures["signals"],
        "transcript": signatures["transcript"],
        "version": 6,
    }
    signatures["embeddings"] = {
        "beats": signatures["beats"],
        "moments": signatures["moments"],
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "version": 2,
    }
    signatures["matches"] = {
        "embeddings": signatures["embeddings"],
        "top_k": 3,
        "scoring_version": editorial_policy_version,
    }
    return signatures


def _is_forced(stage: str, force_stage: str | None) -> bool:
    return bool(force_stage and STAGES.index(stage) >= STAGES.index(force_stage))


def inspect_sources(intro: str | Path, gameplay: str | Path) -> dict[str, Any]:
    intro_info = probe_media(intro)
    gameplay_info = probe_media(gameplay)
    duration = gameplay_info["duration"]
    return {
        "intro": intro_info,
        "gameplay": gameplay_info,
        "estimate": {
            "transcription_minutes": round((intro_info["duration"] + duration) / 60, 1),
            "lightweight_frames_at_2fps": round(duration * 2),
            "max_heavy_visual_frames": min(1000, round(duration * 2)),
        },
    }


def run_analysis(
    project_root: str | Path,
    intro: str | Path,
    gameplay: str | Path,
    *,
    force_stage: str | None = None,
    sample_fps: float = 2.0,
    max_visual_frames: int = 1000,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    intro_path = Path(intro).expanduser().resolve()
    gameplay_path = Path(gameplay).expanduser().resolve()
    if force_stage and force_stage not in STAGES:
        raise ValueError(f"Unknown force stage: {force_stage}. Choose from {', '.join(STAGES)}")

    sources = {"intro": source_fingerprint(intro_path), "gameplay": source_fingerprint(gameplay_path)}
    run_id = f"{sources['intro'][:10]}-{sources['gameplay'][:10]}"
    run_root = root / "cache" / run_id
    cache = StageCache(run_root / "stages")
    artifacts = run_root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    whisper_model = _local_whisper_model()
    signatures = build_stage_signatures(
        sources, whisper_model, sample_fps=sample_fps, max_visual_frames=max_visual_frames
    )

    probe_inputs = signatures["probe"]
    probe = cached_stage(cache, "probe", probe_inputs, lambda: inspect_sources(intro_path, gameplay_path), force=_is_forced("probe", force_stage))

    # Fail before media extraction if setup did not provision the local models.
    ensure_required_models()

    intro_wav = artifacts / "intro.wav"
    gameplay_wav = artifacts / "gameplay.wav"
    audio_inputs = signatures["audio"]
    def make_audio() -> dict[str, str]:
        extract_audio(intro_path, intro_wav)
        extract_audio(gameplay_path, gameplay_wav)
        return {"intro": str(intro_wav), "gameplay": str(gameplay_wav)}
    audio = cached_stage(cache, "audio", audio_inputs, make_audio, force=_is_forced("audio", force_stage) or not intro_wav.exists() or not gameplay_wav.exists())

    transcript_inputs = signatures["transcript"]
    def make_transcripts() -> dict[str, Any]:
        return {
            "intro": transcribe_audio(audio["intro"], whisper_model),
            "gameplay": transcribe_audio(audio["gameplay"], whisper_model),
        }
    transcripts = cached_stage(cache, "transcript", transcript_inputs, make_transcripts, force=_is_forced("transcript", force_stage))

    beat_inputs = signatures["beats"]
    beat_data = cached_stage(
        cache, "beats", beat_inputs,
        lambda: [beat.to_dict() for beat in build_intro_beats(transcripts["intro"]["segments"])],
        force=_is_forced("beats", force_stage),
    )
    beats = _beats(beat_data)

    frame_root = artifacts / "frames"
    frame_root.mkdir(parents=True, exist_ok=True)
    frame_inputs = signatures["frames"]

    def make_frames() -> list[dict[str, Any]]:
        # Every attempt gets a fresh directory. An interrupted retry can never
        # delete or partially overwrite the last valid cached frame set.
        frame_dir = Path(tempfile.mkdtemp(prefix=f"{sample_fps:g}fps-", dir=frame_root))
        return extract_sampled_frames(gameplay_path, frame_dir, fps=sample_fps, width=640)

    frames = cached_stage(
        cache, "frames", frame_inputs,
        make_frames,
        force=_is_forced("frames", force_stage),
    )
    if any(not Path(item["path"]).exists() for item in frames):
        frames = make_frames()
        cache.write("frames", frame_inputs, frames)

    signal_inputs = signatures["signals"]
    def make_signals() -> dict[str, Any]:
        return {
            "frames": measure_frame_metrics(frames),
            "audio": measure_audio_windows(gameplay_wav, window_seconds=0.5),
        }
    signals = cached_stage(cache, "signals", signal_inputs, make_signals, force=_is_forced("signals", force_stage))

    vision_inputs = signatures["vision"]
    def make_vision() -> list[dict[str, Any]]:
        representatives = select_representatives(signals["frames"], signals["audio"], transcripts["gameplay"]["segments"], max_frames=max_visual_frames)
        labels = calibrate_label_scores(describe_frames([item["path"] for item in representatives]))
        return [{**item, "visual_labels": label_scores} for item, label_scores in zip(representatives, labels)]
    vision_frames = cached_stage(cache, "vision", vision_inputs, make_vision, force=_is_forced("vision", force_stage))

    moment_inputs = signatures["moments"]
    moment_data = cached_stage(
        cache, "moments", moment_inputs,
        lambda: [moment.to_dict() for moment in build_moments(vision_frames, signals["audio"], transcripts["gameplay"]["segments"], duration=probe["gameplay"]["duration"])],
        force=_is_forced("moments", force_stage),
    )
    moments = _moments(moment_data)

    embedding_inputs = signatures["embeddings"]
    embeddings = cached_stage(
        cache, "embeddings", embedding_inputs,
        lambda: dict(zip(("beats", "moments"), build_embeddings(beats, moments))),
        force=_is_forced("embeddings", force_stage),
    )

    match_inputs = signatures["matches"]
    match_data = cached_stage(
        cache, "matches", match_inputs,
        lambda: {key: [item.to_dict() for item in values] for key, values in rank_matches(beats, moments, embeddings["beats"], embeddings["moments"], top_k=3).items()},
        force=_is_forced("matches", force_stage),
    )
    matches = _matches(match_data)
    report_data = build_report_data(beats, moments, matches, {"intro": str(intro_path), "gameplay": str(gameplay_path)})
    write_report_files(report_data, root / "reports")
    (root / "cache" / "last_run.json").write_text(json.dumps({"run_id": run_id, "intro": str(intro_path), "gameplay": str(gameplay_path)}, indent=2) + "\n")
    return report_data
