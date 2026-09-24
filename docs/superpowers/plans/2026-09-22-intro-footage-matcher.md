# Intro Footage Matcher V0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a restartable local pipeline that recommends three precise gameplay clips for each intro story beat and renders the results as JSON and HTML.

**Architecture:** A Python CLI orchestrates fingerprinted FFmpeg, Whisper, frame-analysis, moment-index, ranking, and report stages. Expensive artifacts are cached independently; ranking is deterministic and combines text semantics, visual/editorial evidence, and stakes.

**Tech Stack:** Python 3.13, FFmpeg/ffprobe 8, faster-whisper, PyTorch/Transformers CLIP, sentence-transformers, Pillow, NumPy, pytest, static HTML/CSS/JavaScript.

**Spec:** `docs/superpowers/specs/2026-09-22-intro-footage-matcher-design.md`

## Global Constraints

- Source media is read-only and never fully re-encoded.
- Media and inference remain local; no OpenAI or other hosted API is used.
- All source times remain floating-point seconds until presentation.
- Every expensive stage must be fingerprinted, atomic, and restartable.
- V0.1 is a CLI plus static report, not a polished desktop/web application.

## Review Focus

- Paths containing spaces must work without shell interpolation bugs.
- A stale artifact from changed source size/mtime or changed settings must never be reused.
- Intro punctuation gaps and silence must not create empty or excessively long beats.
- Overlapping moment candidates must not occupy multiple top-three slots for the same beat.
- HTML must escape transcripts/descriptions and must not embed source video data.

---

### Task 1: Core models, timestamps, and cache contract

**Files:** Create `pyproject.toml`, `src/intro_footage_matcher/models.py`, `src/intro_footage_matcher/cache.py`, `src/intro_footage_matcher/timecode.py`; test `tests/test_core.py`.

**Interfaces:** Produces typed dictionaries/dataclasses for beats, moments, matches; `format_timecode(seconds)`; `source_fingerprint(path)`; `StageCache.load/write`.

- [ ] Write failing tests using literal timecode values and a temporary file whose size/mtime changes.
- [ ] Run `pytest tests/test_core.py -v`; verify import/behavior failures.
- [ ] Implement minimal formatting, dataclasses, fingerprinting, atomic JSON writes, and validation.
- [ ] Run `pytest tests/test_core.py -v`; verify pass.

### Task 2: Media probing and restartable extraction

**Files:** Create `src/intro_footage_matcher/media.py`; test `tests/test_media.py`.

**Interfaces:** Consumes file paths and stage cache. Produces `probe_media`, `extract_audio`, and `extract_sampled_frames` metadata with exact timestamps.

- [ ] Generate a five-second synthetic A/V fixture in the test and write failing assertions for streams, duration tolerance, and sampled timestamps.
- [ ] Run `pytest tests/test_media.py -v`; verify missing functions fail.
- [ ] Implement subprocess argument arrays for ffprobe/FFmpeg, 16 kHz mono audio, and 2 fps scaled sampling.
- [ ] Run `pytest tests/test_media.py -v`; verify pass and that paths with spaces work.

### Task 3: Transcript and intro beats

**Files:** Create `src/intro_footage_matcher/transcribe.py`, `src/intro_footage_matcher/beats.py`; test `tests/test_beats.py`.

**Interfaces:** `transcribe_audio(path, model_dir)` returns timestamped segments/words. `build_intro_beats(segments)` returns labeled beats.

- [ ] Write failing tests for pause/punctuation boundaries, empty input, maximum duration, and literal editorial labels.
- [ ] Run `pytest tests/test_beats.py -v`; verify expected failures.
- [ ] Implement local faster-whisper adapter and deterministic beat/role logic.
- [ ] Run `pytest tests/test_beats.py -v`; verify pass.

### Task 4: Gameplay moments and local visual evidence

**Files:** Create `src/intro_footage_matcher/signals.py`, `src/intro_footage_matcher/vision.py`, `src/intro_footage_matcher/moments.py`; test `tests/test_moments.py`.

**Interfaces:** `select_representatives(frame_metrics, audio_metrics, transcripts)` chooses bounded frames. `describe_frames(paths, labels)` returns label scores. `build_moments(...)` returns 6–15 second candidates with evidence.

- [ ] Write failing tests for peak selection, window clamping/merging, silent visual moments, and description composition.
- [ ] Run `pytest tests/test_moments.py -v`; verify expected failures.
- [ ] Implement FFmpeg audio metrics, frame-difference metrics, CLIP label scoring, and deterministic candidate aggregation.
- [ ] Run `pytest tests/test_moments.py -v`; verify pass.

### Task 5: Semantic/editorial ranking

**Files:** Create `src/intro_footage_matcher/ranking.py`; test `tests/test_ranking.py`.

**Interfaces:** `rank_matches(beats, moments, embeddings, top_k=3)` returns scored reasons with overlap suppression.

- [ ] Write failing tests proving semantic score, story value, role compatibility, visual-only support, and duplicate suppression affect literal rankings.
- [ ] Run `pytest tests/test_ranking.py -v`; verify expected failures.
- [ ] Implement normalized score components and sentence-transformer embedding adapter.
- [ ] Run `pytest tests/test_ranking.py -v`; verify pass.

### Task 6: CLI, pipeline manifest, and HTML report

**Files:** Create `src/intro_footage_matcher/cli.py`, `src/intro_footage_matcher/pipeline.py`, `src/intro_footage_matcher/report.py`, `src/intro_footage_matcher/templates/report.html`, `run.sh`, `README.md`; test `tests/test_pipeline.py`, `tests/test_report.py`.

**Interfaces:** `ifm analyze`, `ifm report`, and `ifm inspect` orchestrate stages and produce `reports/matches.json` plus `reports/index.html`.

- [ ] Write failing tests for reuse/invalidation, dependency ordering, safe HTML escaping, and three results per beat.
- [ ] Run `pytest tests/test_pipeline.py tests/test_report.py -v`; verify expected failures.
- [ ] Implement the CLI, manifest, report renderer, and rerun documentation.
- [ ] Run the entire `pytest -v` suite; verify pass.
- [ ] Run `./run.sh inspect` against the two real sources.
- [ ] Run the full local analysis, open/inspect the generated report, and rerun to verify cache hits.

