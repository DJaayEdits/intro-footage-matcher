from __future__ import annotations

import math
from typing import Any

from .beats import classify_editorial_roles
from .models import Moment


def compose_description(transcript: str, visual_labels: dict[str, float]) -> str:
    parts: list[str] = []
    if transcript.strip():
        parts.append(f'Dialogue: "{transcript.strip()}"')
    top_visuals = [name for name, score in sorted(visual_labels.items(), key=lambda item: item[1], reverse=True) if score >= 0.05][:3]
    if top_visuals:
        parts.append(f"visuals: {', '.join(top_visuals)}")
    if not parts:
        return "Gameplay activity."
    return "; ".join(parts) + "."


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return [1.0 if high > 0 else 0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def build_moments(
    frames: list[dict[str, Any]],
    audio: list[dict[str, Any]],
    transcript: list[dict[str, Any]],
    *,
    duration: float,
    max_moments: int = 400,
) -> list[Moment]:
    anchors: list[tuple[float, float]] = []
    visual_strengths = [0.55 * float(item.get("motion", 0)) + 0.45 * float(item.get("change", 0)) for item in frames]
    for item, strength in zip(frames, _normalize(visual_strengths)):
        if strength >= 0.60 or len(frames) == 1:
            anchors.append((float(item["time"]), 0.55 + 0.45 * strength))
    audio_strengths = [0.65 * float(item.get("rms", 0)) + 0.35 * float(item.get("peak", 0)) for item in audio]
    for item, strength in zip(audio, _normalize(audio_strengths)):
        if strength >= 0.72:
            anchors.append((float(item["time"]), 0.45 + 0.40 * strength))
    for item in transcript:
        text = str(item.get("text", "")).strip()
        if text:
            anchors.append(((float(item["start"]) + float(item["end"])) / 2, 0.62))
    if not anchors:
        return []

    selected: list[tuple[float, float]] = []
    for center, strength in sorted(anchors, key=lambda item: item[1], reverse=True):
        if all(abs(center - prior[0]) >= 6.0 for prior in selected):
            selected.append((center, strength))
            if len(selected) >= max_moments:
                break
    selected.sort()

    moments: list[Moment] = []
    for index, (center, anchor_strength) in enumerate(selected, start=1):
        cluster_centers = [candidate for candidate, _ in anchors if abs(candidate - center) < 6.0]
        start = max(0.0, min(cluster_centers, default=center) - 4.0)
        end = min(float(duration), max(cluster_centers, default=center) + 6.0)
        if end - start > 15.0:
            start = max(0.0, center - 6.0)
            end = min(float(duration), start + 15.0)
        if end - start < min(6.0, duration):
            if start == 0.0:
                end = min(float(duration), 10.0)
            else:
                start = max(0.0, end - 10.0)

        local_frames = [item for item in frames if start <= float(item["time"]) <= end]
        local_audio = [item for item in audio if start <= float(item["time"]) <= end]
        local_speech = [item for item in transcript if float(item["end"]) >= start and float(item["start"]) <= end]
        speech = " ".join(str(item.get("text", "")).strip() for item in local_speech).strip()
        labels: dict[str, float] = {}
        for frame in local_frames:
            for label, score in frame.get("visual_labels", {}).items():
                labels[label] = max(labels.get(label, 0.0), float(score))
        description = compose_description(speech, labels)
        roles = classify_editorial_roles(speech) if speech else {}
        for label, score in labels.items():
            if score < 0.20:
                continue
            for role, confidence in classify_editorial_roles(label).items():
                roles[role] = max(roles.get(role, 0.0), min(1.0, confidence * score))
        if not roles:
            roles = {"setup": 0.25}
        motion = max((float(item.get("motion", 0.0)) for item in local_frames), default=0.0)
        change = max((float(item.get("change", 0.0)) for item in local_frames), default=0.0)
        loudness = max((float(item.get("rms", 0.0)) for item in local_audio), default=0.0)
        role_peak = max(roles.values(), default=0.0)
        outcome_bonus = 0.15 if set(roles) & {"failure", "defeat", "victory", "clutch", "comeback", "setback"} else 0.0
        story_value = min(100.0, 100 * (0.25 * min(1.0, motion * 3) + 0.20 * min(1.0, change * 3) + 0.20 * min(1.0, loudness * 5) + 0.20 * role_peak + 0.15 * anchor_strength + outcome_bonus))
        frame_path = max(local_frames, key=lambda item: float(item.get("motion", 0)) + float(item.get("change", 0))).get("path") if local_frames else None
        moments.append(Moment(
            id=f"m{index:04d}", start=round(start, 3), end=round(end, 3),
            description=description, roles=roles, story_value=round(story_value, 2),
            transcript=speech, visual_labels=labels,
            evidence={"motion": motion, "change": change, "loudness": loudness, "anchor_strength": anchor_strength},
            frame_path=str(frame_path) if frame_path else None,
        ))
    return moments
