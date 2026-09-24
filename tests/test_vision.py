from intro_footage_matcher.vision import calibrate_label_scores


def test_calibration_promotes_event_specific_label_over_global_bias():
    rows = [
        {"funny": 0.60, "victory": 0.10},
        {"funny": 0.60, "victory": 0.10},
        {"funny": 0.61, "victory": 0.80},
    ]
    calibrated = calibrate_label_scores(rows, top_k=2)
    assert next(iter(calibrated[2])) == "victory"
    assert "victory" not in calibrated[0]
