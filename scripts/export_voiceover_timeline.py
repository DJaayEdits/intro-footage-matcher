"""Export voiceover clip timing from the current Resolve timeline to JSON.

Run inside Resolve's Py3 console.

Optional overrides before exec():
    VO_TRACK_INDEX = 1
    VO_EXPORT_PATH = "/absolute/path/to/fitmc_voiceover_timeline.json"
"""

from __future__ import annotations

import json
from pathlib import Path


def main():
    manager = resolve.GetProjectManager()
    project = manager.GetCurrentProject()
    if not project:
        raise RuntimeError("Open the FitMC Resolve project first")

    timeline = project.GetCurrentTimeline()
    if not timeline:
        raise RuntimeError("Open the FitMC timeline first")

    fps = float(project.GetSetting("timelineFrameRate"))
    track_index = int(globals().get("VO_TRACK_INDEX", 1))
    items = timeline.GetItemListInTrack("audio", track_index) or []
    if not items:
        raise RuntimeError(f"No audio clips found on A{track_index}")

    timeline_start = timeline.GetStartFrame()
    rows = []

    for i, item in enumerate(items, 1):
        start_frame = int(item.GetStart())
        end_frame = int(item.GetEnd())
        duration_frames = end_frame - start_frame
        mpi = item.GetMediaPoolItem()

        source_path = None
        source_name = None
        if mpi:
            source_path = mpi.GetClipProperty("File Path") or None
            source_name = mpi.GetName()

        rows.append({
            "index": i,
            "timeline_item_name": item.GetName(),
            "source_name": source_name,
            "source_path": source_path,
            "record_start_frame": start_frame,
            "record_end_frame_exclusive": end_frame,
            "record_start_seconds": (start_frame - timeline_start) / fps,
            "record_end_seconds": (end_frame - timeline_start) / fps,
            "duration_seconds": duration_frames / fps,
        })

    payload = {
        "project_name": project.GetName(),
        "timeline_name": timeline.GetName(),
        "fps": fps,
        "timeline_start_frame": timeline_start,
        "audio_track_index": track_index,
        "clip_count": len(rows),
        "clips": rows,
    }

    output = globals().get("VO_EXPORT_PATH")
    if output:
        output_path = Path(str(output)).expanduser()
    else:
        output_path = Path.home() / "Desktop" / "fitmc_voiceover_timeline.json"

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"EXPORTED {len(rows)} voiceover clips to {output_path}")


main()
