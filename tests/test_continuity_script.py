import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "create_continuous_context_timeline.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("continuity_timeline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_continuity_timeline_has_no_visual_gaps_or_repeated_source_ranges():
    module = load_script_module()
    edits = module.VIDEO_EDITS

    assert edits[0][0] == 0.0
    assert edits[-1][1] == module.INTRO_DURATION
    assert all(left[1] == right[0] for left, right in zip(edits, edits[1:]))

    source_ranges = [
        (source_in, source_in + record_out - record_in)
        for record_in, record_out, source_in, *_ in edits
    ]
    for index, (start, end) in enumerate(source_ranges):
        for other_start, other_end in source_ranges[index + 1:]:
            assert end <= other_start or start >= other_end


def test_feedback_revision_uses_late_money_loss_teammate_action_and_fresh_scenery():
    module = load_script_module()
    edits_by_timeline_in = {edit[0]: edit for edit in module.VIDEO_EDITS}

    money_loss = edits_by_timeline_in[22.840]
    teammate_penalty = edits_by_timeline_in[28.500]
    money_hard = edits_by_timeline_in[32.280]

    assert module.TIMELINE_NAME == "IFM V0.4 - Refined Context"
    assert money_loss[2] == 4371.000
    assert "-$4,430" in money_loss[3]
    assert teammate_penalty[2] == 1527.800
    assert "following a teammate" in teammate_penalty[3].lower()
    assert money_hard[2] == 3809.600
    assert "industrial" in money_hard[4].lower()
