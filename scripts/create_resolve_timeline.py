"""Create the reviewed V0.1 intro assembly in the open Resolve project.

Run from Resolve's Py3 console with:
exec(open("/absolute/path/to/this/file").read())
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path("/Volumes/Crucial X10/Editing Projects/JayWayy/Wardogs/Footage/intro-footage-matcher")
REPORT_PATH = PROJECT_ROOT / "reports/matches.json"
TIMELINE_NAME = "IFM V0.1 - Intro Assembly"
BIN_NAME = "Intro Footage Matcher V0.1"

# Use a strong alternate from the top three where it avoids immediately
# repeating the same source moment or better isolates the line's meaning.
CHOICES = {
    6: 1,  # making money: stealing weapons for extra money
    7: 1,  # blue-team win objective
    8: 1,  # vendor/free-weapon visual
}


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
    return media_pool.AddSubFolder(root_folder, BIN_NAME)


def import_once(media_pool, root_folder, target_folder, path: Path):
    existing = find_by_path(root_folder, path)
    if existing:
        return existing
    if not media_pool.SetCurrentFolder(target_folder):
        raise RuntimeError(f"Could not select media bin {BIN_NAME}")
    imported = media_pool.ImportMedia([str(path.resolve())])
    if not imported:
        raise RuntimeError(f"Resolve could not import {path}")
    return imported[0]


def existing_timeline(project, name: str):
    for index in range(1, project.GetTimelineCount() + 1):
        timeline = project.GetTimelineByIndex(index)
        if timeline.GetName() == name:
            return timeline
    return None


def timeline_is_complete(timeline, expected_video_clips: int) -> bool:
    return (
        len(timeline.GetItemListInTrack("video", 1)) == expected_video_clips
        and len(timeline.GetItemListInTrack("audio", 1)) == 1
        and len(timeline.GetMarkers()) == expected_video_clips
    )


def preserve_incomplete_timeline(project, timeline):
    base = f"{TIMELINE_NAME} - incomplete"
    name = base
    suffix = 2
    while existing_timeline(project, name):
        name = f"{base} {suffix}"
        suffix += 1
    if not timeline.SetName(name):
        raise RuntimeError("Found an incomplete matcher timeline but could not preserve/rename it")
    print(f"PRESERVED incomplete assembly as: {name}")


def main():
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from intro_footage_matcher.media import probe_media
    from intro_footage_matcher.resolve_assembly import build_edit_plan, require_exact_frame_rate

    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    if not project or project.GetName() != "JayWayy Wardogs":
        raise RuntimeError("Open the JayWayy Wardogs project before running this script")
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    intro_path = Path(report["sources"]["intro"])
    gameplay_path = Path(report["sources"]["gameplay"])
    intro_info = probe_media(intro_path)
    gameplay_info = probe_media(gameplay_path)
    fps = require_exact_frame_rate(
        project.GetSetting("timelineFrameRate"),
        intro_info["video"]["frame_rate"],
        gameplay_info["video"]["frame_rate"],
    )
    intro_duration = intro_info["duration"]
    intro_frames = round(intro_duration * fps)
    plan = build_edit_plan(
        report, fps=fps, intro_duration=intro_duration, choices=CHOICES
    )

    previous = existing_timeline(project, TIMELINE_NAME)
    if previous:
        if timeline_is_complete(previous, len(plan)):
            if not project.SetCurrentTimeline(previous):
                raise RuntimeError("Complete matcher timeline exists but could not be selected")
            print(f"EXISTS {TIMELINE_NAME}: verified complete; no changes made")
            return
        preserve_incomplete_timeline(project, previous)

    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    target_folder = get_or_create_bin(media_pool, root_folder)
    intro_item = import_once(media_pool, root_folder, target_folder, intro_path)
    gameplay_item = import_once(media_pool, root_folder, target_folder, gameplay_path)

    timeline = media_pool.CreateEmptyTimeline(TIMELINE_NAME)
    if not timeline:
        raise RuntimeError("Resolve could not create the matcher timeline")
    if not project.SetCurrentTimeline(timeline) or project.GetCurrentTimeline() != timeline:
        raise RuntimeError("Resolve could not select the newly created matcher timeline")
    if not timeline.SetStartTimecode("00:00:00:00"):
        raise RuntimeError("Resolve could not set matcher timeline start timecode")
    timeline.SetTrackName("video", 1, "MATCHED GAMEPLAY")
    timeline.SetTrackName("audio", 1, "INTRO VO")
    timeline_start = timeline.GetStartFrame()

    audio_items = media_pool.AppendToTimeline([{
        "mediaPoolItem": intro_item,
        "startFrame": 0,
        "endFrame": intro_frames - 1,
        "mediaType": 2,
        "trackIndex": 1,
        "recordFrame": timeline_start,
    }])
    if not audio_items:
        raise RuntimeError("Could not place intro audio")

    for number, edit in enumerate(plan, start=1):
        placed = media_pool.AppendToTimeline([{
            "mediaPoolItem": gameplay_item,
            "startFrame": edit["source_start"],
            "endFrame": edit["source_start"] + edit["duration"] - 1,
            "mediaType": 1,
            "trackIndex": 1,
            "recordFrame": timeline_start + edit["record_start"],
        }])
        if not placed:
            raise RuntimeError(f"Could not place gameplay for {edit['beat_id']}")
        note = f"{edit['beat_text']}\nGameplay source: {edit['source_timecode']}"
        if not timeline.AddMarker(
            edit["record_start"], "Blue", f"{number:02d} {edit['beat_id']}",
            note, edit["duration"], edit["source_timecode"],
        ):
            raise RuntimeError(f"Could not add marker for {edit['beat_id']}")

    if not project_manager.SaveProject():
        raise RuntimeError("Resolve did not confirm project save")
    print(
        f"CREATED {TIMELINE_NAME}: {len(plan)} video edits, "
        f"1 intro audio clip, {intro_frames} frames at {fps} fps"
    )


main()
