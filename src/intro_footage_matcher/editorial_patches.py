"""Validate local video replacements, including clause splits and shot merges."""
import math


def validate_editorial_patches(rows, patches, base, fps):
    """Return changed IDs only if each patch covers its original outer bounds.

    Existing one-frame assembly gaps may be filled inside a merged passage.
    No unrelated shot, outer boundary, or audio item may be included.
    """
    ordered = sorted(rows, key=lambda row: row['record_start'])
    positions = {row['id']: index for index, row in enumerate(ordered)}
    changed = set()
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('Invalid timeline FPS')
    for patch in patches:
        ids = patch['old_ids']
        if not ids or len(set(ids)) != len(ids) or changed.intersection(ids):
            raise ValueError('Empty or repeated patch clip IDs')
        if any(clip_id not in positions for clip_id in ids):
            raise ValueError('Stale patch clip IDs')
        indexes = sorted(positions[clip_id] for clip_id in ids)
        if indexes != list(range(indexes[0], indexes[-1] + 1)):
            raise ValueError('Patch clips must be contiguous')
        originals = [ordered[index] for index in indexes]
        for left, right in zip(originals, originals[1:]):
            if not 0 <= right['record_start'] - left['record_end'] <= 1:
                raise ValueError('Patch crosses a gap or overlap')
        cursor = originals[0]['record_start']
        if not patch['segments']:
            raise ValueError('Missing replacement segments')
        for segment in patch['segments']:
            start = base + round(segment['record_start_seconds'] * fps)
            end = base + round(segment['record_end_seconds'] * fps)
            if start != cursor or end <= start:
                raise ValueError('Replacement timing has a gap, overlap, or changed start')
            cursor = end
        if cursor != originals[-1]['record_end']:
            raise ValueError('Replacement changes the outer end')
        changed.update(ids)
    return changed
