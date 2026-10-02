# FitMC duplicate footage revision

The live MAIN SEQUENCE audit found 38 overlapping source-range pairs. Manual
matching revisions had reused preferred source sections, and the matcher treated
overlap as a score penalty rather than a hard rejection. Extending shots through
pauses also made candidate-only end timestamps insufficient.

A visual comparison additionally confirmed repeated stills embedded at different
timestamps in Personal Story: the veteran group, farming pool, Wrath monument,
and snowy base. Two late source sections also contained black imagery.

The repair replaced 35 V2 shots while retaining 119 shots and the existing record
slots. A project backup was exported first. Resolve's post-repair source-frame
check found zero overlaps; audio clip IDs, timing, source paths, and source offsets
matched the pre-repair snapshot. Other video tracks remained unchanged. A sampled
visual audit compared 1,350 frames at 2 fps and found no repeated sequences in the
revised plan. This sample does not prove uniqueness of every displayed image.

## Prevention

- `AGENTS.md` sets the permanent editorial rule and requires image review for
  embedded stills and footage reused across files.
- `frame_usage.py` rejects reused source frames using full display ranges and
  actual source/timeline FPS, including a guard frame for rounding.
- The folder matcher chooses fitting unused candidates or stops for review.
- The Resolve placement script validates uniqueness before adding video tracks
  or appending timeline clips.
- `repair_fitmc_duplicates.py` refuses stale audits, exports a project backup,
  compares audited audio offsets, replaces only changed V2 clips with non-ripple deletion, preserves transform
  properties/clip markers/color, and verifies audio and other tracks afterward.

Keep analysis caches, placement overrides, live audit JSON, receipts, and DRP
backups in local ignored reports. No transcription or embeddings were regenerated.
The updated local canonical placement JSON contains the unique reviewed plan.

## Validation

Nine added regression tests pass. Full suite: 59 passed, one unrelated baseline
failure in `tests/test_beats.py::test_word_timestamps_split_long_single_segment_at_internal_pause`.
The committed baseline also produces double spaces for the fixture's leading-space
word tokens; this revision does not change transcription or word joining.
