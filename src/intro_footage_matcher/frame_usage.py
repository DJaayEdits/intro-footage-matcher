"""Hard source-frame uniqueness checks for full displayed video ranges."""
from __future__ import annotations

import math
from pathlib import Path


def placement_frame_ranges(matches, source_fps, timeline_fps):
    """Reserve half-open source ranges plus one frame for Resolve rounding.

    Use the full displayed duration, including carried pauses, rather than a
    candidate/transcript end. Same-source touching cuts need a one-frame guard.
    This catches range reuse; it cannot identify re-edited footage in other files.
    """
    if not math.isfinite(timeline_fps) or timeline_fps <= 0:
        raise ValueError('Invalid timeline FPS')
    rows = []
    for index, match in enumerate(matches):
        source = str(Path(match['source']).expanduser().resolve())
        fps = float(source_fps[match['source']])
        duration = (round(float(match['record_end_seconds']) * timeline_fps)
                    - round(float(match['record_start_seconds']) * timeline_fps)) / timeline_fps
        seconds = float(match['source_start_seconds'])
        if not math.isfinite(fps) or fps <= 0 or not math.isfinite(seconds) or seconds < 0 or duration <= 0:
            raise ValueError('Invalid source range or FPS')
        start = round(seconds * fps)
        # The standalone placement script rounds the unquantized duration at
        # source FPS. Reserve that too: rounded record endpoints can be shorter.
        raw_duration = float(match['record_end_seconds']) - float(match['record_start_seconds'])
        consumed = max(math.ceil(duration * fps), round(raw_duration * fps))
        end = start + consumed + 1
        rows.append({'source': source, 'start': start, 'end': end,
                     'label': match.get('label', str(index + 1))})
    return rows


def require_unique_frame_ranges(rows):
    """Reject any reused frame in half-open ranges, across the whole cut."""
    used = {}
    for row in rows:
        if row['end'] <= row['start']:
            raise ValueError('Invalid source frame range')
        for previous in used.setdefault(row['source'], []):
            if max(previous['start'], row['start']) < min(previous['end'], row['end']):
                raise ValueError(f"reused source frames: {previous['label']} / {row['label']} ({row['source']})")
        used[row['source']].append(row)


def require_unique_source_frames(matches, source_fps, timeline_fps):
    require_unique_frame_ranges(placement_frame_ranges(matches, source_fps, timeline_fps))


def choose_unused_candidate(candidates, *, duration, used, source_durations):
    """Pick the first ranked, fitting, unused candidate; never fall back to reuse."""
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Invalid displayed duration')
    for candidate in candidates:
        start = float(candidate['source_start'])
        end = start + duration
        source = candidate['source']
        # 0.1s protects fractional/rounded frame boundaries before timeline FPS
        # is known. The actual placement guard checks Resolve/source FPS later.
        if start < 0 or end + 0.1 > source_durations[source]:
            continue
        if any(max(start, a) < min(end + 0.1, b + 0.1) for a, b in used.get(source, [])):
            continue
        chosen = dict(candidate)
        chosen['source_end'] = end
        return chosen
    raise ValueError('No fitting unused source range is available; review footage instead of repeating frames')
