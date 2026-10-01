from __future__ import annotations

import re
import math
from collections.abc import Iterable
from typing import Any

from .models import Beat


ROLE_TERMS: dict[str, tuple[str, ...]] = {
    "setup": ("start", "begin", "challenge", "goal", "plan", "first", "one item", "loadout", "buy", "spending", "weapon vendor", "stay alive", "steal", " kit", "make money"),
    "success": ("success", "worked", "well", "score", "lead", "good", "easy", "dominat"),
    "confidence": ("confident", "easy", "had this", "no problem", "feeling good", "sure"),
    "escalation": ("then", "but", "suddenly", "worse", "more", "kept", "quickly"),
    "danger": ("danger", "close", "almost", "low health", "surrounded", "threat", "risky", "sniped", "dying", "exploding", "crash", "kill all your teammates"),
    "setback": ("setback", "fell apart", "wrong", "problem", "behind", "comeback against", "lost lead", "don't have", "run out", "lose", "hard to come by", "there goes", "cost"),
    "failure": ("fail", "mistake", "missed", "died", "dying", "death", "terrible", "threw", "lose", "run out", "exploding", "crash", "kill all your teammates", "shoot a teammate"),
    "comeback": ("comeback", "turned it around", "recovered", "back in", "return"),
    "clutch": ("clutch", "last second", "final moment", "one versus", "1v"),
    "victory": ("victory", "won", " win", "champion", "beat them"),
    "defeat": ("defeat", "lost", "loss", "eliminated", "game over"),
    "funny": ("funny", "hilarious", "laughed", "ridiculous", "what was that"),
    "reaction": ("reaction", "couldn't believe", "shocked", "yelled", "screamed", "no way"),
}


def classify_editorial_roles(text: str) -> dict[str, float]:
    normalized = f" {re.sub(r'\s+', ' ', text.lower()).strip()} "
    roles: dict[str, float] = {}
    for role, terms in ROLE_TERMS.items():
        hits = sum(term in normalized for term in terms)
        if hits:
            roles[role] = min(1.0, 0.62 + 0.14 * (hits - 1))
    negative_context = any(phrase in normalized for phrase in (
        " easy to lose", " run out", " don't have", " hard to come by", " crash", " dying", " exploding", " sniped",
    ))
    if negative_context:
        roles.pop("success", None)
        roles.pop("confidence", None)
    if not roles:
        roles["setup"] = 0.35
    return roles


def _split_segment(
    item: dict[str, Any],
    *,
    pause_gap: float,
    max_duration: float,
) -> list[dict[str, Any]]:
    words = [
        {"start": float(word["start"]), "end": float(word["end"]), "text": str(word.get("text", ""))}
        for word in item.get("words", [])
        if str(word.get("text", "")).strip()
    ]
    if words:
        units: list[dict[str, Any]] = []
        current: list[dict[str, Any]] = []
        for word in words:
            if current and (
                word["start"] - current[-1]["end"] > pause_gap
                or word["end"] - current[0]["start"] > max_duration
            ):
                units.append({
                    "start": current[0]["start"], "end": current[-1]["end"],
                    "text": " ".join(part["text"] for part in current).strip(),
                })
                current = []
            current.append(word)
            if re.search(r"[.!?][\"')\]]?$", word["text"].strip()):
                units.append({
                    "start": current[0]["start"], "end": current[-1]["end"],
                    "text": "".join(part["text"] for part in current).strip(),
                })
                current = []
        if current:
            units.append({
                "start": current[0]["start"], "end": current[-1]["end"],
                "text": "".join(part["text"] for part in current).strip(),
            })
        return units

    start, end = float(item["start"]), float(item["end"])
    text = str(item.get("text", "")).strip()
    if not text:
        return []
    chunk_count = max(1, math.ceil((end - start) / max_duration))
    if chunk_count == 1:
        return [{"start": start, "end": end, "text": text}]
    tokens = text.split()
    units = []
    for index in range(chunk_count):
        token_start = round(index * len(tokens) / chunk_count)
        token_end = round((index + 1) * len(tokens) / chunk_count)
        time_start = start + (end - start) * index / chunk_count
        time_end = start + (end - start) * (index + 1) / chunk_count
        chunk_text = " ".join(tokens[token_start:token_end]).strip()
        if chunk_text:
            units.append({"start": time_start, "end": time_end, "text": chunk_text})
    return units


def build_intro_beats(
    segments: Iterable[dict[str, Any]],
    *,
    pause_gap: float = 0.9,
    max_duration: float = 15.0,
) -> list[Beat]:
    cleaned = [
        unit
        for item in segments
        for unit in _split_segment(item, pause_gap=pause_gap, max_duration=max_duration)
        if unit["text"]
    ]
    if not cleaned:
        return []

    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for segment in cleaned:
        if current:
            gap = segment["start"] - current[-1]["end"]
            proposed_duration = segment["end"] - current[0]["start"]
            transition = bool(re.match(r"(?i)^(but\b|however\b|so let['’]?s\b)", segment["text"]))
            if gap > pause_gap or proposed_duration > max_duration or transition:
                groups.append(current)
                current = []
        current.append(segment)
        if re.search(r"[.!?][\"')\]]?$", segment["text"]):
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    beats: list[Beat] = []
    for index, group in enumerate(groups, start=1):
        text = " ".join(item["text"] for item in group)
        beats.append(Beat(
            id=f"b{index:03d}",
            start=group[0]["start"],
            end=group[-1]["end"],
            text=text,
            roles=classify_editorial_roles(text),
        ))
    return beats
