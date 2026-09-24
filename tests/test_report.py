from pathlib import Path

from intro_footage_matcher.models import Beat, Match, Moment
from intro_footage_matcher.report import build_report_data, render_report


def _fixture():
    beat = Beat("b1", 0, 3, "Things <started> well.", {"success": 0.9})
    moments = [
        Moment(f"m{i}", i * 10.0, i * 10.0 + 8, f"Play {i} & score", {"success": 0.8}, 70 + i)
        for i in range(1, 5)
    ]
    matches = {
        "b1": [
            Match("b1", moment.id, 90 - i, moment.story_value, f"Reason {i} <good>", 80 - i)
            for i, moment in enumerate(moments[:3])
        ]
    }
    return [beat], moments, matches


def test_report_data_contains_three_ranked_recommendations():
    beats, moments, matches = _fixture()
    data = build_report_data(beats, moments, matches, {"gameplay": "/tmp/game play.mp4"})
    recommendations = data["results"][0]["recommendations"]
    assert [item["rank"] for item in recommendations] == [1, 2, 3]
    assert recommendations[0]["start_timecode"] == "00:00:10.000"


def test_html_escapes_user_derived_text(tmp_path: Path):
    beats, moments, matches = _fixture()
    data = build_report_data(beats, moments, matches, {"gameplay": "/tmp/game play.mp4"})
    output = render_report(data, tmp_path / "index.html")
    html = output.read_text()
    assert "Things &lt;started&gt; well." in html
    assert "Reason 0 &lt;good&gt;" in html
    assert "Things <started> well." not in html
