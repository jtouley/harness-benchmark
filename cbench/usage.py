"""Parse Claude Code stream-json transcripts into token usage, and price it."""

from __future__ import annotations

import json
from decimal import ROUND_HALF_EVEN, Decimal

MILLION = Decimal(1_000_000)
MICRO = Decimal("0.000001")
_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
_MODEL_USAGE_KEYS = {
    "inputTokens": "input_tokens",
    "outputTokens": "output_tokens",
    "cacheCreationInputTokens": "cache_creation_input_tokens",
    "cacheReadInputTokens": "cache_read_input_tokens",
}


def parse_transcript(text: str) -> dict:
    """Summarize a `claude -p --output-format stream-json --verbose` transcript."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    assistant = [e for e in events if e.get("type") == "assistant"]

    by_model: dict[str, dict[str, int]] = {}
    if result and isinstance(result.get("modelUsage"), dict):
        for model, row in sorted(result["modelUsage"].items()):
            by_model[model] = {dst: int(row.get(src) or 0) for src, dst in _MODEL_USAGE_KEYS.items()}
    else:
        # Fallback: sum per-message usage, counting each message id once.
        seen = set()
        for event in assistant:
            msg = event.get("message") or {}
            mid = msg.get("id")
            if mid in seen:
                continue
            seen.add(mid)
            usage = msg.get("usage") or {}
            row = by_model.setdefault(msg.get("model", "unknown"), {f: 0 for f in _FIELDS})
            for f in _FIELDS:
                row[f] += int(usage.get(f) or 0)

    first_input = None
    if assistant:
        usage = (assistant[0].get("message") or {}).get("usage") or {}
        first_input = sum(int(usage.get(f) or 0) for f in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))

    tool_uses: dict[str, int] = {}
    for event in assistant:
        for block in (event.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_uses[block.get("name", "?")] = tool_uses.get(block.get("name", "?"), 0) + 1

    totals = {f: sum(row[f] for row in by_model.values()) for f in _FIELDS}
    return {
        "by_model": by_model,
        "totals": totals,
        "first_request_input_tokens": first_input,
        "num_turns": result.get("num_turns") if result else None,
        "result_subtype": result.get("subtype") if result else None,
        "is_error": result.get("is_error") if result else None,
        "reported_cost_usd": result.get("total_cost_usd") if result else None,
        "tool_uses": dict(sorted(tool_uses.items())),
    }


def price_key(model: str, pricing: dict) -> str | None:
    """Map a reported model id (may carry suffixes like '[1m]' or a date) onto pricing.json."""
    base = model.split("[", 1)[0]
    if base in pricing["models"]:
        return base
    hits = [k for k in pricing["models"] if base.startswith(k)]
    return max(hits, key=len) if hits else None


def cost_usd(by_model: dict, pricing: dict) -> str | None:
    total = Decimal(0)
    for model, row in by_model.items():
        key = price_key(model, pricing)
        if key is None:
            return None
        p = pricing["models"][key]
        total += (
            Decimal(row["input_tokens"]) * Decimal(p["input"])
            + Decimal(row["output_tokens"]) * Decimal(p["output"])
            + Decimal(row["cache_creation_input_tokens"]) * Decimal(p["cache_write_5m"])
            + Decimal(row["cache_read_input_tokens"]) * Decimal(p["cache_read"])
        ) / MILLION
    return format(total.quantize(MICRO, rounding=ROUND_HALF_EVEN), "f")
