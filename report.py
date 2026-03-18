"""Generate a standalone HTML report from results.jsonl."""

from __future__ import annotations

import json
import html as html_mod
from pathlib import Path
from collections import defaultdict

RESULTS_FILE = Path("results/results.jsonl")
REPORT_FILE = Path("results/report.html")


def _load_records() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    records = []
    for line in RESULTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _esc(text: str) -> str:
    return html_mod.escape(text)


def _compute_stats(records: list[dict]) -> dict:
    models: dict[str, dict] = {}

    for r in records:
        j = r.get("judge")
        if not j:
            continue
        for side, m_key, sc_key, lat_key, tok_key in [
            ("a", "model_a", "score_a", "latency_a_ms", "tokens_a"),
            ("b", "model_b", "score_b", "latency_b_ms", "tokens_b"),
        ]:
            model = r[m_key]
            if model not in models:
                models[model] = {
                    "wins": 0, "losses": 0, "ties": 0,
                    "scores": [], "latencies": [], "tokens": 0,
                }
            s = models[model]
            sc = j[sc_key]
            total = sc["relevance"] + sc["quality"] + sc["creativity"]
            s["scores"].append(total)
            s["latencies"].append(r[lat_key])
            s["tokens"] += r[tok_key]["total"]

            if j["winner"] == side:
                s["wins"] += 1
            elif j["winner"] == "tie":
                s["ties"] += 1
            else:
                s["losses"] += 1

    return models


def _compute_category_stats(records: list[dict]) -> dict:
    cats: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        j = r.get("judge")
        if not j:
            continue
        cat = r["category"]
        for side, m_key, sc_key in [
            ("a", "model_a", "score_a"),
            ("b", "model_b", "score_b"),
        ]:
            model = r[m_key]
            sc = j[sc_key]
            total = sc["relevance"] + sc["quality"] + sc["creativity"]
            cats[cat][model].append(total)
    return dict(cats)


def generate_report() -> None:
    records = _load_records()
    if not records:
        REPORT_FILE.write_text("<h1>No results yet.</h1>", encoding="utf-8")
        return

    stats = _compute_stats(records)
    cat_stats = _compute_category_stats(records)

    leaderboard_rows = ""
    for model, s in sorted(stats.items(), key=lambda x: x[1]["wins"], reverse=True):
        n = len(s["scores"]) or 1
        win_rate = s["wins"] / n * 100
        avg_score = sum(s["scores"]) / n
        avg_lat = sum(s["latencies"]) / n
        leaderboard_rows += f"""
        <tr>
          <td class="model">{_esc(model)}</td>
          <td>{s['wins']}</td>
          <td>{s['losses']}</td>
          <td>{s['ties']}</td>
          <td><strong>{win_rate:.1f}%</strong></td>
          <td>{avg_score:.1f} / 30</td>
          <td>{avg_lat:,.0f} ms</td>
          <td>{s['tokens']:,}</td>
        </tr>"""

    cat_html = ""
    categories = sorted(cat_stats.keys())
    for cat in categories:
        model_scores = cat_stats[cat]
        bars = ""
        for model, scores in sorted(model_scores.items()):
            avg = sum(scores) / len(scores) if scores else 0
            pct = avg / 30 * 100
            bars += f"""
            <div class="bar-row">
              <span class="bar-label">{_esc(model)}</span>
              <div class="bar-track">
                <div class="bar-fill" style="width:{pct:.1f}%"></div>
              </div>
              <span class="bar-value">{avg:.1f}</span>
            </div>"""
        cat_html += f"""
        <div class="cat-card">
          <h3>{_esc(cat.title())}</h3>
          {bars}
        </div>"""

    matchup_cards = ""
    for i, r in enumerate(records):
        j = r.get("judge")
        winner_badge_a = ""
        winner_badge_b = ""
        judge_html = "<p class='no-judge'>Judge failed for this matchup.</p>"

        if j:
            if j["winner"] == "a":
                winner_badge_a = " winner"
            elif j["winner"] == "b":
                winner_badge_b = " winner"

            judge_html = f"""
            <div class="verdict">
              <span class="winner-tag">Winner: <strong>{_esc(j['winner'].upper())}</strong></span>
              <table class="score-table">
                <tr><th></th><th>Rel</th><th>Qual</th><th>Cre</th><th>Total</th></tr>
                <tr>
                  <td>A</td>
                  <td>{j['score_a']['relevance']}</td>
                  <td>{j['score_a']['quality']}</td>
                  <td>{j['score_a']['creativity']}</td>
                  <td><strong>{j['score_a']['relevance']+j['score_a']['quality']+j['score_a']['creativity']}</strong></td>
                </tr>
                <tr>
                  <td>B</td>
                  <td>{j['score_b']['relevance']}</td>
                  <td>{j['score_b']['quality']}</td>
                  <td>{j['score_b']['creativity']}</td>
                  <td><strong>{j['score_b']['relevance']+j['score_b']['quality']+j['score_b']['creativity']}</strong></td>
                </tr>
              </table>
              <p class="judge-reasoning">{_esc(j['reasoning'])}</p>
            </div>"""

        matchup_cards += f"""
        <details class="matchup">
          <summary>
            <span class="matchup-id">{_esc(r['prompt_id'])}</span>
            <span class="matchup-cat">{_esc(r['category'])}</span>
            <span class="matchup-temp">temp={r['temperature']}</span>
            {f'<span class="matchup-winner">Winner: {_esc(j["winner"].upper())}</span>' if j else ''}
          </summary>
          <div class="matchup-body">
            <p class="prompt-text">{_esc(r['prompt_text'])}</p>
            <div class="outputs">
              <div class="output-card{winner_badge_a}">
                <h4>A: {_esc(r['model_a'])} <span class="meta">{r['latency_a_ms']:.0f}ms &middot; {r['tokens_a']['total']} tok</span></h4>
                <pre>{_esc(r['output_a'])}</pre>
              </div>
              <div class="output-card{winner_badge_b}">
                <h4>B: {_esc(r['model_b'])} <span class="meta">{r['latency_b_ms']:.0f}ms &middot; {r['tokens_b']['total']} tok</span></h4>
                <pre>{_esc(r['output_b'])}</pre>
              </div>
            </div>
            {judge_html}
          </div>
        </details>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prompt Tournament Report</title>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --dim: #8b8fa3;
    --accent: #6c8cff;
    --green: #4ade80;
    --red: #f87171;
    --yellow: #fbbf24;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.6; padding: 2rem; max-width: 1100px; margin: 0 auto;
  }}
  h1 {{ font-size: 1.8rem; margin-bottom: .5rem; }}
  h2 {{ font-size: 1.3rem; margin: 2rem 0 1rem; color: var(--accent); }}
  h3 {{ font-size: 1rem; margin-bottom: .5rem; }}
  .subtitle {{ color: var(--dim); margin-bottom: 2rem; }}

  table {{ width:100%; border-collapse:collapse; margin-bottom:1rem; }}
  th, td {{ padding: .6rem .8rem; text-align:left; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--dim); font-size: .85rem; text-transform: uppercase; letter-spacing: .05em; }}
  td.model {{ font-weight: 600; color: var(--accent); }}

  .cat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }}
  .cat-card {{ background: var(--surface); border-radius: 8px; padding: 1rem; }}
  .bar-row {{ display:flex; align-items:center; gap:.5rem; margin:.4rem 0; }}
  .bar-label {{ width:180px; font-size:.8rem; color:var(--dim); text-align:right; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .bar-track {{ flex:1; height:18px; background:var(--border); border-radius:4px; overflow:hidden; }}
  .bar-fill {{ height:100%; background:var(--accent); border-radius:4px; transition:width .3s; }}
  .bar-value {{ width:40px; font-size:.8rem; color:var(--text); }}

  .matchup {{ background: var(--surface); border-radius: 8px; margin-bottom: .6rem; }}
  .matchup summary {{
    padding: .8rem 1rem; cursor: pointer; display:flex; gap:1rem; align-items:center; flex-wrap:wrap;
    list-style: none; font-size: .9rem;
  }}
  .matchup summary::-webkit-details-marker {{ display:none; }}
  .matchup summary::before {{ content:'\\25B6'; margin-right:.3rem; font-size:.7rem; color:var(--dim); }}
  .matchup[open] summary::before {{ content:'\\25BC'; }}
  .matchup-id {{ font-weight:600; color:var(--accent); }}
  .matchup-cat {{ background:var(--border); padding:2px 8px; border-radius:4px; font-size:.75rem; }}
  .matchup-temp {{ color:var(--dim); font-size:.8rem; }}
  .matchup-winner {{ margin-left:auto; font-weight:600; color:var(--green); font-size:.8rem; }}
  .matchup-body {{ padding: 0 1rem 1rem; }}
  .prompt-text {{ font-size:.85rem; color:var(--dim); margin-bottom:1rem; white-space:pre-wrap; }}

  .outputs {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1rem; }}
  @media (max-width:700px) {{ .outputs {{ grid-template-columns:1fr; }} }}
  .output-card {{
    background: var(--bg); border-radius:6px; padding:.8rem; border: 1px solid var(--border);
  }}
  .output-card.winner {{ border-color: var(--green); }}
  .output-card h4 {{ font-size:.85rem; margin-bottom:.5rem; }}
  .output-card .meta {{ color:var(--dim); font-weight:normal; font-size:.75rem; }}
  .output-card pre {{
    font-size:.8rem; white-space:pre-wrap; word-break:break-word;
    max-height:300px; overflow-y:auto; color:var(--text);
  }}

  .verdict {{ background: var(--bg); border-radius:6px; padding:.8rem; }}
  .winner-tag {{ font-size:.9rem; color:var(--green); }}
  .score-table {{ width:auto; margin:.5rem 0; }}
  .score-table th, .score-table td {{ padding:.3rem .6rem; font-size:.8rem; }}
  .judge-reasoning {{ font-size:.8rem; color:var(--dim); margin-top:.5rem; }}
  .no-judge {{ color:var(--yellow); font-size:.85rem; }}

  .footer {{ margin-top:3rem; text-align:center; color:var(--dim); font-size:.8rem; }}
</style>
</head>
<body>
  <h1>Prompt Tournament Report</h1>
  <p class="subtitle">{len(records)} matchups across {len(set(r['category'] for r in records))} categories</p>

  <h2>Leaderboard</h2>
  <table>
    <thead>
      <tr><th>Model</th><th>Wins</th><th>Losses</th><th>Ties</th><th>Win Rate</th><th>Avg Score</th><th>Avg Latency</th><th>Total Tokens</th></tr>
    </thead>
    <tbody>{leaderboard_rows}</tbody>
  </table>

  <h2>Category Breakdown</h2>
  <div class="cat-grid">{cat_html}</div>

  <h2>Matchup Details</h2>
  {matchup_cards}

  <p class="footer">Generated by Prompt Tournament CLI &middot; Powered by Concentrate AI</p>
</body>
</html>"""

    REPORT_FILE.parent.mkdir(exist_ok=True)
    REPORT_FILE.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    generate_report()
    print(f"Report written to {REPORT_FILE}")
