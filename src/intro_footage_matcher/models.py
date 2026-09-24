from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Beat:
    id: str
    start: float
    end: float
    text: str
    roles: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Moment:
    id: str
    start: float
    end: float
    description: str
    roles: dict[str, float] = field(default_factory=dict)
    story_value: float = 0.0
    transcript: str = ""
    visual_labels: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    frame_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Match:
    beat_id: str
    moment_id: str
    match_score: float
    story_value_score: float
    why: str
    rank_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

