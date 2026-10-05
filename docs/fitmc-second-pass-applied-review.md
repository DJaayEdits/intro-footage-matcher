# FitMC applied second-pass review

On 2026-10-04 the existing Parker Wolf FitMC / MAIN SEQUENCE was edited directly on V2, backed up, saved, and independently read back. Existing audio and annotations were compared unchanged. The result has 115 shots and zero video gaps.

Applied: 22 moved existing boundaries, 7 additional motivated boundaries, 85 original selections with adjusted source ranges, 55 extended selections, 3 retimes, 19 frame holds, 13 editorial deletions, and 7 selections receiving replacement visuals. Range/extension counts include small continuity fixes; 45 existing one-frame gaps were closed.

## Verification and remaining work

Original-source provenance reservations are disjoint. A 2 FPS cross-shot image scan reviewed 1,351 samples and found zero potential repeat pairs. This does not prove every frame is unique or every transition absent. Scene-change candidates and source contact sheets were inspected; full playback remains required.

No audio-listening capability was available. Cached words were correlated with the actual edited A1 waveform; this reference lagged approximately 50 ms. Exact audible onsets remain listening checks. Do not treat this measured offset as a general synchronization rule or claim listening completion from correlation.

The clean Fitlantis interior does not prove kitchen, bathroom or gym identity. Literal room coverage remains unresolved, particularly the gym. Do not label an ambiguous interior from narration alone.

Local receipts, project backups, actual saved-timeline audit, original-source provenance, media, and exact TC/frame manual worksheet are retained under the editing workspace's pacing-review directory. The worksheet is second-pass-review.md. Canonical local placement reports now reflect the saved selections; prior reports are retained with a before-pacing suffix. These records are already applied, not authorization to append another full video cut.

## Operational lessons

- Retimes and holds in this pass use prepared video-only 60 FPS media; native Resolve item speed is 100%. Do not retime those assets again. Keep referenced media available and preserve original files.
- Check original-source provenance as well as physical media filenames: distinct derivatives can reuse the same original frames. Recompute consumption after every duration or speed change; a freeze reserves its held original frame.
- Native low-FPS append rounding can leave one-frame record gaps. Read the actual timeline endpoints and verify full coverage after placement.
- Two native source-end frame values were one frame below the exact source-end-time result. Cross-check source-end time with actual FPS and record duration; document discrepancies rather than silently weakening endpoint checks.
- Count editorial deletions separately from API item recreation. Report actions from actual saved state, and distinguish verified application from outstanding listening or visual evidence.
