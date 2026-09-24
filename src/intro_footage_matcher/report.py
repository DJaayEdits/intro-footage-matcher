from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .models import Beat, Match, Moment
from .timecode import format_timecode


def build_report_data(
    beats: list[Beat],
    moments: list[Moment],
    matches: dict[str, list[Match]],
    sources: dict[str, str],
) -> dict[str, Any]:
    moment_by_id = {moment.id: moment for moment in moments}
    results: list[dict[str, Any]] = []
    for beat in beats:
        recommendations = []
        for rank, match in enumerate(matches.get(beat.id, []), start=1):
            moment = moment_by_id[match.moment_id]
            recommendations.append({
                "rank": rank,
                "start": moment.start,
                "end": moment.end,
                "start_timecode": format_timecode(moment.start),
                "end_timecode": format_timecode(moment.end),
                "description": moment.description,
                "why": match.why,
                "match_score": match.match_score,
                "story_value_score": match.story_value_score,
                "rank_score": match.rank_score,
                "roles": moment.roles,
                "transcript": moment.transcript,
                "visual_labels": moment.visual_labels,
                "frame_path": moment.frame_path,
            })
        results.append({
            "beat": {
                **beat.to_dict(),
                "start_timecode": format_timecode(beat.start),
                "end_timecode": format_timecode(beat.end),
            },
            "recommendations": recommendations,
        })
    return {"version": "0.1.0", "sources": sources, "results": results}


def _media_url(path: str, start: float, end: float) -> str:
    uri = Path(path).expanduser().resolve().as_uri()
    return f"{uri}#t={start:.3f},{end:.3f}"


def render_report(data: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    gameplay = data.get("sources", {}).get("gameplay", "")
    cards: list[str] = []
    for result in data.get("results", []):
        beat = result["beat"]
        recommendation_html: list[str] = []
        for item in result.get("recommendations", []):
            link = _media_url(gameplay, item["start"], item["end"]) if gameplay else "#"
            labels = ", ".join(item.get("visual_labels", {}).keys()) or "No dominant visual label"
            recommendation_html.append(f"""
            <article class="recommendation">
              <div class="rank">#{item['rank']}</div>
              <div class="clip-body">
                <a class="time" href="{html.escape(link, quote=True)}">{html.escape(item['start_timecode'])}–{html.escape(item['end_timecode'])}</a>
                <h3>{html.escape(item['description'])}</h3>
                <p>{html.escape(item['why'])}</p>
                <p class="evidence">Visual evidence: {html.escape(labels)}</p>
              </div>
              <div class="scores">
                <span><b>{item['match_score']:.1f}</b> match</span>
                <span><b>{item['story_value_score']:.1f}</b> story</span>
              </div>
            </article>""")
        cards.append(f"""
        <section class="beat-card">
          <div class="beat-head">
            <span>{html.escape(beat['start_timecode'])}–{html.escape(beat['end_timecode'])}</span>
            <h2>{html.escape(beat['text'])}</h2>
            <small>{html.escape(', '.join(beat.get('roles', {}).keys()))}</small>
          </div>
          {''.join(recommendation_html) or '<p>No candidate moments found.</p>'}
        </section>""")

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Intro Footage Matcher V0.1</title>
<style>
:root{{--bg:#0b0d12;--panel:#151923;--line:#2a3040;--text:#eef2ff;--muted:#9ba6bd;--accent:#7dd3fc;--hot:#fbbf24}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,sans-serif}}
main{{max-width:1120px;margin:auto;padding:40px 24px 80px}} header{{margin-bottom:32px}} h1{{font-size:34px;margin:0 0 6px}} header p,.evidence,small{{color:var(--muted)}}
.beat-card{{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin:22px 0;overflow:hidden}} .beat-head{{padding:22px 24px;border-bottom:1px solid var(--line)}}
.beat-head span,.time{{color:var(--accent);font-variant-numeric:tabular-nums}} h2{{margin:6px 0;font-size:22px}} .recommendation{{display:grid;grid-template-columns:48px 1fr 120px;gap:16px;padding:20px 24px;border-bottom:1px solid var(--line)}}
.recommendation:last-child{{border-bottom:0}} .rank{{font-size:20px;color:var(--hot);font-weight:800}} h3{{font-size:16px;margin:5px 0}} p{{margin:5px 0}} .scores{{display:flex;flex-direction:column;gap:8px;text-align:right}} .scores b{{font-size:20px}} a{{text-decoration:none}} a:hover{{text-decoration:underline}}
@media(max-width:700px){{.recommendation{{grid-template-columns:36px 1fr}}.scores{{grid-column:2;text-align:left;flex-direction:row}}}}
</style></head><body><main><header><h1>Intro Footage Matcher</h1><p>Local V0.1 · ranked gameplay support for each intro beat</p></header>{''.join(cards)}</main></body></html>"""
    output.write_text(document, encoding="utf-8")
    return output


def write_report_files(data: dict[str, Any], reports_dir: str | Path) -> tuple[Path, Path]:
    root = Path(reports_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "matches.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return json_path, render_report(data, root / "index.html")

