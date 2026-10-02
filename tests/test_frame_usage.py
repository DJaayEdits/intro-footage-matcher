import pytest
from intro_footage_matcher.frame_usage import require_unique_source_frames

def shot(source,start,record_start,record_end):
 return {'source':source,'source_start_seconds':start,'record_start_seconds':record_start,'record_end_seconds':record_end}

def test_rejects_nonadjacent_reuse_even_when_only_one_source_frame_overlaps():
 rows=[shot('/fit.mp4',10,0,2),shot('/other.mp4',0,2,4),shot('/fit.mp4',11.9666667,4,6)]
 with pytest.raises(ValueError,match='reused source frames'):
  require_unique_source_frames(rows,{'/fit.mp4':30,'/other.mp4':60},60)

def test_checks_pause_extended_duration_not_candidate_end():
 a=shot('/fit.mp4',10,0,6);a['source_candidate_end_seconds']=12
 with pytest.raises(ValueError,match='reused source frames'):
  require_unique_source_frames([a,shot('/fit.mp4',14,6,8)],{'/fit.mp4':30},60)

def test_allows_distinct_ranges_and_distinct_files():
 require_unique_source_frames([shot('/fit.mp4',10,0,2),shot('/fit.mp4',13,2,4),shot('/other.mp4',10,4,6)],{'/fit.mp4':29.97,'/other.mp4':60},60)

def test_mixed_fps_subframe_times_cannot_hide_reuse():
 with pytest.raises(ValueError,match='reused source frames'):
  require_unique_source_frames([shot('/fit.mp4',10,0,1),shot('/fit.mp4',10.99,1,2)],{'/fit.mp4':29.97},60)

def test_selector_skips_a_better_scoring_repeat_and_reserves_full_display_length():
 from intro_footage_matcher.frame_usage import choose_unused_candidate
 candidates=[{'source':'/fit.mp4','source_start':10,'score':.99},{'source':'/fit.mp4','source_start':20,'score':.7}]
 chosen=choose_unused_candidate(candidates,duration=5,used={'/fit.mp4':[(9,13)]},source_durations={'/fit.mp4':40})
 assert chosen['source_start']==20
 assert chosen['source_end']==25

def test_selector_stops_when_only_repeats_or_short_sources_exist():
 from intro_footage_matcher.frame_usage import choose_unused_candidate
 with pytest.raises(ValueError):
  choose_unused_candidate([{'source':'/fit.mp4','source_start':10}],duration=5,used={'/fit.mp4':[(9,13)]},source_durations={'/fit.mp4':40})
 with pytest.raises(ValueError):
  choose_unused_candidate([{'source':'/fit.mp4','source_start':38}],duration=5,used={},source_durations={'/fit.mp4':40})

def test_repair_audio_snapshot_handles_items_without_media_pool_objects():
 import ast
 from pathlib import Path
 from types import SimpleNamespace
 path=Path(__file__).parents[1]/'scripts/repair_fitmc_duplicates.py'
 tree=ast.parse(path.read_text());tree.body.pop();namespace={}
 exec(compile(tree,str(path),'exec'),namespace)
 item=SimpleNamespace(GetUniqueId=lambda:'audio',GetStart=lambda:10,GetEnd=lambda:20,GetLeftOffset=lambda:0,GetRightOffset=lambda:0,GetMediaPoolItem=lambda:None)
 timeline=SimpleNamespace(GetTrackCount=lambda kind:1,GetItemListInTrack=lambda kind,index:[item])
 assert namespace['audio_state'](timeline)==[[('audio',10,20,0,0,None)]]

def test_source_reservation_covers_unquantized_append_duration_at_high_source_fps():
 with pytest.raises(ValueError,match='reused source frames'):
  require_unique_source_frames([shot('/fit.mp4',0,.51/24,2.49/24),shot('/fit.mp4',.05,3/24,5/24)],{'/fit.mp4':120},24)

def test_repair_refuses_audio_source_offsets_changed_since_audit():
 import ast
 from pathlib import Path
 path=Path(__file__).parents[1]/'scripts/repair_fitmc_duplicates.py'
 tree=ast.parse(path.read_text());tree.body.pop();namespace={}
 exec(compile(tree,str(path),'exec'),namespace)
 before=[[('vo',0,100,10,20,'/vo.wav')]]
 audit={'audio':[[['vo',0,100,11,19,'/vo.wav']]]}
 check=namespace['require_audited_audio']
 with pytest.raises(RuntimeError,match='Audio changed since audit'):
  check(before,audit)
