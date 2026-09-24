# intro-footage-matcher V0.1

A local-first prototype that transcribes an intro and a long gameplay recording, builds a multimodal gameplay timeline, and ranks three source-timestamped clip suggestions for each intro story beat.

Editorial selection and assembly follow [`docs/editorial-policy.md`](docs/editorial-policy.md): literal visible action first, contextual source audio second, distinct generic gameplay as the final fallback, continuous intro coverage, and no repeated source ranges.

## What stays local

The source videos, extracted audio, frames, transcripts, visual embeddings, and reports remain on this machine. The source video is never fully re-encoded. FFmpeg decodes it for audio and low-resolution frame sampling only.

## Requirements

- Python 3.11–3.13
- FFmpeg and ffprobe on `PATH`
- Roughly 5 GB free on APFS, or 35 GB on exFAT volumes whose large allocation blocks make Python packages and thousands of sampled frames occupy more physical space
- Apple silicon or a reasonably recent CPU/GPU; V0.1 also works on CPU

## Setup

From this folder:

```bash
chmod +x setup.sh run.sh
./setup.sh
```

`setup.sh` also removes macOS `._*` metadata sidecars that can otherwise confuse Python packages when the project lives on an exFAT drive.

`setup.sh` downloads CLIP and MiniLM weights once into the normal Hugging Face cache. Analysis then loads them offline and never uploads media.

## Inspect before processing

```bash
./run.sh inspect \
  --intro "../Intro to Video One Item.mp4" \
  --gameplay "../WarDogs Full Gameplay Footage.mp4"
```

## Analyze or resume

```bash
./run.sh analyze \
  --intro "../Intro to Video One Item.mp4" \
  --gameplay "../WarDogs Full Gameplay Footage.mp4"
```

Open `reports/index.html` after the command completes. Machine-readable output is `reports/matches.json`.

Each stage prints either `[run]` or `[cache]`. If a run stops, repeat the same command; completed stages are reused. To intentionally rebuild one stage and everything downstream:

```bash
./run.sh analyze \
  --intro "../Intro to Video One Item.mp4" \
  --gameplay "../WarDogs Full Gameplay Footage.mp4" \
  --force-stage matches
```

Valid stages are `probe`, `audio`, `transcript`, `beats`, `frames`, `signals`, `vision`, `moments`, `embeddings`, `matches`, and `report`.

To re-render HTML from the latest JSON without analyzing media:

```bash
./run.sh report
```

## Sampling controls

The defaults inspect the gameplay at 2 fps for inexpensive motion/scene signals and select at most 1,000 representative images for CLIP. For a quicker quality probe:

```bash
./run.sh analyze ... --sample-fps 1 --max-visual-frames 500
```

Changing these values produces a distinct cache signature for the affected stages.

For this 78-minute source, the full 2 fps quality run produced a ~9.4 GB cache on the exFAT drive. Use `--sample-fps 1 --max-visual-frames 500` for future sources when the smaller cache is preferable.

## Tests

```bash
.venv/bin/python -m pytest -v
```

The tests use synthetic media and do not read the large gameplay source.

## Resolve proof-of-concept timeline

The source-specific assembly script is `scripts/create_resolve_timeline.py`.
With the `JayWayy Wardogs` project open, open **Workspace → Console**, select
**Py3**, and run:

```python
exec(open("/Volumes/Crucial X10/Editing Projects/JayWayy/Wardogs/Footage/intro-footage-matcher/scripts/create_resolve_timeline.py").read())
```

It creates `IFM V0.1 - Intro Assembly` once, with intro audio on `INTRO VO`,
nine video-only gameplay selections on `MATCHED GAMEPLAY`, and beat markers
containing the narration line and gameplay source timestamp. A rerun verifies
an already-complete assembly and makes no changes. If it finds an incomplete
assembly, it preserves it under an `- incomplete` name before rebuilding; it
never overwrites the proof timeline or the pre-existing `Timeline 1`.

The feedback-driven Wardogs pass is
`scripts/create_continuous_context_timeline.py`. It creates
`IFM V0.4 - Refined Context`, covers the complete intro without black gaps,
uses distinct source ranges, and places useful helicopter/sniper reactions on
a separate `CONTEXT AUDIO` track.

## V0.1 limitations

- Visual descriptions are label-based CLIP classifications, not free-form captions.
- It does not yet detect game-specific HUD values or Resolve timeline metadata.
- Scores are editorial heuristics intended for comparison within this report, not calibrated probabilities.
