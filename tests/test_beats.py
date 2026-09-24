from intro_footage_matcher.beats import build_intro_beats, classify_editorial_roles


def test_punctuation_splits_meaningful_intro_beats():
    segments = [
        {"start": 0.0, "end": 2.0, "text": "Things started pretty well."},
        {"start": 2.1, "end": 5.0, "text": "But everything quickly fell apart."},
    ]
    beats = build_intro_beats(segments)
    assert [beat.text for beat in beats] == [
        "Things started pretty well.",
        "But everything quickly fell apart.",
    ]
    assert "success" in beats[0].roles
    assert "setback" in beats[1].roles


def test_long_pause_splits_without_punctuation():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "We bought one item"},
        {"start": 2.2, "end": 3.0, "text": "the challenge begins"},
    ]
    beats = build_intro_beats(segments, pause_gap=0.8)
    assert len(beats) == 2


def test_max_duration_splits_at_segment_boundary():
    segments = [
        {"start": 0.0, "end": 4.0, "text": "First thought"},
        {"start": 4.1, "end": 8.0, "text": "second thought"},
        {"start": 8.1, "end": 12.0, "text": "third thought"},
    ]
    beats = build_intro_beats(segments, max_duration=8.0)
    assert [(beat.start, beat.end) for beat in beats] == [(0.0, 8.0), (8.1, 12.0)]


def test_empty_or_whitespace_segments_do_not_create_beats():
    assert build_intro_beats([]) == []
    assert build_intro_beats([{"start": 0.0, "end": 1.0, "text": "  "}]) == []


def test_editorial_roles_cover_comeback_clutch_and_victory():
    roles = classify_editorial_roles("Then we made a huge comeback and clutched the win.")
    assert set(("comeback", "clutch", "victory")).issubset(roles)


def test_failure_language_maps_to_failure_and_defeat():
    roles = classify_editorial_roles("I made a terrible mistake and we lost the match.")
    assert "failure" in roles
    assert "defeat" in roles


def test_negative_money_language_is_not_misclassified_as_success():
    roles = classify_editorial_roles("But money is very easy to lose and then you run out.")
    assert "setback" in roles
    assert "failure" in roles
    assert "success" not in roles
    assert "confidence" not in roles


def test_crash_and_teammate_damage_are_failure_beats():
    roles = classify_editorial_roles("You crash a helicopter and kill all your teammates.")
    assert "failure" in roles
    assert "danger" in roles


def test_contrast_and_action_transition_start_new_beats():
    segments = [
        {"start": 0.0, "end": 3.0, "text": "If you shoot a teammate it costs money"},
        {"start": 3.0, "end": 6.0, "text": "But money is hard to come by"},
        {"start": 6.0, "end": 9.0, "text": "So let's head to the vendor"},
    ]
    beats = build_intro_beats(segments)
    assert [beat.start for beat in beats] == [0.0, 3.0, 6.0]


def test_stealing_kits_is_setup_even_when_victory_is_the_goal():
    roles = classify_editorial_roles("I will steal other people's kits and hopefully get a win.")
    assert "setup" in roles
    assert "victory" in roles


def test_word_timestamps_split_long_single_segment_at_internal_pause():
    segments = [{
        "start": 0.0,
        "end": 30.0,
        "text": "First sentence. Second sentence.",
        "words": [
            {"start": 0.0, "end": 1.0, "text": " First"},
            {"start": 1.0, "end": 2.0, "text": " sentence."},
            {"start": 20.0, "end": 21.0, "text": " Second"},
            {"start": 21.0, "end": 22.0, "text": " sentence."},
        ],
    }]
    beats = build_intro_beats(segments, pause_gap=0.8, max_duration=15.0)
    assert [beat.text for beat in beats] == ["First sentence.", "Second sentence."]
    assert all(beat.end - beat.start <= 15.0 for beat in beats)


def test_long_segment_without_words_has_bounded_fallback():
    beats = build_intro_beats([{"start": 0.0, "end": 31.0, "text": "one two three four five six"}], max_duration=15.0)
    assert len(beats) == 3
    assert all(beat.end - beat.start <= 15.0 for beat in beats)
