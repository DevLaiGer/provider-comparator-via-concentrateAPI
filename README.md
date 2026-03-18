# Prompt Tournament - Provider Comparator via Concentrate AI

A CLI tool that pits two LLM providers against each other on the same prompts, uses a third LLM call as a judge, and generates an HTML leaderboard report. Built on the [Concentrate AI](https://docs.concentrate.ai) unified API.

## What it does

1. Sends 15 prompts (across 5 categories) to **two models** at **two temperature settings** each
2. An **LLM judge** (via structured output) scores both responses on relevance, quality, and creativity (1–10 each)
3. Results are saved to `results/results.jsonl` and rendered into a standalone `results/report.html`

This produces ~90 API calls per run (60 generation + 30 judge).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Concentrate API key
```

## Usage

```bash
# Full tournament (all 15 prompts × 2 temperatures × 2 models + judge)
python main.py

# Quick test with first N prompts
python main.py --limit 3

# Streaming demo (prints tokens live from both models)
python main.py --stream

# Re-generate HTML report from existing results
python main.py --report-only

# Use different models
python main.py --models openai/gpt-4o-mini anthropic/claude-haiku-4-5
```

## Project structure

| File | Purpose |
|---|---|
| `main.py` | CLI entry point, tournament loop, leaderboard display |
| `api.py` | `ConcentrateClient` - handles `/v1/responses`, retries, streaming |
| `prompts.py` | 15 task prompts across rewriting, extraction, creative, reasoning, code |
| `judge.py` | LLM-as-judge with structured JSON output schema |
| `report.py` | Generates standalone `report.html` with leaderboard + matchup details |

## API features exercised

- `/v1/responses` endpoint (non-streaming and SSE streaming)
- Provider-prefixed model selection (`openai/...`, `anthropic/...`)
- Structured output (`text.format.type: "json_schema"`)
- Temperature parameter sweeps (0.3 and 0.9)
- `max_output_tokens` control
- Conversation format input (system + user messages)
- Token usage tracking from response metadata
- Error handling and retry with exponential backoff
