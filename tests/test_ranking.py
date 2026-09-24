from intro_footage_matcher.models import Beat, Moment
from intro_footage_matcher.ranking import rank_matches


def test_semantically_correct_moment_beats_unrelated_high_stakes_moment():
    beat = Beat("b1", 0, 2, "Things started well.", {"success": 0.9})
    moments = [
        Moment("m1", 10, 18, "early successful play", {"success": 0.8}, 55),
        Moment("m2", 30, 40, "major defeat", {"defeat": 0.9}, 100),
    ]
    results = rank_matches([beat], moments, [[1.0, 0.0]], [[0.95, 0.05], [0.0, 1.0]], top_k=2)
    assert [item.moment_id for item in results[beat.id]] == ["m1", "m2"]


def test_story_value_breaks_equal_semantic_matches():
    beat = Beat("b1", 0, 2, "The danger escalated.", {"danger": 0.8, "escalation": 0.7})
    moments = [
        Moment("m1", 10, 18, "danger", {"danger": 0.8}, 40),
        Moment("m2", 30, 38, "danger", {"danger": 0.8}, 85),
    ]
    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0]], top_k=2)
    assert results[beat.id][0].moment_id == "m2"


def test_overlapping_candidates_are_suppressed():
    beat = Beat("b1", 0, 2, "We won.", {"victory": 1.0})
    moments = [
        Moment("m1", 10, 20, "win", {"victory": 1.0}, 90),
        Moment("m2", 11, 21, "same win", {"victory": 1.0}, 89),
        Moment("m3", 40, 50, "other win", {"victory": 0.8}, 70),
    ]
    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0], [0.9]], top_k=2)
    assert [item.moment_id for item in results[beat.id]] == ["m1", "m3"]


def test_visual_only_role_evidence_contributes_to_match_score():
    beat = Beat("b1", 0, 2, "We finally won.", {"victory": 1.0})
    visual = Moment(
        "m1", 10, 18, "visuals: victory or celebration", {}, 75,
        transcript="", visual_labels={"victory or celebration": 0.9},
    )
    unrelated = Moment("m2", 30, 38, "quiet travel", {}, 75, transcript="")
    results = rank_matches([beat], [visual, unrelated], [[1.0]], [[0.7], [0.7]], top_k=2)
    assert results[beat.id][0].moment_id == "m1"
    assert results[beat.id][0].match_score > results[beat.id][1].match_score


def test_adjacent_windows_with_repeated_transcript_are_suppressed():
    beat = Beat("b1", 0, 2, "Money", {"setup": 1.0})
    moments = [
        Moment("m1", 100, 110, "money moment", {"setup": 1.0}, 80, transcript="look at all that money"),
        Moment("m2", 111, 121, "same money moment", {"setup": 1.0}, 79, transcript="look at all that money"),
        Moment("m3", 200, 210, "other money moment", {"setup": 0.8}, 70, transcript="we need cash"),
    ]
    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0], [0.9]], top_k=2)
    assert [item.moment_id for item in results[beat.id]] == ["m1", "m3"]


def test_specific_event_concept_breaks_equal_semantic_tie():
    beat = Beat("b1", 0, 2, "The helicopter crashed and exploded.", {"failure": 1.0})
    moments = [
        Moment("m1", 10, 20, "A helicopter just crashed.", {"failure": 1.0}, 60, transcript="helicopter crashed"),
        Moment("m2", 40, 50, "Everybody is dying.", {"failure": 1.0}, 60, transcript="everybody died"),
    ]
    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0]], top_k=2)
    assert results[beat.id][0].moment_id == "m1"
    assert "aircraft event" in results[beat.id][0].why.lower()


def test_plural_kits_maps_to_weapon_context():
    beat = Beat("b1", 0, 2, "I will steal other people's kits.", {"setup": 1.0})
    moments = [
        Moment("m1", 10, 20, "steal their weapons", {"setup": 1.0}, 50, transcript="steal those weapons"),
        Moment("m2", 40, 50, "walk around", {"setup": 1.0}, 50, transcript="walking around"),
    ]
    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0]], top_k=2)
    assert results[beat.id][0].moment_id == "m1"


def test_any_temporal_overlap_is_suppressed_but_touching_is_allowed():
    beat = Beat("b1", 0, 2, "danger", {"danger": 1.0})
    moments = [
        Moment("m1", 0, 10, "danger one", {"danger": 1.0}, 90),
        Moment("m2", 8, 18, "danger overlap", {"danger": 1.0}, 89),
        Moment("m3", 10, 20, "danger touching", {"danger": 1.0}, 88),
    ]
    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0], [1.0]], top_k=2)
    assert [item.moment_id for item in results[beat.id]] == ["m1", "m3"]


def test_visible_death_action_beats_a_stronger_dialogue_only_match():
    beat = Beat("b1", 0, 2, "You keep dying.", {"defeat": 1.0})
    moments = [
        Moment(
            "m_visual", 10, 14,
            "visuals: player is shot, falls down, and the respawn screen appears",
            {"defeat": 1.0}, 60, transcript="",
            visual_labels={"death or respawn screen": 0.95},
        ),
        Moment(
            "m_dialogue", 30, 34, "visuals: ordinary running gameplay",
            {"defeat": 1.0}, 60, transcript="I'm dead again",
            visual_labels={"quiet setup or travel": 0.9},
        ),
    ]

    results = rank_matches([beat], moments, [[1.0, 0.0]], [[0.60, 0.80], [1.0, 0.0]], top_k=2)

    assert results[beat.id][0].moment_id == "m_visual"
    assert "literal on-screen action" in results[beat.id][0].why.lower()


def test_sniper_reaction_audio_beats_unrelated_generic_gameplay():
    beat = Beat("b1", 0, 2, "You're getting sniped from 700 meters.", {"danger": 1.0})
    moments = [
        Moment(
            "m_generic", 10, 14, "visuals: clean ordinary gameplay",
            {"danger": 1.0}, 70, transcript="moving to the next point",
            visual_labels={"quiet setup or travel": 0.9},
        ),
        Moment(
            "m_reaction", 30, 34, "visuals: player takes distant fire",
            {"danger": 1.0}, 70,
            transcript="Oh snap, where did that shot come from? We're getting shot at.",
        ),
    ]

    results = rank_matches([beat], moments, [[1.0]], [[1.0], [1.0]], top_k=2)

    assert results[beat.id][0].moment_id == "m_reaction"
    assert "contextual source audio" in results[beat.id][0].why.lower()
