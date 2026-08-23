"""Pluggable LLM backend for loop nodes. Only a deterministic mock ships
today — a real provider adapter (Anthropic/OpenAI) can implement the same
protocol later without changing any node logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelResponse:
    """Result of one model call. `text` is provider output; mock nodes never
    read it — they derive their behavior from loop state instead."""

    text: str
    tokens_in: int
    tokens_out: int
    cost: float
    latency_ms: float


class ModelClient(Protocol):
    def complete(self, prompt: str) -> ModelResponse: ...


class MockModelClient:
    """Deterministic stand-in for a real model call: pure arithmetic over
    the prompt length, no `time.sleep`, no randomness. The same prompt
    always produces the same response, so loop execution is reproducible."""

    def __init__(
        self,
        cost_per_token: float = 2e-6,
        base_latency_ms: float = 50.0,
        ms_per_output_token: float = 2.0,
    ) -> None:
        self.cost_per_token = cost_per_token
        self.base_latency_ms = base_latency_ms
        self.ms_per_output_token = ms_per_output_token

    def complete(self, prompt: str) -> ModelResponse:
        tokens_in = max(1, len(prompt) // 4)
        tokens_out = max(1, tokens_in // 2)
        cost = (tokens_in + tokens_out) * self.cost_per_token
        latency_ms = self.base_latency_ms + tokens_out * self.ms_per_output_token

        return ModelResponse(
            text=f"[mock:{len(prompt)}]",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            latency_ms=latency_ms,
        )
