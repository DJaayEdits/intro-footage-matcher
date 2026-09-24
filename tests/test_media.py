import subprocess
import wave
from pathlib import Path

import pytest

from intro_footage_matcher.media import MediaError, extract_audio, extract_sampled_frames, probe_media


@pytest.fixture(scope="module")
def sample_media(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("media with spaces")
    target = root / "sample clip.mp4"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=30:duration=3",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(target),
        ],
        check=True,
    )
    return target


def test_probe_media_reports_audio_video_and_duration(sample_media: Path):
    info = probe_media(sample_media)
    assert 2.9 <= info["duration"] <= 3.1
    assert info["video"]["width"] == 320
    assert info["video"]["height"] == 180
    assert info["audio"]["sample_rate"] == 48000


def test_extract_audio_writes_16khz_mono_wav(sample_media: Path, tmp_path: Path):
    output = tmp_path / "audio out.wav"
    extract_audio(sample_media, output)
    with wave.open(str(output)) as wav:
        assert wav.getframerate() == 16000
        assert wav.getnchannels() == 1
        assert 2.9 <= wav.getnframes() / wav.getframerate() <= 3.1


def test_extract_sampled_frames_preserves_source_times(sample_media: Path, tmp_path: Path):
    frames = extract_sampled_frames(sample_media, tmp_path / "frames", fps=1.0, width=160)
    assert [round(item["time"], 1) for item in frames] == [0.0, 1.0, 2.0]
    assert all(Path(item["path"]).exists() for item in frames)


def test_frame_extraction_never_deletes_existing_artifact(sample_media: Path, tmp_path: Path):
    output = tmp_path / "existing frames"
    output.mkdir()
    sentinel = output / "frame_000001.jpg"
    sentinel.write_bytes(b"old-valid-frame")
    with pytest.raises(MediaError, match="not empty"):
        extract_sampled_frames(sample_media, output, fps=2.0, width=160)
    assert sentinel.read_bytes() == b"old-valid-frame"
