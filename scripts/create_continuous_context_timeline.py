"""Create the continuous, feedback-driven Wardogs intro timeline."""

from pathlib import Path


INTRO_PATH = Path("/Volumes/Crucial X10/Editing Projects/JayWayy/Wardogs/Footage/Intro to Video One Item.mp4")
GAMEPLAY_PATH = Path("/Volumes/Crucial X10/Editing Projects/JayWayy/Wardogs/Footage/WarDogs Full Gameplay Footage.mp4")
TIMELINE_NAME = "IFM V0.4 - Refined Context"
FPS = 60
INTRO_DURATION = 51.35


VIDEO_EDITS = [
    (0.000, 3.580, 4181.800, "No money: -$250", "HUD visibly shows -$250."),
    (3.580, 4.520, 2910.600, "Keep dying: red hit and fall", "Player is hit; the view drops into the red downed state."),
    (4.520, 6.680, 4104.940, "Helicopter crashed: contextual reaction", "Crash is off-screen; source dialogue says a helicopter just crashed."),
    (6.680, 8.960, 1211.200, "Sniped: user-identified hit", "Source anchor 00:20:11:12; red sniper damage and immediate reaction context."),
    (8.960, 10.280, 4200.000, "Ran out of money: -$6,500", "HUD visibly shows -$6,500."),
    (10.280, 12.400, 2597.000, "Money is important: clean gameplay", "Clean readable gameplay fallback; no black gap."),
    (12.400, 14.740, 4194.800, "Buying a vehicle", "Vehicle Vendor selection and MH-6 helicopter purchase."),
    (14.740, 16.040, 15.000, "Browsing guns", "Equipment Vendor visibly displays the weapon catalog."),
    (16.040, 17.180, 7.500, "Buying med kits", "Equipment Vendor visibly displays the $200 medical kit."),
    (17.180, 19.500, 3658.500, "Keeping the team alive", "Player visibly revives a downed teammate."),
    (19.500, 22.840, 4325.000, "Stay alive in the circle", "Player moves through the active red-zone/circle context."),
    (22.840, 25.560, 4371.000, "Money is easy to lose: late -$4,430", "Late-game HUD visibly shows -$4,430 beside an urban equipment case."),
    (25.560, 28.500, 55.500, "Helicopter with teammates", "Closest honest context: player rides inside a helicopter with teammates."),
    (28.500, 32.280, 1527.800, "Teammate penalty: following a teammate", "Player visibly follows a teammate through incoming fire and into cover; no literal team-kill/spawn line exists."),
    (32.280, 35.360, 3809.600, "Money is hard to come by: fresh fallback", "Distinct late-game industrial courtyard combat while wounded; avoids repeating the wooded pre-sniper scenery."),
    (35.360, 40.600, 17.000, "Only spending $150", "The selected $150 monocular and resulting $150 HUD are visible."),
    (40.600, 42.920, 369.550, "Make as much money as possible", "Player discusses obtaining a free weapon."),
    (42.920, 49.100, 433.740, "Stealing other players' kits", "Player discusses taking dead players' weapons."),
    (49.100, 51.350, 4.000, "Heading to the weapon vendor", "Player opens the Equipment Vendor."),
]


AUDIO_EDITS = [
    (4.520, 6.680, 4104.940, "Helicopter crash reaction audio", '"Oh, a helicopter just crashed."'),
    (6.680, 9.800, 1215.180, "Sniper reaction audio", '"You fucker. There\'s no way."'),
]


def frames(seconds):
    return round(seconds * FPS)


def walk_clips(folder):
    yield from folder.GetClipList()
    for child in folder.GetSubFolderList():
        yield from walk_clips(child)


def find_by_path(root, path):
    wanted = str(path.resolve())
    for clip in walk_clips(root):
        if clip.GetClipProperty("File Path") == wanted:
            return clip
    return None


def find_timeline(project, name):
    for index in range(1, project.GetTimelineCount() + 1):
        timeline = project.GetTimelineByIndex(index)
        if timeline.GetName() == name:
            return timeline
    return None


def preserve_existing(project):
    existing = find_timeline(project, TIMELINE_NAME)
    if not existing:
        return
    base = TIMELINE_NAME + " - previous"
    name = base
    suffix = 2
    while find_timeline(project, name):
        name = f"{base} {suffix}"
        suffix += 1
    if not existing.SetName(name):
        raise RuntimeError("Could not preserve the previous continuity timeline")


def append(media_pool, item, record_in, record_out, source_in, media_type, track):
    duration = frames(record_out - record_in)
    source_start = frames(source_in)
    placed = media_pool.AppendToTimeline([{
        "mediaPoolItem": item,
        "startFrame": source_start,
        "endFrame": source_start + duration - 1,
        "mediaType": media_type,
        "trackIndex": track,
        "recordFrame": frames(record_in),
    }])
    if not placed:
        raise RuntimeError(f"Could not place source {source_in:.3f} at {record_in:.3f}")


def main():
    manager = resolve.GetProjectManager()
    project = manager.GetCurrentProject()
    if not project or project.GetName() != "JayWayy Wardogs":
        raise RuntimeError("Open the JayWayy Wardogs project")
    if float(project.GetSetting("timelineFrameRate")) != FPS:
        raise RuntimeError("The verified Wardogs project must remain 60 fps")

    preserve_existing(project)
    media_pool = project.GetMediaPool()
    root = media_pool.GetRootFolder()
    intro = find_by_path(root, INTRO_PATH)
    gameplay = find_by_path(root, GAMEPLAY_PATH)
    if not intro or not gameplay:
        raise RuntimeError("The intro and gameplay media must already be imported")

    timeline = media_pool.CreateEmptyTimeline(TIMELINE_NAME)
    if not timeline or not project.SetCurrentTimeline(timeline):
        raise RuntimeError("Could not create/select the continuity timeline")
    timeline.SetStartTimecode("00:00:00:00")
    timeline.SetTrackName("video", 1, "CONTINUOUS STORY MATCHES")
    timeline.SetTrackName("audio", 1, "INTRO VO")
    if not timeline.AddTrack("audio", "stereo"):
        raise RuntimeError("Could not create the contextual source-audio track")
    timeline.SetTrackName("audio", 2, "CONTEXT AUDIO")

    append(media_pool, intro, 0.0, INTRO_DURATION, 0.0, 2, 1)
    for number, (record_in, record_out, source_in, label, note) in enumerate(VIDEO_EDITS, 1):
        append(media_pool, gameplay, record_in, record_out, source_in, 1, 1)
        timeline.AddMarker(
            frames(record_in), "Blue", f"{number:02d} {label}",
            f"{note}\nSource seconds: {source_in:.3f}", frames(record_out - record_in), f"{source_in:.3f}",
        )
    for record_in, record_out, source_in, label, note in AUDIO_EDITS:
        append(media_pool, gameplay, record_in, record_out, source_in, 2, 2)
        timeline.AddMarker(
            frames(record_in), "Green", label,
            f"{note}\nSource seconds: {source_in:.3f}", frames(record_out - record_in), f"{source_in:.3f}",
        )

    if not manager.SaveProject():
        raise RuntimeError("Resolve did not confirm the project save")
    print(f"CREATED {TIMELINE_NAME}: {len(VIDEO_EDITS)} continuous unique video clips and {len(AUDIO_EDITS)} contextual audio clips")


if __name__ == "__main__":
    main()
