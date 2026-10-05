# Editorial requirements

User instructions are authoritative. Reuse the existing repository, branch,
transcripts, footage index, source transcripts, sampled frames, and embeddings.
Do not rerun transcription or embedding generation unless required data is missing.

## No repeated frames

No source video frame may appear in two different shots of a rough cut, including
partial overlaps and nonadjacent repetitions. Using the same file is allowed
only with disjoint source-frame ranges and distinct displayed imagery.

- Reserve the full displayed duration, including pauses and merged beats.
- Convert to each source's actual FPS, and allow a guard frame for rounding.
- Apply a hard constraint, never merely a score/overlap penalty.
- Recheck the final plan after every manual substitution or duration extension.
- If no fitting, relevant unused footage is available, stop and report the
  affected narration. Do not silently repeat footage or choose unrelated footage.
- Distinct source ranges are necessary but insufficient: a documentary can
  contain repeated stills or reused inserts at different timestamps, and multiple
  files can contain the same footage. Inspect the displayed imagery too. A sampled
  visual comparison helps find repeats but does not prove every frame is unique.
- Verify actual Resolve source-frame ranges after placement. Check across the
  full cut, not only consecutive clips. Preserve the audit and backup locally.

## Existing Resolve projects

Never recreate, move, cut, trim, replace, or modify the existing voiceover.
Place video only. Before a repair, audit live clip IDs, source frames, timing,
and audio offsets; refuse a stale audit. Export a project backup before deleting
video clips. Use non-ripple deletion only on explicitly identified video clips.
Preserve other tracks, video properties, and annotations. Verify the existing
voiceover and other tracks remain unchanged after the operation.

## Relevance

Every spoken claim must be reasonably represented on screen. Prefer literal
footage, then the correct person/event/base/era, then strong contextual evidence.
Use generic B-roll only when stronger footage is unavailable. Low-confidence
CLIP similarity alone is insufficient. Removing duplicates must preserve relevance.

For FitMC, follow docs/fitmc-documentary-matching-policy.md. Preserve the existing
A1 VO in Parker Wolf FitMC / MAIN SEQUENCE and place selected video on V2.

## Red-marker review lessons

Read docs/fitmc-red-marker-review.md before revising a marked rough cut. Match
individual clauses and the actor/victim relationship, use the subject's own POV
when discussing their videos, and reserve literal inserts for their named passage.
Multiple video shots may cover one phrase; several short beats may share one
coherent shot. Align changes with cached word timestamps and preserve the VO.
Preserve current manual video edits and user markers. Verify identities from
original source evidence; do not label an unknown player from their skin alone.
When authorized, download only missing supplemental sources and record provenance;
probe their FPS/duration without rebuilding existing analysis or embeddings.

## Second-pass timing and pacing

Read docs/fitmc-timing-and-pacing-policy.md before refining an assembled cut.
Keep the existing selections as editorial intent and reuse cached analysis.
Listen to the actual edited dialogue; align subject changes to the first frame
of their spoken trigger word. Motivate cuts by meaning, not elapsed duration.
Selective holds into a new idea are allowed; same-phrase changes need tighter timing.
Review full source ranges and exclude baked-in cuts, transitions, title cards
and unrelated scenes. Extend clean footage first, then mild natural retiming,
a clean readable freeze, relevant neighboring coverage, or removal.
An intentional freeze within one shot is permitted, but its original source
frame must not recur in another shot; retain provenance for derivative media.
Recheck actual source-frame consumption after retiming or duration changes.
Record review evidence and unresolved passages; documenting these rules does
not establish that the existing timeline has passed them. Preserve the audio,
user annotations, unrelated edits and source files using the existing guards.

## User-directed visual hits

Read docs/fitmc-marker-timing-policy.md before a marker-guided refinement.
Inventory every current timeline marker, preserve its exact contents and frame,
and distinguish user instructions from generated metadata. An explicit user-marked
visual hit overrides transcript alignment and inferred timing. Learn semantic
patterns from demonstrated hits for unmarked passages, without inventing fixed
shot lengths or cutting on every emphasized word. Adapt neighboring video around
the chosen hit; keep audio locked. Report every marker's disposition separately
from inferred edits and verify exact saved boundary frames. Documentation alone
does not establish that markers were inspected or the timeline was changed.
