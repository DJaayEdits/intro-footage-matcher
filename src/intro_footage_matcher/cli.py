from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import STAGES, inspect_sources, run_analysis
from .report import render_report


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ifm", description="Local intro-to-gameplay footage matcher")
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="Inspect media and print the estimated workload")
    analyze_parser = subparsers.add_parser("analyze", help="Run or resume the complete local analysis")
    subparsers.add_parser("report", help="Re-render the most recent JSON report")
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
    matches = root / "reports" / "matches.json"
    if not matches.exists():
        raise SystemExit("No report data exists yet. Run analyze first.")
    render_report(json.loads(matches.read_text(encoding="utf-8")), root / "reports" / "index.html")
    print(f"Report written: {root / 'reports/index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

