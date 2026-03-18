#!/usr/bin/env python3
"""Prompt Tournament: compare LLM providers via the Concentrate API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID

from api import ConcentrateClient, ConcentrateError
from judge import judge, Verdict
from prompts import TASK_PACK

load_dotenv()

console = Console()
RESULTS_DIR = Path("results")
RESULTS_FILE = RESULTS_DIR / "results.jsonl"

DEFAULT_MODELS = ["openai/gpt-4o", "anthropic/claude-sonnet-4-5"]
TEMPERATURES = [0.3, 0.9]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prompt Tournament CLI")
    p.add_argument(
        "--stream", action="store_true",
        help="Run a single prompt in streaming mode as a demo",
    )
    p.add_argument(
        "--report-only", action="store_true",
        help="Re-generate report.html from existing results.jsonl",
    )
    p.add_argument(
        "--models", nargs=2, default=DEFAULT_MODELS,
        metavar=("MODEL_A", "MODEL_B"),
        help="Two model identifiers to compare (default: %(default)s)",
    )
    p.add_argument(
        "--limit", type=int, default=None,
        help="Only run the first N prompts (for quick testing)",
    )
    return p.parse_args()


def streaming_demo(client: ConcentrateClient, model: str) -> None:
    """Run one prompt in streaming mode to exercise the SSE path."""
    task = TASK_PACK[0]
    console.rule(f"[bold cyan]Streaming Demo: {model}")
    console.print(f"[dim]Prompt:[/dim] {task['prompt_text'][:120]}...")
    console.print()

    gen = client.create_response_stream(
        model=model,
        input_data=task["prompt_text"],
        temperature=0.7,
        max_output_tokens=task["max_tokens"],
    )

    full_text = ""
    try:
        while True:
            delta = next(gen)
            console.print(delta, end="", highlight=False)
            full_text += delta
    except StopIteration as e:
        resp = e.value
    console.print()

    if resp:
        console.print(
            f"\n[green]Done.[/green]  "
            f"model={resp.model}  tokens={resp.usage.total_tokens}  "
            f"latency={resp.latency_ms:.0f}ms"
        )
    else:
        console.print(f"\n[green]Done.[/green] (streamed {len(full_text)} chars)")


def run_tournament(
    client: ConcentrateClient,
    models: list[str],
    limit: int | None = None,
) -> list[dict]:
    """Run all prompts x models x temps, judge each pair, write JSONL."""
    tasks = TASK_PACK[:limit] if limit else TASK_PACK
    model_a, model_b = models
    all_records: list[dict] = []

    total_steps = len(tasks) * len(TEMPERATURES)
    console.rule("[bold cyan]Prompt Tournament")
    console.print(
        f"Models: [bold]{model_a}[/bold] vs [bold]{model_b}[/bold]  |  "
        f"Prompts: {len(tasks)}  |  Temps: {TEMPERATURES}  |  "
        f"Estimated calls: ~{total_steps * 2 + total_steps} "
        f"({total_steps * 2} gen + {total_steps} judge)\n"
    )

    RESULTS_DIR.mkdir(exist_ok=True)
    jsonl = open(RESULTS_FILE, "a", encoding="utf-8")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        bar = progress.add_task("Running tournament...", total=total_steps)

        for task in tasks:
            for temp in TEMPERATURES:
                prompt_id = task["id"]
                prompt_text = task["prompt_text"]
                max_tok = task["max_tokens"]

                progress.update(
                    bar,
                    description=f"[cyan]{prompt_id}[/cyan] temp={temp}",
                )

                # ── Generate from both models ───────────────────
                resp_a = _safe_generate(
                    client, model_a, prompt_text, temp, max_tok, prompt_id
                )
                resp_b = _safe_generate(
                    client, model_b, prompt_text, temp, max_tok, prompt_id
                )

                if resp_a is None or resp_b is None:
                    progress.advance(bar)
                    continue

                # ── Judge ───────────────────────────────────────
                verdict = _safe_judge(
                    client, prompt_text, resp_a, resp_b, model_a, model_b, prompt_id
                )

                # ── Record ──────────────────────────────────────
                record = _build_record(
                    task, temp, model_a, model_b, resp_a, resp_b, verdict
                )
                all_records.append(record)
                jsonl.write(json.dumps(record) + "\n")
                jsonl.flush()

                progress.advance(bar)

    jsonl.close()
    return all_records


def _safe_generate(client, model, prompt_text, temp, max_tok, prompt_id):
    try:
        return client.create_response(
            model=model,
            input_data=prompt_text,
            temperature=temp,
            max_output_tokens=max_tok,
        )
    except ConcentrateError as exc:
        console.print(
            f"  [red]ERROR[/red] {prompt_id} {model} temp={temp}: {exc}"
        )
        return None
    except Exception as exc:
        console.print(
            f"  [red]ERROR[/red] {prompt_id} {model} temp={temp}: {exc}"
        )
        return None


def _safe_judge(client, prompt_text, resp_a, resp_b, model_a, model_b, prompt_id):
    try:
        return judge(client, prompt_text, resp_a.text, resp_b.text, model_a, model_b)
    except Exception as exc:
        console.print(f"  [yellow]JUDGE FAILED[/yellow] {prompt_id}: {exc}")
        return None


def _build_record(task, temp, model_a, model_b, resp_a, resp_b, verdict):
    rec = {
        "prompt_id": task["id"],
        "category": task["category"],
        "prompt_text": task["prompt_text"][:200],
        "temperature": temp,
        "model_a": model_a,
        "model_b": model_b,
        "output_a": resp_a.text[:2000],
        "output_b": resp_b.text[:2000],
        "latency_a_ms": round(resp_a.latency_ms, 1),
        "latency_b_ms": round(resp_b.latency_ms, 1),
        "tokens_a": {
            "input": resp_a.usage.input_tokens,
            "output": resp_a.usage.output_tokens,
            "total": resp_a.usage.total_tokens,
        },
        "tokens_b": {
            "input": resp_b.usage.input_tokens,
            "output": resp_b.usage.output_tokens,
            "total": resp_b.usage.total_tokens,
        },
        "resolved_model_a": resp_a.model,
        "resolved_model_b": resp_b.model,
    }
    if verdict:
        rec["judge"] = {
            "score_a": verdict.score_a,
            "score_b": verdict.score_b,
            "winner": verdict.winner,
            "reasoning": verdict.reasoning[:500],
            "latency_ms": round(verdict.latency_ms, 1),
            "usage": verdict.usage,
        }
    return rec


def print_leaderboard(records: list[dict], models: list[str]) -> None:
    """Print a summary leaderboard table to the console."""
    model_a, model_b = models
    stats: dict[str, dict] = {}
    for m in models:
        stats[m] = {
            "wins": 0, "losses": 0, "ties": 0,
            "total_score": 0, "count": 0,
            "total_latency": 0.0, "total_tokens": 0,
        }

    for r in records:
        j = r.get("judge")
        if not j:
            continue

        for side, model, score_key, lat_key, tok_key in [
            ("a", model_a, "score_a", "latency_a_ms", "tokens_a"),
            ("b", model_b, "score_b", "latency_b_ms", "tokens_b"),
        ]:
            s = stats[model]
            sc = j[score_key]
            total = sc["relevance"] + sc["quality"] + sc["creativity"]
            s["total_score"] += total
            s["count"] += 1
            s["total_latency"] += r[lat_key]
            s["total_tokens"] += r[tok_key]["total"]

            if j["winner"] == side:
                s["wins"] += 1
            elif j["winner"] == "tie":
                s["ties"] += 1
            else:
                s["losses"] += 1

    console.print()
    table = Table(title="Leaderboard", show_lines=True)
    table.add_column("Model", style="bold")
    table.add_column("Wins", justify="right")
    table.add_column("Losses", justify="right")
    table.add_column("Ties", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Avg Score (/30)", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("Total Tokens", justify="right")

    for model in models:
        s = stats[model]
        n = s["count"] or 1
        win_rate = s["wins"] / n * 100
        avg_score = s["total_score"] / n
        avg_lat = s["total_latency"] / n
        table.add_row(
            model,
            str(s["wins"]),
            str(s["losses"]),
            str(s["ties"]),
            f"{win_rate:.1f}%",
            f"{avg_score:.1f}",
            f"{avg_lat:.0f}ms",
            f"{s['total_tokens']:,}",
        )

    console.print(table)


def main():
    args = parse_args()

    if args.report_only:
        from report import generate_report
        generate_report()
        console.print("[green]Report generated at results/report.html[/green]")
        return

    api_key = os.getenv("CONCENTRATE_API_KEY", "")
    if not api_key:
        console.print("[red]Error:[/red] CONCENTRATE_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    with ConcentrateClient(api_key) as client:
        if args.stream:
            streaming_demo(client, args.models[0])
            console.print()
            streaming_demo(client, args.models[1])
            return

        records = run_tournament(client, args.models, limit=args.limit)

        if records:
            print_leaderboard(records, args.models)

            from report import generate_report
            generate_report()
            console.print(
                f"\n[green]Done![/green] {len(records)} matchups recorded to {RESULTS_FILE}"
            )
            console.print("[green]HTML report:[/green] results/report.html")
        else:
            console.print("[yellow]No records produced.[/yellow]")


if __name__ == "__main__":
    main()
