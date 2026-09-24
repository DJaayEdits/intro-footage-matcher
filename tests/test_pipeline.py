from pathlib import Path

from intro_footage_matcher.cache import StageCache
from intro_footage_matcher.pipeline import build_stage_signatures, cached_stage


def test_cached_stage_reuses_result_until_inputs_change(tmp_path: Path):
    cache = StageCache(tmp_path / "cache")
    counter = tmp_path / "calls.txt"

    def produce():
        count = int(counter.read_text() or "0") if counter.exists() else 0
        counter.write_text(str(count + 1))
        return {"value": count + 1}

    assert cached_stage(cache, "demo", {"source": "a"}, produce) == {"value": 1}
    assert cached_stage(cache, "demo", {"source": "a"}, produce) == {"value": 1}
    assert cached_stage(cache, "demo", {"source": "b"}, produce) == {"value": 2}
    assert counter.read_text() == "2"


def test_force_recomputes_stage_even_when_inputs_match(tmp_path: Path):
    cache = StageCache(tmp_path / "cache")
    values = iter(({"value": 1}, {"value": 2}))
    assert cached_stage(cache, "demo", {"source": "a"}, lambda: next(values)) == {"value": 1}
    assert cached_stage(cache, "demo", {"source": "a"}, lambda: next(values), force=True) == {"value": 2}


def test_transcription_model_change_invalidates_all_transcript_consumers_only():
    sources = {"intro": "intro-fp", "gameplay": "game-fp"}
    first = build_stage_signatures(sources, "model-a", sample_fps=2.0, max_visual_frames=1000)
    second = build_stage_signatures(sources, "model-b", sample_fps=2.0, max_visual_frames=1000)
    assert first["frames"] == second["frames"]
    assert first["signals"] == second["signals"]
    for stage in ("transcript", "beats", "vision", "moments", "embeddings", "matches"):
        assert first[stage] != second[stage]


def test_sampling_change_invalidates_frame_consumers_not_transcript_consumers():
    sources = {"intro": "intro-fp", "gameplay": "game-fp"}
    first = build_stage_signatures(sources, "model-a", sample_fps=1.0, max_visual_frames=500)
    second = build_stage_signatures(sources, "model-a", sample_fps=2.0, max_visual_frames=1000)
    assert first["transcript"] == second["transcript"]
    assert first["beats"] == second["beats"]
    for stage in ("frames", "signals", "vision", "moments", "embeddings", "matches"):
        assert first[stage] != second[stage]


def test_editorial_policy_change_invalidates_matches_only():
    sources = {"intro": "intro-fp", "gameplay": "game-fp"}
    first = build_stage_signatures(
        sources, "model-a", sample_fps=2.0, max_visual_frames=1000,
        editorial_policy_version=6,
    )
    second = build_stage_signatures(
        sources, "model-a", sample_fps=2.0, max_visual_frames=1000,
        editorial_policy_version=7,
    )

    assert first["embeddings"] == second["embeddings"]
    assert first["matches"] != second["matches"]
