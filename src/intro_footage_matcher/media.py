from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class MediaError(RuntimeError):
    pass


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise MediaError(f"Required tool not found on PATH: {name}")
    return path


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown media error").strip()
        raise MediaError(detail) from exc


def probe_media(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise MediaError(f"Media file does not exist: {source}")
    result = _run([
        _require_tool("ffprobe"), "-v", "error", "-show_entries",
        "format=filename,duration,size,bit_rate,start_time:stream=index,codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels",
        "-of", "json", str(source),
    ])
    raw = json.loads(result.stdout)
    streams = raw.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video_stream or not audio_stream:
        raise MediaError("Input must contain both a video stream and an audio stream")
    fmt = raw.get("format", {})
    return {
        "path": str(source),
        "duration": float(fmt["duration"]),
        "size": int(fmt.get("size", 0)),
        "bit_rate": int(fmt.get("bit_rate", 0)),
        "start_time": float(fmt.get("start_time", 0.0)),
        "video": {
            "index": int(video_stream["index"]),
            "codec": video_stream.get("codec_name", "unknown"),
            "width": int(video_stream["width"]),
            "height": int(video_stream["height"]),
            "frame_rate": video_stream.get("avg_frame_rate", "0/0"),
        },
        "audio": {
            "index": int(audio_stream["index"]),
            "codec": audio_stream.get("codec_name", "unknown"),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
        },
    }


def extract_audio(source: str | Path, output: str | Path) -> Path:
    source_path = Path(source).expanduser().resolve()
    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp = output_path.with_suffix(output_path.suffix + ".part")
    _run([
        _require_tool("ffmpeg"), "-v", "error", "-y", "-i", str(source_path),
        "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        "-f", "wav", str(temp),
    ])
    temp.replace(output_path)
    return output_path


def extract_sampled_frames(
    source: str | Path,
    output_dir: str | Path,
    *,
    fps: float = 2.0,
    width: int = 640,
) -> list[dict[str, Any]]:
    if fps <= 0 or width <= 0:
        raise ValueError("fps and width must be positive")
    source_path = Path(source).expanduser().resolve()
    target = Path(output_dir).expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise MediaError(f"Frame output directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    pattern = target / "frame_%06d.jpg"
    _run([
        _require_tool("ffmpeg"), "-v", "error", "-y", "-i", str(source_path),
        "-map", "0:v:0", "-vf", f"fps={fps:g},scale={width}:-2:flags=fast_bilinear",
        "-q:v", "4", str(pattern),
    ])
    frames = sorted(target.glob("frame_*.jpg"))
    return [
        {"index": index, "time": (index - 1) / fps, "path": str(path)}
        for index, path in enumerate(frames, start=1)
    ]
