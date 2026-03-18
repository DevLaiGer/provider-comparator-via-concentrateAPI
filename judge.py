"""LLM-as-judge: scores two outputs via structured output from Concentrate."""

from __future__ import annotations

import json
from dataclasses import dataclass

from api import ConcentrateClient, Response

JUDGE_MODEL = "openai/gpt-4o-mini"
JUDGE_TEMPERATURE = 0.2
JUDGE_MAX_TOKENS = 600

JUDGE_SCHEMA = {
    "type": "json_schema",
    "name": "judge_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "score_a": {
                "type": "object",
                "properties": {
                    "relevance": {"type": "integer"},
                    "quality": {"type": "integer"},
                    "creativity": {"type": "integer"},
                },
                "required": ["relevance", "quality", "creativity"],
                "additionalProperties": False,
            },
            "score_b": {
                "type": "object",
                "properties": {
                    "relevance": {"type": "integer"},
                    "quality": {"type": "integer"},
                    "creativity": {"type": "integer"},
                },
                "required": ["relevance", "quality", "creativity"],
                "additionalProperties": False,
            },
            "winner": {"type": "string", "enum": ["a", "b", "tie"]},
            "reasoning": {"type": "string"},
        },
        "required": ["score_a", "score_b", "winner", "reasoning"],
        "additionalProperties": False,
    },
}

JUDGE_SYSTEM_PROMPT = (
    "You are an expert judge evaluating two AI-generated responses to the same prompt. "
    "Score each response on three dimensions (1-10 scale):\n"
    "  - relevance: how well it addresses the prompt\n"
    "  - quality: correctness, clarity, polish\n"
    "  - creativity: originality, insight, elegance\n"
    "Pick a winner ('a', 'b', or 'tie') and explain your reasoning briefly."
)


@dataclass
class Verdict:
    score_a: dict[str, int]
    score_b: dict[str, int]
    winner: str
    reasoning: str
    usage: dict
    latency_ms: float


def judge(
    client: ConcentrateClient,
    prompt_text: str,
    output_a: str,
    output_b: str,
    model_a: str,
    model_b: str,
) -> Verdict:
    user_msg = (
        f"## Original Prompt\n{prompt_text}\n\n"
        f"## Response A (from {model_a})\n{output_a}\n\n"
        f"## Response B (from {model_b})\n{output_b}"
    )

    resp: Response = client.create_response(
        model=JUDGE_MODEL,
        input_data=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=JUDGE_TEMPERATURE,
        max_output_tokens=JUDGE_MAX_TOKENS,
        text_format=JUDGE_SCHEMA,
    )

    parsed = json.loads(resp.text)

    return Verdict(
        score_a=parsed["score_a"],
        score_b=parsed["score_b"],
        winner=parsed["winner"],
        reasoning=parsed["reasoning"],
        usage={
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "total_tokens": resp.usage.total_tokens,
        },
        latency_ms=resp.latency_ms,
    )
