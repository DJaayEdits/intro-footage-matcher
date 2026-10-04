"""Apply audited red-note V2 patches in Resolve Py3; never alter audio.

Run with exec(open('/path/to/this/script').read()). PLAN_JSON/AUDIT_JSON
may be supplied in the console; defaults refer to the reviewed FitMC files.
"""
from pathlib import Path
import ast
import json
import sys
from datetime import datetime

REPO = Path('/Users/djaay/Projects/intro-footage-matcher')
sys.path.insert(0, str(REPO / 'src'))
from intro_footage_matcher.editorial_patches import validate_editorial_patches
from intro_footage_matcher.frame_usage import require_unique_source_frames, require_unique_frame_ranges


def load_helpers():
    path = REPO / 'scripts/repair_fitmc_duplicates.py'
    tree = ast.parse(path.read_text()); tree.body.pop()
    ns = {'resolve': resolve}
    exec(compile(tree, str(path), 'exec'), ns)
    path = REPO / 'scripts/place_matches_on_existing_timeline.py'
    tree = ast.parse(path.read_text()); tree.body.pop()
    exec(compile(tree, str(path), 'exec'), ns)
    return ns


def annotations(timeline):
    return {'timeline': timeline.GetMarkers(), 'audio': [
        (item.GetUniqueId(), item.GetMarkers(), item.GetProperty())
        for track in range(1, timeline.GetTrackCount('audio') + 1)
        for item in (timeline.GetItemListInTrack('audio', track) or [])]}


def other_video(timeline):
    return [[(item.GetUniqueId(), item.GetStart(), item.GetEnd())
             for item in (timeline.GetItemListInTrack('video', track) or [])]
            for track in range(1, timeline.GetTrackCount('video') + 1) if track != 2]


def main():
    plan_path = Path(globals().get('PLAN_JSON', str(REPO / 'reports/fitmc-red-notes-placement.json')))
    audit_path = Path(globals().get('AUDIT_JSON', '/Users/djaay/Editing Projects Mac/Parker Wolf/fitmc-notes-current-audit.json'))
    data = json.loads(plan_path.read_text()); audit = json.loads(audit_path.read_text())
    manager = resolve.GetProjectManager(); project = manager.GetCurrentProject()
    if not project or project.GetName() != data['project_name']:
        raise RuntimeError('Wrong project; no edits made')
    timeline = project.GetCurrentTimeline()
    if not timeline or timeline.GetName() != data['timeline_name']:
        raise RuntimeError('Wrong timeline; no edits made')
    h = load_helpers(); state = h['video_state']; audio = h['audio_state']
    before = state(timeline)
    if before != audit['rows']:
        raise RuntimeError('V2 changed since audit; re-export before applying notes')
    before_audio = audio(timeline); h['require_audited_audio'](before_audio, audit)
    before_notes = annotations(timeline); before_other = other_video(timeline)
    fps = float(timeline.GetSetting('timelineFrameRate'))
    if fps != float(project.GetSetting('timelineFrameRate')):
        raise RuntimeError('Project/timeline FPS mismatch')
    base = min(item.GetStart() for item in timeline.GetItemListInTrack('audio', 1))
    changed = validate_editorial_patches(before, data['editorial_patches'], base, fps)
    items = {item.GetUniqueId(): item for item in timeline.GetItemListInTrack('video', 2)}
    prepared = []
    for patch in data['editorial_patches']:
        originals = sorted([items[clip_id] for clip_id in patch['old_ids']], key=lambda item: item.GetStart())
        props = originals[0].GetProperty(); color = originals[0].GetClipColor()
        # Imported chapter metadata from this Rusher source is retained in the
        # project backup/receipt; it must not label unrelated replacement footage.
        def imported_chapters(item):
            markers = list(item.GetMarkers().values())
            return (item.GetMediaPoolItem().GetClipProperty('File Path').endswith('Minecraft 2B2T - The Day Everything Changed...mp4')
                    and {m['name'] for m in markers} == {'Intro', 'The Castle', 'The Mine', 'Exploring'}
                    and all(m['color'] == 'Blue' and not m['note'] and not m.get('customData') for m in markers))
        if any(item.GetFusionCompCount() or (item.GetMarkers() and not imported_chapters(item)) for item in originals):
            raise RuntimeError('Affected clip has Fusion/clip markers; preserve explicitly before replacing')
        if any(item.GetProperty() != props or item.GetClipColor() != color for item in originals):
            raise RuntimeError('Merged clip properties differ; preserve explicitly before replacing')
        prepared.append((patch, originals, props, color))
    pool = project.GetMediaPool(); root = pool.GetRootFolder()
    target = h['get_or_create_bin'](pool, root)
    media = {source: h['import_once'](pool, root, target, Path(source))
             for source in {match['source'] for match in data['matches']}}
    if any(not item for item in media.values()):
        raise RuntimeError('A source could not be imported')
    rates = {source: float(item.GetClipProperty('FPS')) for source, item in media.items()}
    require_unique_source_frames(data['matches'], rates, fps)
    # Ensure the complete reviewed plan really contains only the named patches.
    unchanged = [row for row in before if row['id'] not in changed]
    expected = sorted([(row['source'], row['record_start'], row['record_end'], row['source_start'])
                       for row in unchanged] + [
        (segment['source'], base + round(segment['record_start_seconds'] * fps),
         base + round(segment['record_end_seconds'] * fps),
         round(segment['source_start_seconds'] * rates[segment['source']]))
        for patch in data['editorial_patches'] for segment in patch['segments']], key=lambda row: row[1])
    planned = [(match['source'], base + round(match['record_start_seconds'] * fps),
                base + round(match['record_end_seconds'] * fps),
                round(match['source_start_seconds'] * rates[match['source']])) for match in data['matches']]
    if planned != expected:
        raise RuntimeError('Full plan does not agree with patches and untouched live footage')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = plan_path.parent / f'fitmc-before-red-notes-{stamp}.drp'
    if not manager.SaveProject() or not manager.ExportProject(project.GetName(), str(backup)):
        raise RuntimeError('Backup failed; no clips deleted')
    receipt_path = plan_path.parent / f'fitmc-red-notes-receipt-{stamp}.json'
    receipt = {'backup': str(backup), 'audio_before': before_audio, 'patches_applied': [], 'original_clip_annotations': {clip_id: items[clip_id].GetMarkers() for clip_id in changed}}
    try:
        for patch, originals, props, color in prepared:
            if not timeline.DeleteClips(originals, False):
                raise RuntimeError('Non-ripple V2 deletion failed')
            for segment in patch['segments']:
                mpi = media[segment['source']]; sfps = rates[segment['source']]
                start = base + round(segment['record_start_seconds'] * fps)
                end = base + round(segment['record_end_seconds'] * fps)
                origin = int(float(mpi.GetClipProperty('Start') or 0))
                source_start = origin + round(segment['source_start_seconds'] * sfps)
                result = pool.AppendToTimeline([{'mediaPoolItem': mpi, 'startFrame': source_start,
                    'endFrame': source_start + round((end - start) / fps * sfps),
                    'mediaType': 1, 'trackIndex': 2, 'recordFrame': start}])
                if not result:
                    raise RuntimeError('Video append failed')
                new = result[0]
                if not new.SetProperty(props) or (color and not new.SetClipColor(color)):
                    raise RuntimeError('Cannot preserve video properties')
                if abs(new.GetStart() - start) > 1 or abs(new.GetEnd() - end) > 1:
                    raise RuntimeError('Replacement timing differs')
            receipt['patches_applied'].append(patch['old_ids'])
        after = state(timeline)
        if [row for row in after if row['id'] in {r['id'] for r in unchanged}] != unchanged:
            raise RuntimeError('Untouched V2 footage changed')
        if len(after) != len(expected):
            raise RuntimeError('Wrong final shot count')
        for row, goal in zip(after, expected):
            if row['source'] != goal[0] or any(abs(row[key] - value) > 1 for key, value in
                    zip(['record_start', 'record_end', 'source_start'], goal[1:])):
                raise RuntimeError('Live footage differs from reviewed plan')
        require_unique_frame_ranges([{'source': str(Path(row['source']).resolve()),
            'start': row['source_start'], 'end': row['source_end'] + 1, 'label': row['id']} for row in after])
        if audio(timeline) != before_audio or annotations(timeline) != before_notes or other_video(timeline) != before_other:
            raise RuntimeError('Audio, markers, or other tracks changed')
        if not manager.SaveProject():
            raise RuntimeError('Project save failed')
        receipt.update(status='verified', audio_unchanged=True, annotations_unchanged=True,
                       other_tracks_unchanged=True, remaining_source_frame_overlaps=0, video_after=after)
    except Exception as error:
        receipt.update(status='failed_or_partial', error=str(error))
        raise
    finally:
        receipt['audio_after'] = audio(timeline)
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'VERIFIED RED NOTES: {len(prepared)} patches, {len(after)} V2 shots; audio and markers unchanged; zero source-frame overlaps. Receipt: {receipt_path}')


main()
