"""Place matched footage over an existing Resolve voiceover timeline.

This script NEVER recreates or moves the voiceover. It only adds video footage
to the currently open timeline according to a JSON match file.

Expected JSON fields:
{
  "project_name": "Parker Wolf FitMC",
  "timeline_name": "MAIN SEQUENCE",
  "video_track": 2,
  "voiceover_track_index": 1,
  "matches": [
    {
      "record_start_seconds": 0.0,
      "record_end_seconds": 4.2,
      "source": "/absolute/path/to/video.mp4",
      "source_start_seconds": 123.5,
      "label": "literal match",
      "note": "..."
    }
  ]
}

Run inside Resolve's Py3 console.

Set before exec():
    MATCHES_JSON = "/absolute/path/to/fitmc_matches.json"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


BIN_NAME = "FitMC Matched Footage"


def frames(seconds: float, fps: float) -> int:
    return round(float(seconds) * fps)


def walk_clips(folder):
    yield from folder.GetClipList()
    for child in folder.GetSubFolderList():
        yield from walk_clips(child)


def find_by_path(root, path: Path):
    wanted = str(path.resolve())
    for clip in walk_clips(root):
        if clip.GetClipProperty("File Path") == wanted:
            return clip
    return None


def get_or_create_bin(media_pool, root):
    for folder in root.GetSubFolderList():
        if folder.GetName() == BIN_NAME:
            return folder
    folder = media_pool.AddSubFolder(root, BIN_NAME)
    if not folder:
        raise RuntimeError(f"Could not create bin: {BIN_NAME}")
    return folder


def import_once(media_pool, root, target, path: Path):
    existing = find_by_path(root, path)
    if existing:
        return existing
    if not path.exists():
        raise FileNotFoundError(path)
    if not media_pool.SetCurrentFolder(target):
        raise RuntimeError(f"Could not select bin: {BIN_NAME}")
    imported = media_pool.ImportMedia([str(path.resolve())])
    if not imported:
        raise RuntimeError(f"Could not import {path}")
    return imported[0]


def main():
    match_path = globals().get("MATCHES_JSON")
    if not match_path:
        raise RuntimeError("Set MATCHES_JSON before running this script")

    data = json.loads(Path(str(match_path)).expanduser().read_text(encoding="utf-8"))

    manager = resolve.GetProjectManager()
    project = manager.GetCurrentProject()
    if not project:
        raise RuntimeError("Open the FitMC project first")

    timeline = project.GetCurrentTimeline()
    if not timeline:
        raise RuntimeError("Open the FitMC timeline first")

    expected_project = data.get("project_name")
    if expected_project and project.GetName() != expected_project:
        raise RuntimeError(
            f'Expected project "{expected_project}", but "{project.GetName()}" is open'
        )

    expected_timeline = data.get("timeline_name")
    if expected_timeline and timeline.GetName() != expected_timeline:
        raise RuntimeError(
            f'Expected timeline "{expected_timeline}", but "{timeline.GetName()}" is open'
        )

    fps = float(project.GetSetting("timelineFrameRate"))
    timeline_start = timeline.GetStartFrame()
    video_track = int(data.get("video_track", 2))
    voiceover_track = int(data.get("voiceover_track_index", 1))

    voiceover_items = timeline.GetItemListInTrack("audio", voiceover_track) or []
    if not voiceover_items:
        raise RuntimeError(f"No voiceover clips found on A{voiceover_track}")
    voiceover_base_frame = min(int(item.GetStart()) for item in voiceover_items)

    media_pool = project.GetMediaPool()
    root = media_pool.GetRootFolder()
    target = get_or_create_bin(media_pool, root)
    cache = {}

    def item_for(source):
        path = Path(source).expanduser()
        key = str(path.resolve())
        if key not in cache:
            cache[key] = import_once(media_pool, root, target, path)
        return cache[key]

    matches = data.get("matches") or []
    if not matches:
        raise RuntimeError("No matches in JSON")

    repo_root = Path(str(match_path)).expanduser().resolve().parent.parent
    sys.path.insert(0, str(repo_root / "src"))
    from intro_footage_matcher.frame_usage import require_unique_source_frames
    source_fps_by_path = {
        source: float(item_for(source).GetClipProperty("FPS"))
        for source in {match["source"] for match in matches}
    }
    require_unique_source_frames(matches, source_fps_by_path, fps)

    while timeline.GetTrackCount("video") < video_track:
        if not timeline.AddTrack("video"):
            raise RuntimeError(f"Could not create V{video_track}")

    placed = 0
    for i, match in enumerate(matches, 1):
        record_start = float(match["record_start_seconds"])
        record_end = float(match["record_end_seconds"])
        source_start = float(match["source_start_seconds"])

        duration = frames(record_end - record_start, fps)
        if duration <= 0:
            raise ValueError(f"Match {i} has non-positive duration")

        media_item = item_for(match["source"])
        props = media_item.GetClipProperty() or {}
        try:
            source_fps = float(props.get("FPS") or fps)
        except (TypeError, ValueError):
            source_fps = fps
        try:
            clip_start_frame = int(float(props.get("Start") or 0))
        except (TypeError, ValueError):
            clip_start_frame = 0

        source_start_frame = clip_start_frame + frames(source_start, source_fps)
        source_duration = frames(record_end - record_start, source_fps)
        if source_duration <= 0:
            raise ValueError(f"Match {i} has non-positive source duration")

        record_frame = voiceover_base_frame + frames(record_start, fps)

        result = media_pool.AppendToTimeline([{
            "mediaPoolItem": media_item,
            "startFrame": source_start_frame,
            "endFrame": source_start_frame + source_duration,
            "mediaType": 1,
            "trackIndex": int(match.get("video_track", video_track)),
            "recordFrame": record_frame,
        }])
        if not result:
            raise RuntimeError(f"Could not place match {i}")

        label = match.get("label")
        note = match.get("note")
        if label or note:
            timeline.AddMarker(
                (voiceover_base_frame - timeline_start) + frames(record_start, fps),
                str(match.get("marker_color", "Blue")),
                str(label or f"Match {i:03d}"),
                str(note or ""),
                duration,
                str(match.get("match_type", "")),
            )
        placed += 1

    if not manager.SaveProject():
        raise RuntimeError("Resolve did not confirm project save")

    print(
        f"PLACED {placed} matched video clips on V{video_track} "
        f"without changing the voiceover; aligned to A{voiceover_track} start"
    )


main()
