from __future__ import annotations

from fractions import Fraction
from typing import Any


def require_exact_frame_rate(project_rate: str, *source_rates: str) -> int:
    try:
        project = Fraction(project_rate)
        sources = [Fraction(value) for value in source_rates]
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("Invalid project or source frame rate") from exc
    if project.denominator != 1 or project != 60:
        raise ValueError(f"Expected an exact 60 fps project frame rate, got {project_rate}")
    if any(rate != project for rate in sources):
        raise ValueError(
            f"Expected exact 60 fps source frame rates, got {', '.join(source_rates)}"
        )
    return int(project)


def build_edit_plan(
    report: dict[str, Any],
    *,
    fps: int,
    intro_duration: float,
    choices: dict[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Turn ranked matches into contiguous, frame-aligned B-roll slots."""
    selected = choices or {}
    results = report["results"]
    plan: list[dict[str, Any]] = []
    used_source_ranges: list[tuple[float, float]] = []
    for index, result in enumerate(results):
        beat = result["beat"]
        record_start = round(float(beat["start"]) * fps)
        next_start = (
            float(results[index + 1]["beat"]["start"])
            if index + 1 < len(results)
            else intro_duration
        )
        duration = round(next_start * fps) - record_start
        recommendations = result["recommendations"]
        preferred = selected.get(index, 0)
        if preferred >= len(recommendations):
            raise ValueError(f"Recommendation choice for {beat['id']} is out of range")
        ordered = [recommendations[preferred], *(
            recommendation
            for candidate_index, recommendation in enumerate(recommendations)
            if candidate_index != preferred
        )]
        fitting = [
            recommendation for recommendation in ordered
            if round((float(recommendation["end"]) - float(recommendation["start"])) * fps) >= duration
        ]
        if not fitting:
            raise ValueError(f"Recommendation for {beat['id']} is shorter than its timeline slot")
        recommendation = next((
            candidate for candidate in fitting
            if all(
                float(candidate["end"]) <= used_start
                or float(candidate["start"]) >= used_end
                for used_start, used_end in used_source_ranges
            )
        ), None)
        if recommendation is None:
            raise ValueError(f"No non-overlapping recommendation is available for {beat['id']}")
        used_source_ranges.append((float(recommendation["start"]), float(recommendation["end"])))
        plan.append({
            "beat_id": beat["id"],
            "beat_text": beat["text"],
            "record_start": record_start,
            "duration": duration,
            "source_start": round(float(recommendation["start"]) * fps),
            "source_timecode": recommendation["start_timecode"],
        })
    return plan
