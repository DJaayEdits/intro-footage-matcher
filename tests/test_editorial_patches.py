import pytest
from intro_footage_matcher.editorial_patches import validate_editorial_patches


def segment(a,b):
    return {'record_start_seconds':a,'record_end_seconds':b}


def test_allows_phrase_split_and_merges_tiny_gaps_without_touching_other_shots():
    rows=[{'id':'a','record_start':100,'record_end':160},
          {'id':'b','record_start':161,'record_end':220},
          {'id':'c','record_start':220,'record_end':280}]
    patches=[{'old_ids':['a','b'],'segments':[segment(0,.5),segment(.5,2)]}]
    assert validate_editorial_patches(rows,patches,100,60)=={'a','b'}


def test_refuses_a_patch_that_covers_an_unselected_live_shot():
    rows=[{'id':'a','record_start':0,'record_end':60},
          {'id':'b','record_start':60,'record_end':120},
          {'id':'c','record_start':120,'record_end':180}]
    with pytest.raises(ValueError,match='contiguous'):
        validate_editorial_patches(rows,[{'old_ids':['a','c'],'segments':[segment(0,3)]}],0,60)


@pytest.mark.parametrize('parts',[[segment(0,.9),segment(1,2)],
                                  [segment(0,1.1),segment(1,2)],
                                  [segment(0,1.9)]])
def test_refuses_replacement_gaps_overlaps_or_changed_outer_bounds(parts):
    with pytest.raises(ValueError):
        validate_editorial_patches([{'id':'a','record_start':0,'record_end':120}],
                                  [{'old_ids':['a'],'segments':parts}],0,60)


def test_refuses_reused_or_stale_clip_ids():
    rows=[{'id':'a','record_start':0,'record_end':60}]
    for ids in [['a','a'],['missing']]:
        with pytest.raises(ValueError):
            validate_editorial_patches(rows,[{'old_ids':ids,'segments':[segment(0,1)]}],0,60)
