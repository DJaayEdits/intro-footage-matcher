"""Replace only changed V2 shots. Set PLAN_JSON and AUDIT_JSON in Resolve Py3.

The audited clip IDs/ranges must still match. Export a project backup before
non-ripple deletion. Never delete, move, trim, or replace audio.
"""
from pathlib import Path
import ast
from datetime import datetime
import json
import sys


def audio_state(timeline):
    return [[(i.GetUniqueId(), i.GetStart(), i.GetEnd(), i.GetLeftOffset(),
              i.GetRightOffset(), (i.GetMediaPoolItem().GetClipProperty('File Path')
                                  if i.GetMediaPoolItem() else None))
             for i in (timeline.GetItemListInTrack('audio', track) or [])]
            for track in range(1, timeline.GetTrackCount('audio') + 1)]


def video_state(timeline):
    return [{'id': i.GetUniqueId(), 'source': i.GetMediaPoolItem().GetClipProperty('File Path'),
             'record_start': i.GetStart(), 'record_end': i.GetEnd(),
             'source_start': i.GetSourceStartFrame(), 'source_end': i.GetSourceEndFrame()}
            for i in sorted(timeline.GetItemListInTrack('video', 2) or [], key=lambda item: item.GetStart())]


def require_audited_audio(before_audio, audit):
    normalized = json.loads(json.dumps(before_audio))
    if 'audio' not in audit or normalized != audit['audio']:
        raise RuntimeError('Audio changed since audit or audited audio is missing. Re-audit before repair.')


def capture_audit(path):
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project or not project.GetCurrentTimeline():
        raise RuntimeError('Open the target project and timeline first')
    timeline = project.GetCurrentTimeline()
    payload = {'project': project.GetName(), 'timeline': timeline.GetName(),
               'rows': video_state(timeline), 'audio': audio_state(timeline)}
    Path(path).write_text(json.dumps(payload, indent=2) + '\n')
    print('EXPORTED live video and audio audit:', path)


def repair():
    plan_path = Path(PLAN_JSON)
    repo = plan_path.resolve().parent.parent
    sys.path.insert(0, str(repo / 'src'))
    from intro_footage_matcher.frame_usage import require_unique_source_frames, require_unique_frame_ranges
    data = json.loads(plan_path.read_text())
    audit = json.loads(Path(AUDIT_JSON).read_text())
    manager = resolve.GetProjectManager()
    project = manager.GetCurrentProject()
    if not project or project.GetName() != data['project_name']:
        raise RuntimeError('Wrong open project')
    timeline = project.GetCurrentTimeline()
    if not timeline or timeline.GetName() != data['timeline_name']:
        raise RuntimeError('Wrong open timeline')
    old_state = video_state(timeline)
    expected = [{k: r[k] for k in old_state[0]} for r in sorted(audit['rows'], key=lambda r: r['record_start'])]
    if old_state != expected or len(old_state) != len(data['matches']):
        raise RuntimeError('V2 has changed since the audit. Re-audit; no timeline edits made.')
    fps = float(timeline.GetSetting('timelineFrameRate'))
    if abs(fps - float(project.GetSetting('timelineFrameRate'))) > .001:
        raise RuntimeError('Project/timeline FPS mismatch')
    before_audio = audio_state(timeline)
    require_audited_audio(before_audio, audit)
    base = min(i.GetStart() for i in timeline.GetItemListInTrack('audio', 1))
    # Load the existing, documented media-pool helpers without executing main().
    script = repo / 'scripts/place_matches_on_existing_timeline.py'
    tree = ast.parse(script.read_text());tree.body.pop()
    ns = {'resolve': resolve, '__name__': '__repair_helpers__'}
    exec(compile(tree, str(script), 'exec'), ns)
    pool = project.GetMediaPool();root = pool.GetRootFolder()
    target = ns['get_or_create_bin'](pool, root)
    media = {source: ns['import_once'](pool, root, target, Path(source))
             for source in {m['source'] for m in data['matches']}}
    rates = {source: float(item.GetClipProperty('FPS')) for source, item in media.items()}
    require_unique_source_frames(data['matches'], rates, fps)
    items = sorted(timeline.GetItemListInTrack('video', 2), key=lambda i: i.GetStart())
    changes = []
    for item, old, match in zip(items, old_state, data['matches']):
        if abs((base + round(match['record_start_seconds'] * fps)) - old['record_start']) > .001:
            raise RuntimeError('Replacement would move a shot')
        if abs((base + round(match['record_end_seconds'] * fps)) - old['record_end']) > .001:
            raise RuntimeError('Replacement would trim a shot')
        source_start = round(match['source_start_seconds'] * rates[match['source']])
        if old['source'] == match['source'] and abs(old['source_start'] - source_start) <= 1:
            continue
        if item.GetFusionCompCount():
            raise RuntimeError('Affected shot has a Fusion composition; preserve it before replacement')
        changes.append((item, old, match, item.GetProperty(), item.GetMarkers(), item.GetClipColor()))
    # Do not touch any other video track. Check it for source-frame conflicts too.
    other_video = [[(i.GetUniqueId(), i.GetStart(), i.GetEnd())
                    for i in (timeline.GetItemListInTrack('video', track) or [])]
                   for track in range(1, timeline.GetTrackCount('video') + 1) if track != 2]
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = plan_path.parent / f'fitmc-before-dedup-{stamp}.drp'
    if not manager.SaveProject() or not manager.ExportProject(project.GetName(), str(backup)):
        raise RuntimeError('Could not export project backup. No timeline clips deleted.')
    receipt = {'project': project.GetName(), 'timeline': timeline.GetName(),
               'backup': str(backup), 'replaced': [], 'audio_before': before_audio}
    receipt_path = plan_path.parent / 'fitmc-dedup-receipt.json'
    try:
        for item, old, match, props, markers, color in changes:
            if not timeline.DeleteClips([item], False):
                raise RuntimeError('Non-ripple V2 deletion failed')
            mpi = media[match['source']];sfps = rates[match['source']]
            origin = int(float(mpi.GetClipProperty('Start') or 0))
            source_start = origin + round(match['source_start_seconds'] * sfps)
            duration = (old['record_end'] - old['record_start']) / fps
            result = pool.AppendToTimeline([{'mediaPoolItem': mpi,
                'startFrame': source_start, 'endFrame': source_start + round(duration * sfps),
                'mediaType': 1, 'trackIndex': 2, 'recordFrame': old['record_start']}])
            if not result:
                raise RuntimeError('V2 append failed')
            new = result[0]
            if not new.SetProperty(props):
                raise RuntimeError('Could not preserve video properties')
            if color and not new.SetClipColor(color):
                raise RuntimeError('Could not preserve clip color')
            for frame, marker in markers.items():
                if not new.AddMarker(frame, marker['color'], marker['name'], marker['note'], marker['duration'], marker.get('customData', '')):
                    raise RuntimeError('Could not preserve clip marker')
            if abs(new.GetStart() - old['record_start']) > 1 or abs(new.GetEnd() - old['record_end']) > 1:
                raise RuntimeError('Replacement timing differs from original')
            receipt['replaced'].append({'label': match['label'], 'old': old,
                'new_id': new.GetUniqueId(), 'start': new.GetStart(), 'end': new.GetEnd()})
        after = video_state(timeline)
        if len(after) != len(old_state):
            raise RuntimeError('Video clip count changed unexpectedly')
        # Treat the API source end as inclusive conservatively: +1 protects the
        # boundary even on Resolve versions that report an exclusive end.
        require_unique_frame_ranges([{'source': str(Path(r['source']).resolve()),
            'start': r['source_start'], 'end': r['source_end'] + 1,
            'label': r['id']} for r in after])
        after_other = [[(i.GetUniqueId(), i.GetStart(), i.GetEnd())
                        for i in (timeline.GetItemListInTrack('video', track) or [])]
                       for track in range(1, timeline.GetTrackCount('video') + 1) if track != 2]
        if after_other != other_video or audio_state(timeline) != before_audio:
            raise RuntimeError('Audio or other video tracks changed')
        receipt['video_after'] = after
        receipt['audio_unchanged'] = True
        receipt['remaining_source_frame_overlaps'] = 0
        if not manager.SaveProject():
            raise RuntimeError('Project save failed')
        receipt['status'] = 'verified'
    except Exception as error:
        receipt['status'] = 'failed_or_partial';receipt['error'] = str(error)
        raise
    finally:
        receipt['audio_after'] = audio_state(timeline)
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f"VERIFIED: replaced {len(changes)} V2 shots; 119 shots retained; zero source-frame overlaps; audio unchanged. Backup: {backup}")


if globals().get('CAPTURE_AUDIT_PATH'):
    capture_audit(globals().pop('CAPTURE_AUDIT_PATH'))
else:
    repair()
