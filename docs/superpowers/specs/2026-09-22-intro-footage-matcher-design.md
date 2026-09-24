# Intro Footage Matcher V0.1 Design

## Purpose

Build a local-first prototype that turns one timestamped intro and one long gameplay recording into three ranked gameplay clip suggestions for every meaningful intro beat. The prototype is successful when the recommendations are editorially useful, have precise source timestamps, include intelligible reasons and separate semantic/story scores, and can be reviewed in a local HTML report.

## Inputs and constraints

- Intro: `../Intro to Video One Item.mp4` (51.35 seconds, 1080p60 H.264/AAC).
- Gameplay: `../WarDogs Full Gameplay Footage.mp4` (4,707.819 seconds, 1080p60 H.264/AAC, 40.0 GB).
- Do not alter or re-encode either source.
- Keep speech, frames, models, embeddings, and results local.
- Preserve source seconds as floating-point values until display formatting.
- Fingerprint source path, size, modification time, and relevant stage settings so completed work can be reused safely.
- Keep V0.1 as a command-line batch pipeline and static report; do not build a polished application or Resolve integration.

## Architecture

The `ifm` command drives independent cached stages: probe, audio extraction, transcription, intro-beat construction, gameplay signal/frame extraction, moment construction, semantic/story matching, and report rendering. Each stage writes a versioned JSON artifact under `cache/<source fingerprint>/`; frame JPEGs live beside their metadata. A manifest records the exact inputs, settings, model names, and completion status.

The expensive media work is delegated to FFmpeg/ffprobe. Python performs deterministic segmentation, feature aggregation, editorial-role scoring, ranking, and HTML rendering. Faster Whisper `small.en` supplies local timestamped speech. A local CLIP model supplies visual similarity to gameplay/editorial labels, while a compact sentence-transformer supplies text-semantic embeddings. If a model is unavailable, the stage fails with a direct setup message rather than silently returning keyword-only results.

## Data flow

1. Probe both media files and validate usable audio/video streams.
2. Extract 16 kHz mono WAV audio with stream timestamps anchored at zero.
3. Transcribe locally into word/segment JSON.
4. Split intro speech at sentence punctuation, long pauses, and maximum duration; label each beat with one or more editorial roles.
5. Decode gameplay at 2 fps and 640-pixel width, recording frame time, visual-change/motion signals, and cached JPEGs only for selected representatives.
6. Measure audio loudness in short windows. Combine peaks, transcript boundaries, and visual changes into 6–15 second gameplay moment candidates.
7. For each moment, combine local transcript context, top CLIP labels, motion, cuts, and loudness into a searchable description and story-role feature vector.
8. Embed intro beats and moment descriptions. Rank candidates with semantic similarity, role compatibility, visual support, and stakes/story value; suppress near-duplicate overlapping clips.
9. Render JSON and a self-contained local HTML report with source timestamps, descriptions, reasons, scores, and optional frame thumbnails.

## Scoring

`match_score` is a normalized 0–100 score composed of 55% semantic similarity, 25% editorial-role compatibility, 10% visual-label support, and 10% transcript/context support. `story_value_score` is a separate 0–100 measure derived from action/motion, audio intensity, scene change, outcome-bearing labels, and role confidence. The final retrieval ordering uses 75% match score and 25% story value, followed by temporal-overlap suppression.

Editorial roles are setup, success, confidence, escalation, danger, setback, failure, comeback, clutch, victory, defeat, funny, and reaction. Rules may assign multiple roles and confidence values. Visual evidence can produce a useful match even when the moment has no dialogue.

## Restartability and errors

Every stage writes to a temporary file then atomically replaces its final artifact. A valid artifact is reused when its fingerprint and stage version match. `--force-stage NAME` invalidates one stage and all dependents. FFmpeg/model failures preserve earlier artifacts and print the failed command/stage without exposing private data.

## User interface

Primary command:

```bash
./run.sh analyze --intro "../Intro to Video One Item.mp4" --gameplay "../WarDogs Full Gameplay Footage.mp4"
```

Fast reranking/report rebuild:

```bash
./run.sh report
```

Outputs are `reports/matches.json` and `reports/index.html`. The HTML groups recommendations by intro beat and shows exact `HH:MM:SS.mmm` in/out values, short descriptions, reasons, scores, and a clickable local media link with a `#t=start,end` fragment when supported by the browser.

## Testing and acceptance

Unit tests cover timestamp formatting, beat splitting, editorial-role classification, moment-window merging, score calculation, overlap suppression, cache invalidation, and report escaping. A small synthetic media fixture validates ffprobe/audio/frame timestamp handling without touching the 40 GB source. Final acceptance requires a full local run, three ranked non-overlapping suggestions per intro beat where enough moments exist, a renderable HTML report, and rerun evidence showing expensive stages are reused.

