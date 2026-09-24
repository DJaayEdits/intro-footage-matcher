from __future__ import annotations

import math
import re
from collections.abc import Sequence
from typing import Any

from .beats import classify_editorial_roles
from .models import Beat, Match, Moment


def embed_texts(texts: list[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> list[list[float]]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Semantic ranking requires sentence-transformers") from exc
    model = SentenceTransformer(model_name, local_files_only=True)
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=len(texts) > 50)
    return embeddings.tolist()


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions do not match")
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))


def _role_compatibility(beat_roles: dict[str, float], moment_roles: dict[str, float]) -> float:
    shared = set(beat_roles) & set(moment_roles)
    return max((min(beat_roles[role], moment_roles[role]) for role in shared), default=0.0)


def _visual_support(beat: Beat, moment: Moment) -> tuple[float, str | None]:
    best_score = 0.0
    best_label = None
    for label, confidence in moment.visual_labels.items():
        label_roles = classify_editorial_roles(label)
        compatibility = _role_compatibility(beat.roles, label_roles) * confidence
        if compatibility > best_score:
            best_score = compatibility
            best_label = label
    return min(1.0, best_score), best_label


def _concepts(text: str) -> set[str]:
    value = text.lower()
    concepts: set[str] = set()
    def has(pattern: str) -> bool:
        return bool(re.search(pattern, value))
    if has(r"money|cash|dollars?|\$|grand|brib|afford|\b500\b"):
        concepts.add("money/resources")
    if has(r"money|cash|dollars?|\$|grand|brib|afford") and has(r"lose|lost|run out|don't have|can't|cannot|cost|spent|gone"):
        concepts.add("resource loss")
    if has(r"helicopter|chopper|parachute"):
        concepts.add("aircraft event")
    if has(r"helicopter|chopper") and has(r"crash|explod|blow|died|down"):
        concepts.add("aircraft crash")
    if has(r"team ?mate|my team|your team"):
        concepts.add("teammate incident")
    if has(r"team ?mate") and has(r"shoot|kill|dead|died|crash"):
        concepts.add("teammate damage")
    if has(r"weapon|gun|loadout|\bkits?\b|vendor|ammo"):
        concepts.add("weapons/kits")
    if has(r"vehicle|helicopter|chopper") and has(r"buy|bought|purchase|vendor|select|spawn"):
        concepts.add("vehicle purchase")
    if has(r"weapon|gun|launcher") and has(r"buy|bought|purchase|vendor|catalog|brows"):
        concepts.add("weapon purchase")
    if has(r"med ?kit|medical kit") and has(r"buy|bought|purchase|vendor|catalog|brows"):
        concepts.add("medkit purchase")
    if has(r"snip|700 meters|long range"):
        concepts.add("sniper threat")
    if has(r"dying|died|dead|death|defeat|game over|lost"):
        concepts.add("death/defeat")
    if has(r"\bwin\b|won|victory|champion"):
        concepts.add("victory objective")
    if has(r"revive|defib|med ?kit|health|stay alive"):
        concepts.add("survival/medic")
    return concepts


def _visual_text(moment: Moment) -> str:
    """Return only evidence that is safe to treat as visible action."""
    description = moment.description.lower()
    if "visuals:" in description:
        description = description.rsplit("visuals:", 1)[1]
    elif moment.transcript:
        description = ""
    labels = " ".join(moment.visual_labels).lower()
    return f"{description} {labels}".strip()


def _literal_visual_support(beat_concepts: set[str], moment: Moment) -> bool:
    visual = _visual_text(moment)
    patterns = {
        "death/defeat": r"respawn|death screen|downed|player .*(?:shot|hit).*(?:fall|down)|falls? .*ground|red damage screen",
        "aircraft crash": r"(?:helicopter|chopper|aircraft).*(?:crash|explod|blow|burn|wreck)",
        "vehicle purchase": r"vehicle vendor|vehicle (?:purchase|selection)|select.*(?:vehicle|helicopter)|spawn.*(?:vehicle|helicopter)",
        "weapon purchase": r"weapon vendor|gun catalog|weapon catalog|buying (?:a )?(?:gun|weapon)",
        "medkit purchase": r"medical kit|med ?kit.*(?:vendor|price|purchase)",
        "survival/medic": r"reviv|med ?kit|medical kit|healing|downed teammate",
    }
    return any(
        concept in beat_concepts and re.search(pattern, visual)
        for concept, pattern in patterns.items()
    )


def _contextual_audio_support(beat_concepts: set[str], transcript: str) -> bool:
    audio = transcript.lower()
    if not audio.strip():
        return False
    if beat_concepts & _concepts(audio):
        return True
    if "sniper threat" in beat_concepts and re.search(
        r"where .*shot.*come from|where did .*shot|getting shot at|taking fire|shots? .*from|sniper",
        audio,
    ):
        return True
    return False


def _evidence_level(beat: Beat, moment: Moment) -> int:
    """Order candidates by editorial usefulness before numeric similarity.

    3 = literal visible action, 2 = contextual source audio, 1 = usable visual
    fallback, 0 = no concrete evidence.
    """
    beat_concepts = _concepts(beat.text)
    if _literal_visual_support(beat_concepts, moment):
        return 3
    if _contextual_audio_support(beat_concepts, moment.transcript):
        return 2
    if _visual_text(moment):
        return 1
    return 0


def _overlap_ratio(left: Moment, right: Moment) -> float:
    overlap = max(0.0, min(left.end, right.end) - max(left.start, right.start))
    shorter = min(left.end - left.start, right.end - right.start)
    return overlap / shorter if shorter > 0 else 0.0


def _near_duplicate(left: Moment, right: Moment) -> bool:
    if _overlap_ratio(left, right) > 0.0:
        return True
    left_words = set(left.transcript.lower().split())
    right_words = set(right.transcript.lower().split())
    union = left_words | right_words
    text_similarity = len(left_words & right_words) / len(union) if union else 0.0
    left_center = (left.start + left.end) / 2
    right_center = (right.start + right.end) / 2
    return abs(left_center - right_center) < 18.0 and text_similarity >= 0.50


def rank_matches(
    beats: list[Beat],
    moments: list[Moment],
    beat_embeddings: Sequence[Sequence[float]],
    moment_embeddings: Sequence[Sequence[float]],
    *,
    top_k: int = 3,
) -> dict[str, list[Match]]:
    if len(beats) != len(beat_embeddings) or len(moments) != len(moment_embeddings):
        raise ValueError("Every beat and moment must have one embedding")
    output: dict[str, list[Match]] = {}
    for beat, beat_embedding in zip(beats, beat_embeddings):
        candidates: list[tuple[Match, Moment, int]] = []
        for moment, moment_embedding in zip(moments, moment_embeddings):
            semantic = _cosine(beat_embedding, moment_embedding)
            role = _role_compatibility(beat.roles, moment.roles)
            visual, visual_label = _visual_support(beat, moment)
            beat_concepts = _concepts(beat.text)
            moment_concepts = _concepts(f"{moment.description} {moment.transcript}")
            shared_concepts = sorted(beat_concepts & moment_concepts)
            concept_support = len(shared_concepts) / len(beat_concepts) if beat_concepts else 0.0
            if set(shared_concepts) & {"aircraft crash", "resource loss", "teammate damage"}:
                concept_support = 1.0
            match_score = 100 * (0.55 * semantic + 0.25 * role + 0.10 * visual + 0.10 * concept_support)
            story_value = max(0.0, min(100.0, moment.story_value))
            rank_score = 0.75 * match_score + 0.25 * story_value

            reasons: list[str] = []
            shared_roles = sorted(set(beat.roles) & set(moment.roles))
            if shared_roles:
                reasons.append(f"shared story role: {', '.join(shared_roles)}")
            if visual_label:
                reasons.append(f"visual evidence: {visual_label}")
            if shared_concepts:
                reasons.append(f"event context: {', '.join(shared_concepts)}")
            if semantic >= 0.55:
                reasons.append("strong semantic connection")
            elif semantic >= 0.30:
                reasons.append("moderate semantic connection")
            if story_value >= 70:
                reasons.append("high-stakes moment")
            evidence_level = _evidence_level(beat, moment)
            if evidence_level == 3:
                reasons.insert(0, "literal on-screen action")
            elif evidence_level == 2:
                reasons.insert(0, "contextual source audio")
            elif evidence_level == 1 and not shared_concepts:
                reasons.append("generic gameplay fallback")
            if not reasons:
                reasons.append("best available contextual fit")

            candidates.append((Match(
                beat_id=beat.id,
                moment_id=moment.id,
                match_score=round(match_score, 1),
                story_value_score=round(story_value, 1),
                why="; ".join(reasons).capitalize() + ".",
                rank_score=round(rank_score, 2),
            ), moment, evidence_level))

        chosen: list[tuple[Match, Moment, int]] = []
        for candidate in sorted(
            candidates,
            key=lambda item: (item[2], item[0].rank_score),
            reverse=True,
        ):
            if all(not _near_duplicate(candidate[1], existing[1]) for existing in chosen):
                chosen.append(candidate)
                if len(chosen) >= top_k:
                    break
        output[beat.id] = [item[0] for item in chosen]
    return output


def build_embeddings(beats: list[Beat], moments: list[Moment]) -> tuple[list[list[float]], list[list[float]]]:
    beat_texts = [f"{beat.text} Story roles: {', '.join(beat.roles)}." for beat in beats]
    moment_texts = [
        f"{moment.description} Story roles: {', '.join(moment.roles)}. Visual evidence: {', '.join(moment.visual_labels)}."
        for moment in moments
    ]
    combined = embed_texts(beat_texts + moment_texts)
    return combined[:len(beats)], combined[len(beats):]
