from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path
from typing import Any


def _unit(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def measure_frame_metrics(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Frame metrics require numpy and pillow") from exc

    measured: list[dict[str, Any]] = []
    previous = None
    for item in frames:
        with Image.open(item["path"]) as image:
            grey = np.asarray(image.convert("L").resize((160, 90)), dtype=np.float32)
        motion = float(np.mean(np.abs(grey - previous)) / 255.0) if previous is not None else 0.0
        histogram, _ = np.histogram(grey, bins=32, range=(0, 256), density=True)
        previous_hist = measured[-1].get("_hist") if measured else None
        change = float(np.mean(np.abs(histogram - previous_hist)) * 32.0) if previous_hist is not None else 0.0
        measured.append({**item, "motion": motion, "change": change, "_hist": histogram})
        previous = grey
    for item in measured:
        item.pop("_hist", None)
    return measured


def measure_audio_windows(wav_path: str | Path, *, window_seconds: float = 0.5) -> list[dict[str, float]]:
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    results: list[dict[str, float]] = []
    with wave.open(str(wav_path), "rb") as source:
        if source.getsampwidth() != 2 or source.getnchannels() != 1:
            raise ValueError("Expected 16-bit mono WAV")
        rate = source.getframerate()
        count = max(1, round(rate * window_seconds))
        index = 0
        while raw := source.readframes(count):
            samples = array("h")
            samples.frombytes(raw)
            if not samples:
                break
            mean_square = sum(value * value for value in samples) / len(samples)
            rms = math.sqrt(mean_square) / 32768.0
            peak = max(abs(value) for value in samples) / 32768.0
            results.append({"time": index * window_seconds, "rms": rms, "peak": peak})
            index += 1
    return results


def select_representatives(
    frame_metrics: list[dict[str, Any]],
    audio_metrics: list[dict[str, Any]],
    transcripts: list[dict[str, Any]],
    *,
    max_frames: int = 1000,
) -> list[dict[str, Any]]:
    if max_frames <= 0 or not frame_metrics:
        return []
    if len(frame_metrics) <= max_frames:
        return list(frame_metrics)

    motions = _unit([float(item.get("motion", 0.0)) for item in frame_metrics])
    changes = _unit([float(item.get("change", 0.0)) for item in frame_metrics])
    ranked = sorted(
        zip(frame_metrics, motions, changes),
        key=lambda row: 0.55 * row[1] + 0.45 * row[2],
        reverse=True,
    )
    event_slots = max(2, max_frames // 2)
    chosen: dict[int, dict[str, Any]] = {id(row[0]): row[0] for row in ranked[:event_slots]}

    coverage_slots = max_frames - len(chosen)
    if coverage_slots > 0:
        last = len(frame_metrics) - 1
        for index in range(coverage_slots):
            position = round(index * last / max(1, coverage_slots - 1))
            chosen[id(frame_metrics[position])] = frame_metrics[position]
            if len(chosen) >= max_frames:
                break

    if len(chosen) < max_frames:
        for frame in frame_metrics:
            chosen[id(frame)] = frame
            if len(chosen) >= max_frames:
                break
    return sorted(chosen.values(), key=lambda item: float(item["time"]))

