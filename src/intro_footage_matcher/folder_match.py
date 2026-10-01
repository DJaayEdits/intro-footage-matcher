from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from .beats import build_intro_beats
from .ranking import embed_texts


def _norm_rows(values: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(values, axis=1, keepdims=True)
    denom[denom == 0] = 1.0
    return values / denom


def _topic_boost(text: str, relative_path: str) -> float:
    q = text.lower()
    p = relative_path.lower()
    boost = 0.0

    rules = [
        (r"fitlantis|ocean monument|bedrock|chrome ?crusher|coords?|team aurora", ("fitlantis",), 0.42),
        (r"camping rusher|rusher war|rushers?|veterans? vs|queue", ("rusher/", "teamveteran", "largest battle"), 0.34),
        (r"summermelon", ("summermelon",), 0.45),
        (r"largest battle|battle.*server history", ("largest battle",), 0.42),
        (r"personal story|early days|original player|built bases|friends with", ("personal story",), 0.28),
        (r"team veteran|veteran side|leader of the veterans|rallied the og", ("teamveteran", "rusher/"), 0.34),
        (r"nuking|sanctuary", ("nuking rusher",), 0.40),
        (r"diamond rushers", ("diamond rushers",), 0.40),
    ]
    for pattern, needles, amount in rules:
        if re.search(pattern, q) and any(n in p for n in needles):
            boost = max(boost, amount)
    return boost


def _confidence(score: float, *, evidence: str) -> str:
    if evidence == "specific-transcript":
        if score >= 0.78:
            return "high"
        if score >= 0.58:
            return "medium"
        return "low"
    if score >= 0.72:
        return "medium"
    return "low"


def _clip_range(center: float, beat_duration: float, media_duration: float) -> tuple[float, float]:
    length = max(3.0, min(8.0, beat_duration))
    start = max(0.0, center - min(1.0, length * 0.2))
    end = min(media_duration, start + length)
    if end - start < length and media_duration >= length:
        start = max(0.0, end - length)
    return round(start, 3), round(end, 3)


def _specific_candidates(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for video in videos:
        transcript = video.get("transcript") or {}
        for segment in transcript.get("segments", []):
            text = str(segment.get("text", "")).strip()
            if not text:
                continue
            rows.append({
                "path": video["path"],
                "relative_path": video["relative_path"],
                "category": video["category"],
                "start": float(segment["start"]),
                "end": float(segment["end"]),
                "text": text,
            })
    return rows


def _load_or_build_clip_embeddings(
    project_root: Path,
    frame_rows: list[dict[str, Any]],
    *,
    batch_size: int = 24,
) -> np.ndarray:
    cache_dir = project_root / "cache" / "folder-index"
    cache_dir.mkdir(parents=True, exist_ok=True)
    npy_path = cache_dir / "clip-frame-embeddings.npy"
    meta_path = cache_dir / "clip-frame-embeddings-meta.json"
    signature = [
        f"{row['path']}|{row['time']:.3f}|{row['frame_path']}"
        for row in frame_rows
    ]

    if npy_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("signature") == signature:
                print("[cache] visual embeddings", flush=True)
                return np.load(npy_path)
        except Exception:
            pass

    try:
        import torch
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise RuntimeError("Visual matching requires torch, pillow, and transformers") from exc

    model_id = "openai/clip-vit-base-patch32"
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[run] visual embeddings for {len(frame_rows)} cached frames on {device}", flush=True)
    model = CLIPModel.from_pretrained(model_id, local_files_only=True).to(device)
    processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)

    chunks: list[np.ndarray] = []
    for offset in range(0, len(frame_rows), batch_size):
        batch = frame_rows[offset:offset + batch_size]
        images = []
        for row in batch:
            with Image.open(row["frame_path"]) as img:
                images.append(img.convert("RGB").copy())
        inputs = processor(images=images, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(device)
        with torch.inference_mode():
            features = model.get_image_features(pixel_values=pixel_values)
        arr = features.detach().cpu().numpy().astype(np.float32)
        chunks.append(_norm_rows(arr))
        if offset == 0 or (offset // batch_size) % 25 == 0:
            print(f"  visual frames {min(offset + len(batch), len(frame_rows))}/{len(frame_rows)}", flush=True)

    matrix = np.vstack(chunks) if chunks else np.empty((0, 512), dtype=np.float32)
    np.save(npy_path, matrix)
    meta_path.write_text(json.dumps({"signature": signature}, indent=2), encoding="utf-8")
    return matrix


def _encode_clip_queries(texts: list[str]) -> np.ndarray:
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise RuntimeError("Visual matching requires torch and transformers") from exc

    model_id = "openai/clip-vit-base-patch32"
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = CLIPModel.from_pretrained(model_id, local_files_only=True).to(device)
    processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
    inputs = processor(text=[f"Minecraft gameplay footage showing {t}" for t in texts], return_tensors="pt", padding=True)
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)
    with torch.inference_mode():
        features = model.get_text_features(input_ids=input_ids, attention_mask=attention_mask)
    return _norm_rows(features.detach().cpu().numpy().astype(np.float32))


def build_voiceover_matches(
    project_root: str | Path,
    voiceover_json: str | Path,
    index_json: str | Path,
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    voiceover = json.loads(Path(voiceover_json).expanduser().resolve().read_text(encoding="utf-8"))
    index = json.loads(Path(index_json).expanduser().resolve().read_text(encoding="utf-8"))

    beats = build_intro_beats(voiceover["segments"], pause_gap=0.75, max_duration=9.0)
    videos = [v for v in index["videos"] if not v.get("error")]

    specific = _specific_candidates(videos)
    beat_texts = [b.text for b in beats]

    specific_matrix = np.empty((0, 384), dtype=np.float32)
    beat_semantic = np.empty((len(beats), 384), dtype=np.float32)
    if specific:
        combined = embed_texts(beat_texts + [
            f"{row['relative_path']}. {row['text']}" for row in specific
        ])
        beat_semantic = np.asarray(combined[:len(beats)], dtype=np.float32)
        specific_matrix = np.asarray(combined[len(beats):], dtype=np.float32)

    frame_rows: list[dict[str, Any]] = []
    duration_by_path: dict[str, float] = {}
    for video in videos:
        duration_by_path[video["path"]] = float((video.get("probe") or {}).get("duration") or 0.0)
        for frame in video.get("frames", []):
            frame_path = Path(frame["path"])
            if frame_path.exists():
                frame_rows.append({
                    "path": video["path"],
                    "relative_path": video["relative_path"],
                    "category": video["category"],
                    "time": float(frame["time"]),
                    "frame_path": str(frame_path),
                })

    image_matrix = _load_or_build_clip_embeddings(root, frame_rows)
    query_matrix = _encode_clip_queries(beat_texts)
    visual_scores = query_matrix @ image_matrix.T if len(frame_rows) else np.empty((len(beats), 0))

    output_beats = []
    last_used: dict[str, list[tuple[float, float]]] = {}

    for beat_index, beat in enumerate(beats):
        candidates: list[dict[str, Any]] = []

        if specific:
            semantic_scores = specific_matrix @ beat_semantic[beat_index]
            best_indices = np.argsort(semantic_scores)[::-1][: min(30, len(specific))]
            for idx in best_indices:
                row = specific[int(idx)]
                semantic = float(semantic_scores[int(idx)])
                route = _topic_boost(beat.text, row["relative_path"])
                score = min(1.0, 0.76 * semantic + route)
                candidates.append({
                    "source": row["path"],
                    "relative_path": row["relative_path"],
                    "source_start": round(row["start"], 3),
                    "source_end": round(row["end"], 3),
                    "evidence": "specific-transcript",
                    "source_transcript": row["text"],
                    "score": score,
                    "reason": f"specific source transcript similarity={semantic:.3f}; topic boost={route:.2f}",
                })

        if len(frame_rows):
            row_scores = visual_scores[beat_index]
            best_frames = np.argsort(row_scores)[::-1][: min(60, len(frame_rows))]
            for idx in best_frames:
                row = frame_rows[int(idx)]
                raw = float(row_scores[int(idx)])
                route = _topic_boost(beat.text, row["relative_path"])
                # CLIP cosine is useful for ordering, but is not a calibrated probability.
                visual = max(0.0, min(1.0, (raw + 0.1) / 0.55))
                category_bonus = 0.06 if row["category"] in {"fit", "rusher"} else 0.0
                score = min(1.0, 0.72 * visual + route + category_bonus)
                start, end = _clip_range(
                    row["time"],
                    beat.end - beat.start,
                    duration_by_path.get(row["path"], row["time"] + 8.0),
                )
                candidates.append({
                    "source": row["path"],
                    "relative_path": row["relative_path"],
                    "source_start": start,
                    "source_end": end,
                    "evidence": "visual-frame",
                    "frame_time": round(row["time"], 3),
                    "frame_path": row["frame_path"],
                    "score": score,
                    "reason": f"visual CLIP similarity={raw:.3f}; topic boost={route:.2f}",
                })

        candidates.sort(key=lambda item: item["score"], reverse=True)

        chosen = None
        alternates = []
        seen = set()
        for item in candidates:
            key = (item["source"], round(item["source_start"], 1), item["evidence"])
            if key in seen:
                continue
            seen.add(key)
            overlaps = any(
                max(item["source_start"], a) < min(item["source_end"], b)
                for a, b in last_used.get(item["source"], [])
            )
            adjusted = dict(item)
            if overlaps:
                adjusted["score"] *= 0.90
                adjusted["reason"] += "; overlap penalty"
            if chosen is None:
                chosen = adjusted
            elif len(alternates) < top_k - 1:
                alternates.append(adjusted)
            if chosen is not None and len(alternates) >= top_k - 1:
                break

        if chosen is None:
            raise RuntimeError(f"No candidate found for beat {beat.id}")

        last_used.setdefault(chosen["source"], []).append((chosen["source_start"], chosen["source_end"]))
        chosen["confidence"] = _confidence(chosen["score"], evidence=chosen["evidence"])
        chosen["match_type"] = (
            "literal/contextual candidate"
            if chosen["evidence"] == "specific-transcript"
            else ("contextual visual candidate" if chosen["relative_path"].lower().startswith(("fit/", "rusher/")) else "generic visual candidate")
        )

        output_beats.append({
            "id": beat.id,
            "record_start": round(beat.start, 3),
            "record_end": round(beat.end, 3),
            "text": beat.text,
            "selected": chosen,
            "alternates": alternates,
        })

    payload = {
        "voiceover_source": voiceover.get("source"),
        "voiceover_duration": voiceover.get("duration"),
        "clips_root": index.get("clips_root"),
        "beat_count": len(output_beats),
        "warning": "Candidate confidence is heuristic. Specific transcript evidence is stronger than CLIP-only visual similarity; review low-confidence/generic candidates before Resolve placement.",
        "beats": output_beats,
    }
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    output_path = reports / "fitmc-match-candidates.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
