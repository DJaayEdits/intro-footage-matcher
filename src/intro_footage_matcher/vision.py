from __future__ import annotations

from pathlib import Path
from typing import Any
import math


DEFAULT_VISUAL_LABELS = [
    "quiet setup or travel", "successful play", "scoring or taking the lead",
    "confident aggressive play", "intense combat", "danger or low health",
    "mistake or failed play", "player death or defeat", "enemy comeback",
    "heroic comeback", "clutch last-second play", "victory or celebration",
    "funny unexpected moment", "surprised emotional reaction", "scoreboard or results screen",
]


def calibrate_label_scores(rows: list[dict[str, float]], *, top_k: int = 3) -> list[dict[str, float]]:
    """Reduce CLIP prompt-prior bias using per-video relative lift."""
    if not rows:
        return []
    labels = sorted({label for row in rows for label in row})
    means = {label: sum(row.get(label, 0.0) for row in rows) / len(rows) for label in labels}
    calibrated: list[dict[str, float]] = []
    for row in rows:
        candidates: list[tuple[str, float]] = []
        for label, raw in row.items():
            lift = raw / max(means[label], 1e-9)
            if lift >= 1.15:
                candidates.append((label, min(1.0, raw * math.sqrt(lift))))
        if not candidates and row:
            candidates = [max(row.items(), key=lambda item: item[1])]
        calibrated.append(dict(sorted(candidates, key=lambda item: item[1], reverse=True)[:top_k]))
    return calibrated


def describe_frames(
    paths: list[str | Path],
    labels: list[str] | None = None,
    *,
    model_name: str = "openai/clip-vit-base-patch32",
    batch_size: int = 16,
) -> list[dict[str, float]]:
    if not paths:
        return []
    try:
        import torch
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise RuntimeError("Visual analysis requires torch, pillow, and transformers") from exc

    concepts = labels or DEFAULT_VISUAL_LABELS
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = CLIPModel.from_pretrained(model_name, local_files_only=True).to(device)
    processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
    prompts = [f"a gameplay frame showing {label}" for label in concepts]
    results: list[dict[str, float]] = []
    for offset in range(0, len(paths), batch_size):
        batch_paths = paths[offset:offset + batch_size]
        images = []
        for path in batch_paths:
            with Image.open(path) as source:
                images.append(source.convert("RGB").copy())
        inputs = processor(text=prompts, images=images, return_tensors="pt", padding=True)
        inputs = {name: value.to(device) for name, value in inputs.items()}
        with torch.inference_mode():
            probabilities = model(**inputs).logits_per_image.softmax(dim=1).cpu()
        for row in probabilities:
            scored = {label: round(float(score), 6) for label, score in zip(concepts, row)}
            results.append(scored)
    return results
