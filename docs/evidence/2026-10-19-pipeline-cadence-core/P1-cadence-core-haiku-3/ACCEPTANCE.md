# Acceptance run record (gh-1, Phase 9)

Run from a clean state (`lake/` and `out/` deleted). Commands are from the repository root.

## Signals

| Signal | Command | Result |
|---|---|---|
| Batch build from raw files | `make build` | Pass. 56 of 56 dbt tests. |
| Two builds give equal marts | `make build`, `python -m pipeline.verify hash`, twice | Pass. Hash `b704bea2bb65e9248a838a37b38d61629c8dcebd5c7dfa1fcf42c2897479c8fe` both times. |
| Stream consumes the replay | `make stream DURATION=60` | Pass. 14,571 arrivals in the uninterrupted run R. |
| Killed and restarted run equals uninterrupted run | SIGKILL at 20 seconds, then `make stream DURATION=60`; `python -m pipeline.verify restart` | Pass. m = 14,571. No duplicate `meta_id`. No gap in `arrival_seq`. Equal prefix sets. |
| Replay determinism (Phase 0 gate) | two fresh connections, first 200 ids | Identical, so the restart asserts are hard gates. |
| Seven checks return results | `chk_*` views in `transform/models/checks/` | Pass. See `oracle_map.yml`. |
| Models have grains and key tests | `dbt build` | Pass. 84 of 84. |
| Unit tests | `python -m unittest discover -s pipeline/tests -p "test_*.py"` | Pass. 30 tests. |

## Check results (final stream state, run K)

- Check 1, net obligations by agency: total $1,442,017,216.67, the source total.
- Check 2, top county per person: District of Columbia, $129.07.
- Check 3, awards with a net negative obligation: 1,122.
- Check 4, June 2024: zero county-versus-state difference in all 52 states. The states sum to the source total.
- Check 5, stream edits per wiki and human or bot: 9,210 edits, 7,117,392 net bytes.
- Check 6, top en.wikipedia.org window: 2026-10-15 00:25, 759 on-time edits.
- Check 7, late events: 0.
