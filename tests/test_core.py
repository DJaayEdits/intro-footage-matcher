import json
import os
from pathlib import Path

from intro_footage_matcher.cache import StageCache, source_fingerprint
from intro_footage_matcher.models import Beat, Match, Moment
from intro_footage_matcher.timecode import format_timecode


def test_format_timecode_keeps_millisecond_precision():
    assert format_timecode(3723.4567) == "01:02:03.457"


def test_format_timecode_clamps_negative_values():
    assert format_timecode(-1.0) == "00:00:00.000"


def test_source_fingerprint_changes_when_file_changes(tmp_path: Path):
    source = tmp_path / "clip with spaces.mp4"
    source.write_bytes(b"first")
    first = source_fingerprint(source)
    source.write_bytes(b"second-version")
    os.utime(source, ns=(source.stat().st_atime_ns, source.stat().st_mtime_ns + 1))
    assert source_fingerprint(source) != first


def test_stage_cache_reuses_only_matching_inputs(tmp_path: Path):
    cache = StageCache(tmp_path)
    cache.write("beats", {"source": "abc", "settings": {"gap": 1.0}}, {"items": [1]})
    assert cache.load("beats", {"source": "abc", "settings": {"gap": 1.0}}) == {"items": [1]}
    assert cache.load("beats", {"source": "def", "settings": {"gap": 1.0}}) is None


def test_data_models_serialize_complete_match():
    beat = Beat("b1", 0.0, 3.0, "Things started well.", {"success": 0.9})
    moment = Moment("m1", 10.0, 18.0, "Successful early play", {"success": 0.8}, 70.0)
    match = Match(beat.id, moment.id, 86.5, 70.0, "Success supports the setup.")
    payload = {
        "beat": beat.to_dict(),
        "moment": moment.to_dict(),
        "match": match.to_dict(),
    }
    assert json.loads(json.dumps(payload))["match"]["match_score"] == 86.5
