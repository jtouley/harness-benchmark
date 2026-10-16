"""cbench/cost.py: each request is priced at its own tier; totals alone give bounds, never one number.

Haiku 5.5 costs $0.10 / $0.50 per million tokens for a prompt up to 100K tokens and $0.50 / $2.50 above.
"""

from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from cbench import cost

ROOT = Path(__file__).resolve().parents[1]
PRICES = cost.load_prices()
HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"


def assistant(msg_id: str, model: str, *, input=0, cache_write=0, cache_read=0, output=0,
              split: dict | None = None, **entry) -> dict:
    usage = {"input_tokens": input, "cache_creation_input_tokens": cache_write,
             "cache_read_input_tokens": cache_read, "output_tokens": output}
    if split is not None:
        usage["cache_creation"] = split
    return {"type": "assistant", "message": {"id": msg_id, "model": model, "usage": usage}, **entry}


def write_jsonl(path: Path, entries: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return path


def model_usage(model: str, *, input=0, cache_write=0, cache_read=0, output=0) -> dict:
    return {model: {"inputTokens": input, "cacheCreationInputTokens": cache_write,
                    "cacheReadInputTokens": cache_read, "outputTokens": output}}


def test_each_request_is_priced_at_the_tier_its_own_prompt_selects(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [
        assistant("m1", HAIKU, input=1_000, cache_read=99_000, output=1_000),   # 100,000: base
        assistant("m2", HAIKU, input=1_000, cache_read=99_001, output=1_000),   # 100,001: above
    ])
    out = cost.price_session([f], PRICES)
    base = (1_000 * Decimal("0.10") + 99_000 * Decimal("0.01") + 1_000 * Decimal("0.50")) / 1_000_000
    above = (1_000 * Decimal("0.50") + 99_001 * Decimal("0.05") + 1_000 * Decimal("2.50")) / 1_000_000
    assert out["exact"] and out["method"] == "per_request"
    assert Decimal(out["usd"]) == (base + above).quantize(Decimal("0.000001"))
    tiers = out["by_model"][HAIKU]["by_tier"]
    assert tiers["base"]["requests"] == 1 and tiers["above_100000"]["requests"] == 1
    assert out["by_model"][HAIKU]["max_prompt_tokens"] == 100_001


def test_a_cache_write_counts_toward_the_prompt_size(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", HAIKU, input=10, cache_write=100_000)])
    out = cost.price_session([f], PRICES)
    assert list(out["by_model"][HAIKU]["by_tier"]) == ["above_100000"]


def test_a_model_with_no_tier_has_one_price_at_any_prompt_size(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", OPUS, input=200_000, output=1_000)])
    out = cost.price_session([f], PRICES)
    assert Decimal(out["usd"]) == Decimal("0.82")
    assert list(out["by_model"][OPUS]["by_tier"]) == ["base"]


def test_lines_of_one_response_count_once_with_the_largest_usage(tmp_path):
    """Claude Code writes a line per content block; stream JSON can show partial output on early blocks;
    the stdout transcript and the session log hold the same responses."""
    stdout = write_jsonl(tmp_path / "transcript.jsonl", [
        assistant("m1", OPUS, input=100, output=1),
        assistant("m1", OPUS, input=100, output=50),
    ])
    log = write_jsonl(tmp_path / "claude-projects" / "p" / "s.jsonl", [assistant("m1", OPUS, input=100, output=50)])
    out = cost.price_session([stdout, log.parents[1]], PRICES)
    assert out["requests"] == 1
    assert out["by_model"][OPUS]["tokens"]["output"] == 50


def test_a_run_dir_reads_the_subagent_logs_too(tmp_path):
    write_jsonl(tmp_path / "claude-projects" / "p" / "s.jsonl", [assistant("m1", HAIKU, input=10)])
    write_jsonl(tmp_path / "claude-projects" / "p" / "s" / "subagents" / "agent-1.jsonl",
                [assistant("m2", OPUS, input=10, isSidechain=True)])
    out = cost.price_session([tmp_path], PRICES)
    assert set(out["by_model"]) == {HAIKU, OPUS}
    assert out["by_model"][OPUS]["subagent_requests"] == 1


def test_one_hour_cache_writes_are_priced_at_their_own_rate(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", OPUS, cache_write=1_000_000,
                                                     split={"ephemeral_5m_input_tokens": 0,
                                                            "ephemeral_1h_input_tokens": 1_000_000})])
    assert Decimal(cost.price_session([f], PRICES)["usd"]) == Decimal("8.00")


def test_a_split_that_does_not_add_up_is_priced_as_five_minute_writes(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", OPUS, cache_write=1_000_000,
                                                     split={"ephemeral_1h_input_tokens": 5})])
    assert Decimal(cost.price_session([f], PRICES)["usd"]) == Decimal("5.00")


def test_synthetic_messages_with_no_usage_are_not_requests(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", "<synthetic>"), assistant("m2", HAIKU, input=1)])
    assert cost.price_session([f], PRICES)["requests"] == 1


def test_tokens_on_a_model_with_no_price_fail_loudly(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", "claude-unknown-9", input=1)])
    with pytest.raises(cost.PricingError, match="claude-unknown-9"):
        cost.price_session([f], PRICES)


def test_dated_and_context_suffixed_ids_resolve_to_the_list_price():
    assert cost.resolve_model("claude-opus-5-5[1m]", PRICES) == OPUS
    assert cost.resolve_model("claude-haiku-4-5-20251001", PRICES) == "claude-haiku-4-5"


# --- totals only ---------------------------------------------------------------------------------------

def test_totals_alone_give_a_tiered_model_bounds_and_no_number():
    out = cost.price_session([], PRICES, model_usage(HAIKU, input=1_000_000, output=1_000_000))
    assert out["method"] == "totals" and not out["exact"] and out["usd"] is None
    assert (out["usd_lower"], out["usd_upper"]) == ("0.600000", "3.000000")
    assert "bounds" in out["label"]
    assert cost.display(out) == "$0.60–$3.00 (bounds)"


def test_totals_alone_price_a_model_with_no_tier_exactly():
    out = cost.price_session([], PRICES, model_usage(OPUS, input=1_000_000))
    assert out["exact"] and out["usd"] == "4.000000"
    assert cost.display(out) == "$4.00"


# --- requests checked against totals -------------------------------------------------------------------

def test_requests_that_match_the_totals_are_exact(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", HAIKU, input=10, cache_write=20, cache_read=30, output=40)])
    out = cost.price_session([f], PRICES, model_usage(HAIKU, input=10, cache_write=20, cache_read=30, output=40))
    assert out["exact"] and out["checked_against_totals"] and not out["notes"]


def test_tokens_the_records_miss_on_a_tiered_model_turn_the_price_into_bounds(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", HAIKU, input=1_000_000)])
    out = cost.price_session([f], PRICES, model_usage(HAIKU, input=2_000_000))
    assert not out["exact"] and out["usd"] is None
    assert (out["usd_lower"], out["usd_upper"]) == ("0.600000", "1.000000")  # recorded request is above the tier
    assert "miss" in out["label"]


def test_tokens_the_records_miss_on_a_model_with_no_tier_are_priced_exactly_with_a_note(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", OPUS, input=1_000_000)])
    out = cost.price_session([f], PRICES, model_usage(OPUS, input=2_000_000))
    assert out["exact"] and out["usd"] == "8.000000" and "miss" in out["notes"][0]


def test_records_that_exceed_the_totals_give_no_price(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", HAIKU, input=10), assistant("m2", HAIKU, input=10)])
    out = cost.price_session([f], PRICES, model_usage(HAIKU, input=10))
    assert out["usd"] is None and out["usd_lower"] is None and "exceed" in out["label"]
    assert cost.display(out) == "no price (see label)"


def test_totals_split_by_ttl_compare_with_the_records_as_one_cache_write(tmp_path):
    f = write_jsonl(tmp_path / "t.jsonl", [assistant("m1", OPUS, cache_write=30, split={
        "ephemeral_5m_input_tokens": 10, "ephemeral_1h_input_tokens": 20})])
    out = cost.price_session([f], PRICES, model_usage(OPUS, cache_write=30))
    assert out["exact"] and not out["notes"]


# --- prices file -------------------------------------------------------------------------------------------

def test_every_tier_and_one_hour_price_names_a_model_in_pricing_json():
    base = json.loads((ROOT / "pricing.json").read_text())["models"]
    tiers = json.loads((ROOT / "pricing_tiers.json").read_text())["models"]
    assert set(tiers) == set(base)
    for model, p in base.items():
        assert Decimal(tiers[model]["cache_write_1h"]) == 2 * Decimal(p["input"]), model


def test_the_cli_exits_nonzero_on_bounds_and_prints_them(tmp_path):
    result = tmp_path / "result.json"
    result.write_text(json.dumps({"modelUsage": model_usage(HAIKU, input=1_000_000)}))
    run = subprocess.run([sys.executable, "-m", "cbench.cost", str(tmp_path / "none"), "--result", str(result)],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 1
    assert json.loads(run.stdout)["usd_upper"] == "0.500000"
