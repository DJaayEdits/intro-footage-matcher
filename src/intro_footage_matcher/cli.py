from __future__ import annotations

import argparse
import json
from pathlib import Path

from .folder_index import build_folder_index
from .folder_match import build_voiceover_matches
from .pipeline import STAGES, inspect_sources, run_analysis
from .report import render_report
from .voiceover import write_voiceover_outputs


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ifm", description="Local intro-to-gameplay footage matcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect media and print the estimated workload")
    analyze_parser = subparsers.add_parser("analyze", help="Run or resume the complete local analysis")
    subparsers.add_parser("report", help="Re-render the most recent JSON report")

    index_parser = subparsers.add_parser(
        "index-folder",
        help="Recursively index a folder of local footage for later matching",
    )
    index_parser.add_argument("--clips-root", required=True, type=Path)
    index_parser.add_argument("--sample-every", type=float, default=8.0)
    index_parser.add_argument("--max-frames-per-video", type=int, default=90)
    index_parser.add_argument(
        "--no-transcribe-specific",
        action="store_true",
        help="Skip local Whisper transcription of fit/ and rusher/ source videos",
    )

    vo_parser = subparsers.add_parser(
        "transcribe-voiceover",
        help="Transcribe an edited voiceover locally with word timestamps",
    )
    vo_parser.add_argument("--voiceover", required=True, type=Path)

    match_parser = subparsers.add_parser(
        "match-voiceover",
        help="Match a timestamped voiceover transcript against an indexed footage folder",
    )
    match_parser.add_argument("--voiceover", required=True, type=Path)
    match_parser.add_argument("--index", required=True, type=Path)
    match_parser.add_argument("--top-k", type=int, default=5)

    for child in (inspect_parser, analyze_parser):
        child.add_argument("--intro", required=True, type=Path)
        child.add_argument("--gameplay", required=True, type=Path)

    analyze_parser.add_argument("--force-stage", choices=STAGES)
    analyze_parser.add_argument("--sample-fps", type=float, default=2.0)
    analyze_parser.add_argument("--max-visual-frames", type=int, default=1000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = _project_root()

    if args.command == "inspect":
        print(json.dumps(inspect_sources(args.intro, args.gameplay), indent=2))
        return 0

    if args.command == "analyze":
        result = run_analysis(
            root, args.intro, args.gameplay,
            force_stage=args.force_stage,
            sample_fps=args.sample_fps,
            max_visual_frames=args.max_visual_frames,
        )
        print(f"Report written: {root / 'reports/index.html'}")
        print(f"Intro beats: {len(result['results'])}")
        return 0

    if args.command == "index-folder":
        result = build_folder_index(
            root,
            args.clips_root,
            sample_every=args.sample_every,
            max_frames_per_video=args.max_frames_per_video,
            transcribe_specific=not args.no_transcribe_specific,
        )
        print(f"Index written: {root / 'reports/footage-index.json'}")
        print(json.dumps(result["counts"], indent=2))
        return 0

    if args.command == "transcribe-voiceover":
        result = write_voiceover_outputs(root, args.voiceover)
        print(f"Transcript JSON: {result['json']}")
        print(f"Transcript text: {result['text']}")
        print(f"Segments: {result['segments']}")
        print(f"Duration: {result['duration']:.2f}s")
        return 0

    if args.command == "match-voiceover":
        result = build_voiceover_matches(root, args.voiceover, args.index, top_k=args.top_k)
        print(f"Match candidates: {root / 'reports/fitmc-match-candidates.json'}")
        print(f"Beats: {result['beat_count']}")
        return 0

    matches = root / "reports" / "matches.json"
    if not matches.exists():
        raise SystemExit("No report data exists yet. Run analyze first.")
    render_report(json.loads(matches.read_text(encoding="utf-8")), root / "reports" / "index.html")
    print(f"Report written: {root / 'reports/index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
