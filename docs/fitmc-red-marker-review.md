# FitMC red-marker editorial review

The October 3, 2026 review addresses nine distinct user notes on MAIN SEQUENCE.
The red notes were exported from the actual Resolve timeline, with fresh V2 and
all-audio snapshots. Existing edits to the b042/b043 boundary are authoritative.
The one red A1 clip marker duplicates the opening timeline note; audio is untouched.

## Rules learned from the review

- Match the action and object in each clause. Destruction needs an explosion,
  active griefing, or visible ruins; an intact base is insufficient. Hostility
  between players should show player interaction/combat when available.
- Match who performs and who suffers the action. Do not imply Fit destroyed a
  base when the narration describes other players destroying his bases.
- When narration concerns Fit's videos or actions, prefer his own footage/POV.
  A Rusher recording is appropriate only for a claim concerning Rusher or a
  clearly relevant event, not solely because the section concerns the war.
- A sentence may contain multiple shots. Use cached word timestamps to align
  highways, bases, bedrock, maps, and attacks with their respective clauses.
  Do not force one shot to cover distinct visible subjects.
- Conversely, merge fragmented adjacent beats when one coherent sequence
  supports them. Avoid arbitrary very short shots, such as a 1.6-second
  architecture insert during a sustained description of veterans.
- Reserve scarce literal footage for the narration that explicitly names it.
  If a monument insert was consumed earlier, relocate the earlier contextual
  shot; do not downgrade the literal monument passage or repeat the insert.
- A source transcript match is a search lead, not visual proof. Inspect the
  actual in/out range, including transitions, death screens, black frames,
  embedded stills and repeated material inside documentary compilations.
- Check named players against source evidence. Do not infer identity from
  a generic player skin. If local footage cannot establish identity, seek an
  original source when authorized and record its provenance.
- Preserve all user review notes. Timeline markers remain at their exact
  positions even when video is split or merged. The executor refuses affected
  clips with user markers or Fusion compositions pending explicit preservation.
  Original imported Rusher chapter metadata is archived in the project backup
  and receipt, rather than copied as false labels on unrelated new footage.

## Reviewed changes

| VO time | Revision |
|---|---|
| 00:05–00:14 | Ruins for griefing/destruction; Fit's base when the narration switches to building. |
| 00:34–00:41 | Spawn context, then Fit POV combat for no rules; removes the sustained death screen. |
| 00:41–00:46 | Player attack/death for hostility rather than empty wasteland. |
| 01:10–01:20 | Obsidian route through ruined spawn, then the burning/ruined Wrath monument. |
| 02:16–02:28 | Continuous archived Kingoros versus PopBob/iTristan fight; replaces unrelated architecture and rapid beat changes. |
| 04:42–04:50 | Fit's own documentary tour POV with historian Offtopia rather than Rusher's POV. |
| 07:04–07:07, 07:37–08:01 | Reallocate drainage/interior footage, then align bedrock, coordinate map and Fitlantis attack to the spoken clauses. |
| 08:33–08:40 | Visible destroyed structures; avoids showing Fit as the perpetrator. This is contextual ruined-base coverage, not an asserted specific attack on Fit's base. |
| 10:41–10:47 | Highway followed by the original wood/farm base at the corresponding clause. |

Additional visual-review fixes move the Rusher introduction past a dark logo,
consolidate the duel aftermath to prevent repeating the same death/portrait
insert across adjacent shots, and replace the repeated Personal Story sunset
with unused Fit documentary tour footage.

## Supplemental sources

Only these missing sources were downloaded. Existing transcripts, footage index,
and CLIP embeddings were reused; no transcription or embedding pass was rerun.
New source FPS and duration were probed locally.

- FitMC, [The Untold Stories of 2b2t](https://www.youtube.com/watch?v=an6XX4R4Mn0).
  Original uploader metadata and automatic source captions identify the archived
  Kingoros encounter with PopBob/iTristan at 05:33–05:45 and 06:15–06:30.
  The reviewed selection uses 05:55–06:07.45, within that combat sequence.
- FitMC, [2b2t: A Dark History](https://www.youtube.com/watch?v=39cvCuUxtEM).
  The uploader describes visiting PopBob's last known home. Selected POV tour
  ranges are 02:25–02:33.83 and 04:10–04:16.47; they show Fit documenting history,
  without implying the accompanying historian Offtopia is PopBob.

The installed downloader's older extraction failed with HTTP 403. A current
PyPI copy in a temporary directory successfully downloaded both sources at 720p.
No project dependency or cached-analysis environment was changed.

## Validation and application status

The applied plan contains 16 bounded V2 patches. The initial 15 reviewed
revisions were refreshed to preserve a manual split of the final shot, with an
additional two-source-frame offset on its tail to avoid a shared boundary frame.
The final timeline contains 121 V2 shots. All unrelated current shot timings/source ranges are retained.
Full-plan source-frame uniqueness and source-duration checks pass. A 1,349-frame
visual comparison at 2 fps flagged no repeated images before the final manual-split
refresh. The post-placement comparison flagged the two adjoining pieces of the
final camera pan as visually similar. Full-size frame inspection confirms
different camera/star positions within the same continuous shot, not a reused
insert; their actual source-frame ranges are disjoint. Sampling is not an exhaustive
proof that every decoded frame differs.

The six editorial-patch regression cases and nine frame-usage cases pass.
The full suite has 65 passes and the same pre-existing word-join fixture failure
in `test_word_timestamps_split_long_single_segment_at_internal_pause`.

**Applied and verified in Resolve on October 3, 2026.** The initial attempt
stopped before editing because V2 had changed: the final shot had been split
after the original audit. The refreshed snapshot confirmed all 136 A1 clips and
audio offsets were unchanged. The plan retained that split and all other manual
edits; the guard was not bypassed.

Resolve completed all 16 patches and saved the project. The timestamped receipt
reports `verified`, 121 V2 shots, zero actual source-frame overlaps, unchanged
audio/annotations/other tracks, and unchanged unrelated V2 items. The project
backup was exported before non-ripple V2 deletion. Original source chapter
metadata is retained in that backup and the receipt. The receipt is
`reports/fitmc-red-notes-receipt-20261003-233245.json`; its project backup is
`reports/fitmc-before-red-notes-20261003-233245.drp`. Canonical placement reports
now reflect the actual saved timeline and source-frame starts.

Local ignored evidence lives in `reports/fitmc-red-marker-notes.json`,
`fitmc-notes-current-audit.json`, `fitmc-red-notes-placement.json`, and
`fitmc-red-notes-visual-audit.json`. Media, project backups, and full caches are
kept out of Git.
