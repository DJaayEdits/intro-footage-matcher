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
