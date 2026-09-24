from intro_footage_matcher.moments import build_moments, compose_description
from intro_footage_matcher.signals import select_representatives


def test_representative_selection_is_bounded_and_keeps_time_coverage():
    frames = [
        {"time": float(i), "motion": 0.1, "change": 0.1, "path": f"{i}.jpg"}
        for i in range(20)
    ]
    frames[7]["motion"] = 1.0
    frames[15]["change"] = 1.0
    chosen = select_representatives(frames, [], [], max_frames=5)
    assert len(chosen) <= 5
    assert {7.0, 15.0}.issubset({item["time"] for item in chosen})
    assert min(item["time"] for item in chosen) <= 2.0
    assert max(item["time"] for item in chosen) >= 17.0


def test_visual_only_event_creates_a_moment():
    frames = [
        {"time": 30.0, "motion": 0.95, "change": 0.9, "path": "event.jpg", "visual_labels": {"intense combat": 0.82, "danger": 0.71}},
    ]
    moments = build_moments(frames, [], [], duration=60.0)
    assert len(moments) == 1
    assert moments[0].start == 26.0
    assert moments[0].end == 36.0
    assert "intense combat" in moments[0].description
    assert moments[0].transcript == ""


def test_overlapping_signal_windows_merge_and_clamp_to_source():
    frames = [
        {"time": 1.0, "motion": 1.0, "change": 1.0, "path": "a.jpg", "visual_labels": {"victory": 0.8}},
        {"time": 3.0, "motion": 0.9, "change": 0.9, "path": "b.jpg", "visual_labels": {"celebration": 0.7}},
    ]
    audio = [{"time": 2.0, "rms": 1.0, "peak": 1.0}]
    transcript = [{"start": 0.5, "end": 4.0, "text": "We won that fight!"}]
    moments = build_moments(frames, audio, transcript, duration=8.0)
    assert len(moments) == 1
    assert moments[0].start == 0.0
    assert moments[0].end == 8.0


def test_description_combines_transcript_and_visual_evidence():
    description = compose_description(
        "No way, we got it!",
        {"clutch win": 0.91, "scoreboard": 0.75},
    )
    assert description == 'Dialogue: "No way, we got it!"; visuals: clutch win, scoreboard.'


def test_outcome_bearing_spoken_event_has_story_value_without_visual_spike():
    transcript = [{"start": 10.0, "end": 12.0, "text": "A helicopter just crashed."}]
    moments = build_moments([], [], transcript, duration=30.0)
    assert moments[0].story_value >= 35.0
