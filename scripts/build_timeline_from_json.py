"""Build a DaVinci Resolve timeline from a reusable JSON cut list.

Run inside Resolve's Py3 console.

Option A: put cuts.json next to this script, then run:
    exec(open("/absolute/path/to/scripts/build_timeline_from_json.py").read())

Option B: point to a specific config first:
    CUTS_JSON = "/absolute/path/to/my-cuts.json"
    exec(open("/absolute/path/to/scripts/build_timeline_from_json.py").read())
"""

from __future__ import annotations

import json
from pathlib import Path


BIN_NAME = "AI Timeline Builder"


def seconds_to_frames(seconds: float, fps: float) -> int:
    return round(float(seconds) * fps)


def walk_clips(folder):
    yield from folder.GetClipList()
    for child in folder.GetSubFolderList():
        yield from walk_clips(child)


def find_by_path(root_folder, path: Path):
    wanted = str(path.resolve())
    for clip in walk_clips(root_folder):
        if clip.GetClipProperty("File Path") == wanted:
            return clip
    return None


def get_or_create_bin(media_pool, root_folder):
    for folder in root_folder.GetSubFolderList():
        if folder.GetName() == BIN_NAME:
            return folder
    created = media_pool.AddSubFolder(root_folder, BIN_NAME)
    if not created:
        raise RuntimeError(f"Could not create Resolve bin: {BIN_NAME}")
    return created


def import_once(media_pool, root_folder, target_folder, path: Path):
    existing = find_by_path(root_folder, path)
    if existing:
        return existing
    if not path.exists():
        raise FileNotFoundError(f"Source file does not exist: {path}")
    if not media_pool.SetCurrentFolder(target_folder):
        raise RuntimeError(f"Could not select media bin: {BIN_NAME}")
    imported = media_pool.ImportMedia([str(path.resolve())])
    if not imported:
        raise RuntimeError(f"Resolve could not import: {path}")
    return imported[0]


def find_timeline(project, name: str):
    for index in range(1, project.GetTimelineCount() + 1):
        timeline = project.GetTimelineByIndex(index)
        if timeline.GetName() == name:
            return timeline
    return None


def unique_backup_name(project, base_name: str) -> str:
    name = f"{base_name} - previous"
    suffix = 2
    while find_timeline(project, name):
        name = f"{base_name} - previous {suffix}"
        suffix += 1
    return name


def ensure_track(timeline, media_type: str, track_index: int):
    while timeline.GetTrackCount(media_type) < track_index:
        if media_type == "audio":
            ok = timeline.AddTrack("audio", "stereo")
        else:
            ok = timeline.AddTrack("video")
        if not ok:
            raise RuntimeError(
                f"Could not create {media_type} track {track_index}"
            )


def place_range(
    media_pool,
    media_item,
    source_start: int,
    source_end: int,
    record_frame: int,
    media_type: int,
    track_index: int,
):
    placed = media_pool.AppendToTimeline([{
        "mediaPoolItem": media_item,
        "startFrame": source_start,
        "endFrame": source_end,
        "mediaType": media_type,
        "trackIndex": track_index,
        "recordFrame": record_frame,
    }])
    if not placed:
        raise RuntimeError(
            f"Resolve could not place source frames "
            f"{source_start}-{source_end} at timeline frame {record_frame}"
        )
    return placed


def load_config() -> tuple[Path, dict]:
    explicit = globals().get("CUTS_JSON")
    if explicit:
        config_path = Path(str(explicit)).expanduser()
    else:
        config_path = Path(__file__).resolve().with_name("cuts.json")

    if not config_path.exists():
        raise FileNotFoundError(
            "Cut-list JSON not found. Either place cuts.json next to this script "
            "or set CUTS_JSON to an absolute JSON path before running the script. "
            f"Looked for: {config_path}"
        )

    data = json.loads(config_path.read_text(encoding="utf-8"))
    return config_path, data


def validate_config(data: dict):
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object")

    if not data.get("timeline_name"):
        raise ValueError("timeline_name is required")

    cuts = data.get("cuts")
    if not isinstance(cuts, list) or not cuts:
        raise ValueError("cuts must be a non-empty array")

    default_source = data.get("source")
    for index, cut in enumerate(cuts, 1):
        if not isinstance(cut, dict):
            raise ValueError(f"Cut {index} must be an object")

        source = cut.get("source", default_source)
        if not source:
            raise ValueError(
                f"Cut {index} needs a source path, either on the cut or at top level"
            )

        if "start_seconds" not in cut or "end_seconds" not in cut:
            raise ValueError(
                f"Cut {index} needs start_seconds and end_seconds"
            )

        start = float(cut["start_seconds"])
        end = float(cut["end_seconds"])
        if start < 0 or end <= start:
            raise ValueError(
                f"Cut {index} has invalid range: {start} -> {end}"
            )


def main():
    config_path, data = load_config()
    validate_config(data)

    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    if not project:
        raise RuntimeError("Open a DaVinci Resolve project before running this script")

    expected_project = data.get("project_name")
    if expected_project and project.GetName() != expected_project:
        raise RuntimeError(
            f'Expected project "{expected_project}", but "{project.GetName()}" is open'
        )

    fps = float(data.get("fps") or project.GetSetting("timelineFrameRate"))
    if fps <= 0:
        raise RuntimeError("Could not determine a valid timeline frame rate")

    timeline_name = str(data["timeline_name"])
    replace_existing = bool(data.get("replace_existing", False))

    existing = find_timeline(project, timeline_name)
    if existing:
        if not replace_existing:
            raise RuntimeError(
                f'Timeline "{timeline_name}" already exists. '
                'Set "replace_existing": true to preserve it under a - previous name '
                "and create a fresh timeline."
            )
        backup = unique_backup_name(project, timeline_name)
        if not existing.SetName(backup):
            raise RuntimeError(
                f'Could not preserve existing timeline "{timeline_name}" as "{backup}"'
            )
        print(f'PRESERVED existing timeline as: {backup}')

    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    target_folder = get_or_create_bin(media_pool, root_folder)

    source_cache = {}

    def get_source_item(source_text: str):
        source_path = Path(source_text).expanduser()
        key = str(source_path.resolve())
        if key not in source_cache:
            source_cache[key] = import_once(
                media_pool, root_folder, target_folder, source_path
            )
        return source_cache[key]

    timeline = media_pool.CreateEmptyTimeline(timeline_name)
    if not timeline:
        raise RuntimeError(f'Could not create timeline "{timeline_name}"')
    if not project.SetCurrentTimeline(timeline):
        raise RuntimeError(f'Could not select timeline "{timeline_name}"')

    start_timecode = str(data.get("start_timecode", "00:00:00:00"))
    if not timeline.SetStartTimecode(start_timecode):
        raise RuntimeError(f"Could not set timeline start timecode to {start_timecode}")

    video_track = int(data.get("video_track", 1))
    audio_track = int(data.get("audio_track", 1))
    ensure_track(timeline, "video", video_track)
    ensure_track(timeline, "audio", audio_track)

    timeline.SetTrackName(
        "video", video_track, str(data.get("video_track_name", "AI ROUGH CUT"))
    )
    timeline.SetTrackName(
        "audio", audio_track, str(data.get("audio_track_name", "AI ROUGH CUT AUDIO"))
    )

    base_record_frame = timeline.GetStartFrame()
    sequential_record_frame = base_record_frame
    default_source = data.get("source")

    placed_video = 0
    placed_audio = 0

    for index, cut in enumerate(data["cuts"], 1):
        source_text = cut.get("source", default_source)
        item = get_source_item(source_text)

        start_seconds = float(cut["start_seconds"])
        end_seconds = float(cut["end_seconds"])
        source_start = seconds_to_frames(start_seconds, fps)
        duration = seconds_to_frames(end_seconds - start_seconds, fps)
        source_end = source_start + duration - 1

        if "record_start_seconds" in cut:
            record_frame = base_record_frame + seconds_to_frames(
                float(cut["record_start_seconds"]), fps
            )
        else:
            record_frame = sequential_record_frame

        include_video = bool(cut.get("video", True))
        include_audio = bool(cut.get("audio", True))

        if not include_video and not include_audio:
            raise ValueError(f"Cut {index} disables both video and audio")

        if include_video:
            place_range(
                media_pool,
                item,
                source_start,
                source_end,
                record_frame,
                1,
                int(cut.get("video_track", video_track)),
            )
            placed_video += 1

        if include_audio:
            cut_audio_track = int(cut.get("audio_track", audio_track))
            ensure_track(timeline, "audio", cut_audio_track)
            place_range(
                media_pool,
                item,
                source_start,
                source_end,
                record_frame,
                2,
                cut_audio_track,
            )
            placed_audio += 1

        label = cut.get("label")
        note = cut.get("note")
        if label or note:
            timeline.AddMarker(
                record_frame - base_record_frame,
                str(cut.get("marker_color", "Blue")),
                str(label or f"Cut {index:02d}"),
                str(note or f"{start_seconds:.3f}-{end_seconds:.3f}s"),
                duration,
                f"{start_seconds:.3f}-{end_seconds:.3f}",
            )

        if "record_start_seconds" not in cut:
            sequential_record_frame += duration

    if not project_manager.SaveProject():
        raise RuntimeError("Resolve did not confirm project save")

    print(
        f'CREATED "{timeline_name}" from {config_path}: '
        f'{len(data["cuts"])} cuts, {placed_video} video placements, '
        f'{placed_audio} audio placements at {fps:g} fps'
    )


main()
