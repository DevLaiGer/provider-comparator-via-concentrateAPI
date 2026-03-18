"""Concentrate AI API client with retry logic and streaming support."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Generator

import httpx

BASE_URL = "https://api.concentrate.ai/v1"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass
class Response:
    id: str
    model: str
    text: str
    usage: Usage
    latency_ms: float
    status: str = "completed"
    raw: dict = field(default_factory=dict)


class ConcentrateError(Exception):
    def __init__(self, status_code: int, message: str, raw: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}
        super().__init__(f"[{status_code}] {message}")


class ConcentrateClient:
    def __init__(self, api_key: str, timeout: float = 120.0):
        self.api_key = api_key
        self.http = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def close(self):
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def create_response(
        self,
        model: str,
        input_data: str | list[dict],
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        text_format: dict | None = None,
    ) -> Response:
        body: dict = {"model": model, "input": input_data}
        if temperature is not None:
            body["temperature"] = temperature
        if max_output_tokens is not None:
            body["max_output_tokens"] = max_output_tokens
        if text_format is not None:
            body["text"] = {"format": text_format}

        return self._post_with_retry(body)

    def create_response_stream(
        self,
        model: str,
        input_data: str | list[dict],
        *,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> Generator[str, None, Response]:
        """Yields text deltas as they arrive; returns the final Response."""
        body: dict = {
            "model": model,
            "input": input_data,
            "stream": True,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_output_tokens is not None:
            body["max_output_tokens"] = max_output_tokens

        t0 = time.perf_counter()
        full_text = ""
        resp_id = ""
        resp_model = model
        usage = Usage()

        with self.http.stream("POST", "/responses", json=body) as stream:
            if stream.status_code != 200:
                raw = stream.read().decode()
                raise ConcentrateError(stream.status_code, raw)

            for line in stream.iter_lines():
                if not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                evt_type = data.get("type", "")

                if evt_type == "response.output_text.delta":
                    delta = data.get("delta", "")
                    full_text += delta
                    yield delta

                elif evt_type == "response.completed":
                    resp_obj = data.get("response", {})
                    resp_id = resp_obj.get("id", "")
                    resp_model = resp_obj.get("model", model)
                    u = resp_obj.get("usage", {})
                    usage = Usage(
                        input_tokens=u.get("input_tokens", 0),
                        output_tokens=u.get("output_tokens", 0),
                        total_tokens=u.get("total_tokens", 0),
                    )

        latency_ms = (time.perf_counter() - t0) * 1000
        return Response(
            id=resp_id,
            model=resp_model,
            text=full_text,
            usage=usage,
            latency_ms=latency_ms,
        )

    # ── internal ────────────────────────────────────────────────────

    def _post_with_retry(self, body: dict) -> Response:
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                backoff = INITIAL_BACKOFF * (2 ** (attempt - 1))
                time.sleep(backoff)
            try:
                return self._post(body)
            except ConcentrateError as exc:
                last_exc = exc
                if exc.status_code not in RETRYABLE_STATUS_CODES:
                    raise
            except httpx.TransportError as exc:
                last_exc = exc
        raise last_exc  # type: ignore[misc]

    def _post(self, body: dict) -> Response:
        t0 = time.perf_counter()
        r = self.http.post("/responses", json=body)
        latency_ms = (time.perf_counter() - t0) * 1000

        if r.status_code != 200:
            try:
                raw = r.json()
            except Exception:
                raw = {"raw_text": r.text}
            msg = raw.get("error", {}).get("message", r.text) if isinstance(raw, dict) else r.text
            raise ConcentrateError(r.status_code, msg, raw)

        data = r.json()
        text = _extract_text(data)
        u = data.get("usage", {})
        usage = Usage(
            input_tokens=u.get("input_tokens", 0),
            output_tokens=u.get("output_tokens", 0),
            total_tokens=u.get("total_tokens", 0),
        )
        return Response(
            id=data.get("id", ""),
            model=data.get("model", body.get("model", "")),
            text=text,
            usage=usage,
            latency_ms=latency_ms,
            raw=data,
        )


def _extract_text(data: dict) -> str:
    """Pull the assistant text out of the normalized response envelope."""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    return part.get("text", "")
    return ""
