import pytest

from intro_footage_matcher.resolve_assembly import build_edit_plan, require_exact_frame_rate


def test_edit_plan_covers_intro_with_video_only_choices_at_beat_boundaries():
    report = {
        "sources": {"intro": "/intro.mp4", "gameplay": "/game.mp4"},
        "results": [
            {
                "beat": {"id": "b1", "start": 0.0, "end": 2.0, "text": "Setup"},
                "recommendations": [
                    {"start": 100.0, "end": 110.0, "start_timecode": "00:01:40.000"}
                ],
            },
            {
                "beat": {"id": "b2", "start": 2.5, "end": 5.0, "text": "Setback"},
                "recommendations": [
                    {"start": 200.0, "end": 210.0, "start_timecode": "00:03:20.000"},
                    {"start": 300.0, "end": 310.0, "start_timecode": "00:05:00.000"},
                ],
            },
        ],
    }

    plan = build_edit_plan(report, fps=60, intro_duration=5.5, choices={1: 1})

    assert plan == [
        {
            "beat_id": "b1",
            "beat_text": "Setup",
            "record_start": 0,
            "duration": 150,
            "source_start": 6000,
            "source_timecode": "00:01:40.000",
        },
        {
            "beat_id": "b2",
            "beat_text": "Setback",
            "record_start": 150,
            "duration": 180,
            "source_start": 18000,
            "source_timecode": "00:05:00.000",
        },
    ]


def test_edit_plan_rejects_recommendation_too_short_for_assigned_slot():
    report = {
        "results": [{
            "beat": {"id": "b1", "start": 0.0, "end": 3.0, "text": "Beat"},
            "recommendations": [{"start": 10.0, "end": 11.0, "start_timecode": "00:00:10.000"}],
        }]
    }

    try:
        build_edit_plan(report, fps=60, intro_duration=3.0)
    except ValueError as exc:
        assert "shorter than its timeline slot" in str(exc)
    else:
        raise AssertionError("expected short recommendation to be rejected")


def test_exact_frame_rate_rejects_5994_project_or_source_as_60():
    assert require_exact_frame_rate("60", "60/1", "60/1") == 60

    with pytest.raises(ValueError, match="project frame rate"):
        require_exact_frame_rate("59.94", "60/1", "60/1")
    with pytest.raises(ValueError, match="source frame rates"):
        require_exact_frame_rate("60", "60000/1001", "60/1")


def test_edit_plan_uses_a_unique_backup_instead_of_repeating_source_footage():
    report = {
        "results": [
            {
                "beat": {"id": "b1", "start": 0.0, "end": 2.0, "text": "First"},
                "recommendations": [
                    {"start": 100.0, "end": 110.0, "start_timecode": "00:01:40.000"},
                ],
            },
            {
                "beat": {"id": "b2", "start": 2.0, "end": 4.0, "text": "Second"},
                "recommendations": [
                    {"start": 100.0, "end": 110.0, "start_timecode": "00:01:40.000"},
                    {"start": 200.0, "end": 210.0, "start_timecode": "00:03:20.000"},
                ],
            },
        ]
    }

    plan = build_edit_plan(report, fps=60, intro_duration=4.0)

    assert [edit["source_start"] for edit in plan] == [6000, 12000]
    assert plan[0]["record_start"] + plan[0]["duration"] == plan[1]["record_start"]
