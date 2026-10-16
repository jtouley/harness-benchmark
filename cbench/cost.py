"""Price an agent session per request, each request at its own price tier.

Some models have a price tier set per request: Haiku 5.5 costs 5 times more for a request whose prompt
(input + cache read + cache write) is above 100K tokens. A price from session totals cannot know which
requests were above the line, so for such a model it is not a number. This module:

- reads per-request usage from Claude Code transcripts (stream JSON on stdout, or the session logs under
  ``~/.claude/projects``, subagent logs included), one record per API response;
- prices each request at the tier its own prompt size selects (``pricing.json`` + ``pricing_tiers.json``);
- checks the requests against the session totals (``result.json`` ``modelUsage``) when they are given;
- from totals alone, prices a model with no tier exactly, and gives a model with a tier only a lower and
  an upper bound, labelled as such, never one number.

Standard library only, so shell scripts can run it with a bare ``python3``:

    python3 -m cbench.cost RUN_DIR_OR_JSONL... [--result result.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICING_PATH = ROOT / "pricing.json"
TIERS_PATH = ROOT / "pricing_tiers.json"

FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
MILLION = Decimal(1_000_000)
CENT_FRACTION = Decimal("0.000001")


class PricingError(ValueError):
    """A token count with no price, or session data that cannot give a price."""


# --- prices ------------------------------------------------------------------------------------------

def load_prices(pricing_path: Path = PRICING_PATH, tiers_path: Path = TIERS_PATH) -> dict:
    """{model: {"base": {field: Decimal}, "tiers": [(above_prompt_tokens, {field: Decimal}), ...]}}."""
    base = json.loads(pricing_path.read_text(encoding="utf-8"))["models"]
    extra = json.loads(tiers_path.read_text(encoding="utf-8"))["models"] if tiers_path.exists() else {}
    prices = {}
    for model, p in base.items():
        more = extra.get(model, {})
        row = {k: Decimal(v) for k, v in p.items() if k in FIELDS}
        if "cache_write_1h" in more:
            row["cache_write_1h"] = Decimal(more["cache_write_1h"])
        tiers = sorted(((int(t["above_prompt_tokens"]), {k: Decimal(v) for k, v in t.items() if k in FIELDS})
                        for t in more.get("tiers", [])), key=lambda t: t[0])
        prices[model] = {"base": row, "tiers": tiers}
    return prices


def resolve_model(model: str, prices: dict) -> str | None:
    """The pricing key for a model id as a host reports it (``[1m]`` suffix, dated snapshot)."""
    name = re.sub(r"\[.*\]$", "", model)
    for candidate in (name, re.sub(r"-\d{8}$", "", name)):
        if candidate in prices:
            return candidate
    return None


def tier_for(prompt_tokens: int, entry: dict) -> tuple[str, dict]:
    """The tier name and prices for a request with this many prompt tokens."""
    name, row = "base", entry["base"]
    for above, tier in entry["tiers"]:
        if prompt_tokens > above:
            name, row = f"above_{above}", {**entry["base"], **tier}
    return name, row


def _usd(tokens: dict, row: dict) -> Decimal:
    total = Decimal(0)
    for k in FIELDS:
        n = tokens.get(k, 0)
        if not n:
            continue
        if k not in row:
            raise PricingError(f"{n} {k} tokens have no price")
        total += n * row[k]
    return total / MILLION


# --- requests ----------------------------------------------------------------------------------------

@dataclass
class Request:
    model: str
    key: str
    tokens: dict = field(default_factory=lambda: dict.fromkeys(FIELDS, 0))
    sidechain: bool = False

    @property
    def prompt_tokens(self) -> int:
        t = self.tokens
        return t["input"] + t["cache_read"] + t["cache_write_5m"] + t["cache_write_1h"]


def usage_tokens(u: dict) -> dict:
    """API ``usage`` -> our fields. Cache writes split by TTL when the host reports the split."""
    written = u.get("cache_creation_input_tokens") or 0
    split = u.get("cache_creation") or {}
    w5m, w1h = split.get("ephemeral_5m_input_tokens") or 0, split.get("ephemeral_1h_input_tokens") or 0
    if w5m + w1h != written:  # no split, or one that does not add up: price every write as 5-minute
        w5m, w1h = written, 0
    return {"input": u.get("input_tokens") or 0, "cache_write_5m": w5m, "cache_write_1h": w1h,
            "cache_read": u.get("cache_read_input_tokens") or 0, "output": u.get("output_tokens") or 0}


def _assistant_message(entry: dict) -> dict | None:
    if entry.get("type") != "assistant":
        return None
    msg = entry.get("message")
    return msg if isinstance(msg, dict) and isinstance(msg.get("usage"), dict) else None


def jsonl_files(paths: list[Path]) -> list[Path]:
    """Every ``.jsonl`` under the given paths: a run dir's ``transcript.jsonl`` and ``claude-projects/``."""
    out = []
    for p in paths:
        if p.is_dir():
            out += sorted(f for f in p.rglob("*.jsonl") if f.is_file())
        elif p.is_file():
            out.append(p)
    return out


def read_requests(paths: list[Path]) -> list[Request]:
    """One record per API response, from any mix of stream JSON and session logs.

    Claude Code writes one line per content block, each line repeating the response's usage (stream JSON
    can show a partial ``output_tokens`` on early blocks), and the same response can appear in both the
    stdout transcript and the session log. So lines are merged by message id (else request id), keeping
    the largest count of each field.
    """
    by_key: dict[str, Request] = {}
    anonymous = 0
    for f in jsonl_files(paths):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            msg = _assistant_message(entry) if isinstance(entry, dict) else None
            if msg is None:
                continue
            model = msg.get("model") or "unknown"
            tokens = usage_tokens(msg["usage"])
            if model == "<synthetic>" and not any(tokens.values()):
                continue  # a host-written message, not an API response
            key = msg.get("id") or entry.get("requestId")
            if not key:
                anonymous += 1
                key = f"{f}:{anonymous}"
            req = by_key.setdefault(key, Request(model=model, key=key))
            req.tokens = {k: max(req.tokens[k], tokens[k]) for k in FIELDS}
            req.sidechain |= bool(entry.get("isSidechain") or entry.get("parent_tool_use_id"))
    return list(by_key.values())


# --- pricing a session -------------------------------------------------------------------------------

def _q(d: Decimal | None) -> str | None:
    return None if d is None else format(d.quantize(CENT_FRACTION), "f")


def total_tokens(model_usage_entry: dict) -> dict:
    """Claude Code ``modelUsage`` entry (camelCase) -> our fields. Totals carry no TTL split."""
    u = model_usage_entry
    return {"input": u.get("inputTokens", 0) or 0, "cache_write_5m": u.get("cacheCreationInputTokens", 0) or 0,
            "cache_write_1h": 0, "cache_read": u.get("cacheReadInputTokens", 0) or 0,
            "output": u.get("outputTokens", 0) or 0}


def price_totals(model_usage: dict, prices: dict) -> dict:
    """From session totals only. A model with a tier gets bounds (all requests in the lowest tier, all in
    the highest), labelled, and ``usd`` None; a model with no tier is exact."""
    by_model, lower, upper = {}, Decimal(0), Decimal(0)
    for model, u in model_usage.items():
        tokens = total_tokens(u)
        key = resolve_model(model, prices)
        if key is None:
            if any(tokens.values()):
                raise PricingError(f"no price for model {model!r}")
            continue
        entry = prices[key]
        lo = _usd(tokens, entry["base"])
        hi = _usd(tokens, tier_for(sys.maxsize, entry)[1])
        by_model[model] = {"tokens": tokens, "usd_lower": _q(lo), "usd_upper": _q(hi),
                           "usd": _q(lo) if lo == hi else None}
        lower, upper = lower + lo, upper + hi
    exact = lower == upper
    return {"method": "totals", "exact": exact, "usd": _q(lower) if exact else None,
            "usd_lower": _q(lower), "usd_upper": _q(upper),
            "label": None if exact else "bounds: session totals only, a model here has a price tier per request",
            "by_model": by_model}


def price_requests(requests: list[Request], prices: dict, model_usage: dict | None = None) -> dict:
    """Price each request at its own tier. With ``model_usage`` (the session totals), check that the
    requests account for every token: tokens the records miss are priced as bounds, and records that add
    up to more than the totals (a record read twice) make the result not a number."""
    by_model: dict[str, dict] = {}
    for r in requests:
        key = resolve_model(r.model, prices)
        if key is None:
            if any(r.tokens.values()):
                raise PricingError(f"no price for model {r.model!r}")
            continue
        tier, row = tier_for(r.prompt_tokens, prices[key])
        usd = _usd(r.tokens, row)
        m = by_model.setdefault(r.model, {"requests": 0, "subagent_requests": 0, "max_prompt_tokens": 0,
                                          "tokens": dict.fromkeys(FIELDS, 0), "by_tier": {}, "usd": Decimal(0)})
        m["requests"] += 1
        m["subagent_requests"] += r.sidechain
        m["max_prompt_tokens"] = max(m["max_prompt_tokens"], r.prompt_tokens)
        for k in FIELDS:
            m["tokens"][k] += r.tokens[k]
        t = m["by_tier"].setdefault(tier, {"requests": 0, "usd": Decimal(0)})
        t["requests"] += 1
        t["usd"] += usd
        m["usd"] += usd

    lower = upper = sum((m["usd"] for m in by_model.values()), Decimal(0))
    notes, overcount = [], False
    if model_usage is not None:
        want_by_key: dict[str, dict] = {}
        for model, u in model_usage.items():
            key = resolve_model(model, prices)
            if key is None:
                if any(total_tokens(u).values()):
                    raise PricingError(f"no price for model {model!r}")
                continue
            w = want_by_key.setdefault(key, dict.fromkeys(FIELDS, 0))
            for k, n in total_tokens(u).items():
                w[k] += n
        have_by_key: dict[str, dict] = {}
        for model, m in by_model.items():
            h = have_by_key.setdefault(resolve_model(model, prices), dict.fromkeys(FIELDS, 0))
            for k in FIELDS:  # totals do not split cache writes by TTL: compare all writes together
                h["cache_write_5m" if k == "cache_write_1h" else k] += m["tokens"][k]
        for key in sorted(set(want_by_key) | set(have_by_key)):
            want = want_by_key.get(key, dict.fromkeys(FIELDS, 0))
            have = have_by_key.get(key, dict.fromkeys(FIELDS, 0))
            over = {k: have[k] - want[k] for k in FIELDS if have[k] > want[k]}
            missing = {k: want[k] - have[k] for k in FIELDS if want[k] > have[k]}
            if over:
                overcount = True
                notes.append(f"{key}: the request records exceed the session totals by {over}")
            if missing:
                lower += _usd(missing, prices[key]["base"])
                upper += _usd(missing, tier_for(sys.maxsize, prices[key])[1])
                notes.append(f"{key}: the request records miss {missing} of the session totals")
    for m in by_model.values():
        m["usd"] = _q(m["usd"])
        for t in m["by_tier"].values():
            t["usd"] = _q(t["usd"])
    exact = not overcount and lower == upper
    return {"method": "per_request", "exact": exact,
            "usd": _q(lower) if exact else None,
            "usd_lower": None if overcount else _q(lower), "usd_upper": None if overcount else _q(upper),
            "label": None if exact else "; ".join(notes), "notes": notes,
            "requests": sum(m["requests"] for m in by_model.values()), "by_model": by_model,
            "checked_against_totals": model_usage is not None}


def price_session(paths: list[Path], prices: dict, model_usage: dict | None = None) -> dict:
    """Per request when the paths hold request records; otherwise from the totals, as bounds."""
    requests = read_requests(paths)
    if requests:
        return price_requests(requests, prices, model_usage)
    if model_usage:
        return price_totals(model_usage, prices)
    return {"method": "none", "exact": True, "usd": _q(Decimal(0)), "usd_lower": _q(Decimal(0)),
            "usd_upper": _q(Decimal(0)), "label": None, "by_model": {}}


def display(cost: dict) -> str:
    """One cell for a results table: the price, or the labelled bounds."""
    if cost.get("usd") is not None:
        return f"${Decimal(cost['usd']):.2f}"
    if cost.get("usd_lower") is not None:
        return f"${Decimal(cost['usd_lower']):.2f}–${Decimal(cost['usd_upper']):.2f} (bounds)"
    return "no price (see label)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m cbench.cost", description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", type=Path, help="transcript .jsonl files or dirs holding them")
    ap.add_argument("--result", type=Path, help="Claude Code result.json: check the requests against its modelUsage")
    args = ap.parse_args(argv)
    usage = None
    if args.result:
        usage = json.loads(args.result.read_text(encoding="utf-8") or "{}").get("modelUsage") or None
    try:
        out = price_session(args.paths, load_prices(), usage)
    except PricingError as e:
        print(f"cost: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0 if out["exact"] else 1


if __name__ == "__main__":
    sys.exit(main())
