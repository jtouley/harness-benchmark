# Trap catalog: the open-data pipeline (hidden from arms)

Status: **proposed** (2026-10-14). Each trap is a known cause of a wrong answer. Because the cause is
known in advance, a failed check has a ground-truth explanation, and the [audit protocol](pipeline-family.md#audit-protocol)
can score whether an auditor finds it from the run record.

Every data fact below must be checked against the frozen snapshot or capture when the task is built,
before the task is admitted (as for [L3](L3-open-data-bi-pipeline.md)). A trap that the snapshot does not
contain is removed, not faked.

Columns: **Detected by** names the check in the [shared spec](pipeline-spec.md#the-request-the-text-every-arm-gets).
**Cause class** is the label an auditor must give. Classes: `data-semantics` (the data means something
other than it looks), `spec-reading` (the request says it, the solution did not do it), `stream-semantics`
(delivery, ordering or time), `idempotence`, `numeric`.

## Batch traps (USAspending, Census)

| Id | Trap | What a shallow solution does | Detected by | Cause class |
|---|---|---|---|---|
| B1 | One row per transaction action; the award's total amount repeats on each row | Sums the award total over its rows, so a modified award counts many times | Check 1 | data-semantics |
| B2 | De-obligations are negative actions | Drops negative rows or treats them as errors | Checks 1, 3 | data-semantics |
| B3 | County FIPS is state code + county code with leading zeros | Reads codes as integers; `01001` becomes `1001`; joins fail | Check 2 | data-semantics |
| B4 | Connecticut's counties are planning regions in Census data from 2022 | Drops Connecticut from the join, or counts it twice | Checks 2, 4 | data-semantics |
| B5 | Some transactions have no place-of-performance county | Drops them; state totals no longer reconcile | Check 4 | data-semantics |
| B6 | Fiscal year 2024 runs October 2023 to September 2024 | Filters calendar year 2024 | Checks 1, 2, 3 | spec-reading |
| B7 | Re-running the load | Appends a second copy | Idempotence check | idempotence |
| B8 | Money as floating point | Sums in `double`; totals drift by cents | Checks 1, 4 (exact to the cent) | numeric |

## Spec traps

| Id | Trap | What a shallow solution does | Detected by | Cause class |
|---|---|---|---|---|
| S1 | Amendment A changes "per person" to the July 1, 2024 estimate | Uses the 2020 census count (the first file it finds) | Check 2 | spec-reading |
| S2 | `DECISIONS.md` must record each open choice | Leaves it empty or generic, so an audit has nothing to read | Audit only (no check) | spec-reading |
| S3 | Late events go to `late_events`, not the window | Adds them to the window, or drops them | Checks 6, 7 | spec-reading |

## Stream traps (the capture)

| Id | Trap | What a shallow solution does | Detected by | Cause class |
|---|---|---|---|---|
| W1 | Canary events (`meta.domain == "canary"`), which Wikimedia tells clients to discard | Counts them as edits | Check 5 | data-semantics |
| W2 | `length` and `revision` are present for `edit` and `new` and absent for `log` and `categorize` events | Crashes on a missing field, or counts every event as an edit with zero bytes | Check 5 | data-semantics |
| W3 | `timestamp` is Unix seconds; `meta.dt` is an ISO string in UTC | Mixes them, or reads local time | Check 6 | stream-semantics |
| W4 | `bot` is a boolean on the event; `user` names that end in "bot" are not the rule | Classifies by user name | Check 5 | data-semantics |
| W5 | Net bytes are `length.new - length.old`; `old` is absent for a new page | Uses `length.new` as the delta, or fails on null | Check 5 | data-semantics |

## Stream faults (injected by the replay server, from a seed) {#stream-faults}

| Id | Fault | What a shallow consumer does | Detected by | Cause class |
|---|---|---|---|---|
| F1 | The server closes the connection at a scheduled point | Stops, or restarts from the beginning and counts every event again | Checks 5, 6 | stream-semantics |
| F2 | After a reconnect that sends `Last-Event-ID` as a timestamp, the server re-sends the events with that same timestamp | Counts those events twice | Check 5 | stream-semantics |
| F3 | Events arrive out of event-time order within a few seconds | Assigns windows by arrival | Check 6 | stream-semantics |
| F4 | A batch of events arrives 12 to 20 minutes after their window | Adds them to the closed window | Checks 6, 7 | stream-semantics |
| F5 | One frame is not valid JSON | Crashes, or stops consuming | Check 5 | stream-semantics |
| F6 | The consumer is stopped and started by the grader mid-run (`make stream` twice) | Re-reads from the start; double counts | Check 5 | idempotence |

## Mapping for the audit

For each check, the set of traps that can make it fail:

| Check | Traps |
|---|---|
| 1 | B1, B2, B6, B7, B8 |
| 2 | B3, B4, B6, S1 |
| 3 | B2, B6 |
| 4 | B4, B5, B8 |
| 5 | W1, W2, W4, W5, F1, F2, F5, F6 |
| 6 | W3, F1, F3, F4, S3 |
| 7 | F4, S3 |

Each check failure is diagnosed by the grader itself, before any audit: the answer key stores, for each
check, the wrong answer that each single trap produces (computed from the reference solution with that
one trap re-introduced). A run's wrong answer that matches one of them names the trap. A wrong answer that
matches none is "unexplained", and the audit is scored on the run record alone.
