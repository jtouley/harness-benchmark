# cd-1 issue log

- P4 plan-update (cycle 1) removed the RUN_BY_COMMAND: plan-create provenance marker from .context/plans/cd-1-pipeline.plan.md.
  P3 gate (/plan-review) denies: no plan with RUN_BY_COMMAND: plan-create. plan_create_gate.py also fails.
  Classification: recoverable. Action: re-run /plan-update --from-review so the marker is restored, then re-run P3.
- Re-run P4 is blocked by the handoff hook: no plan with RUN_BY_COMMAND: plan-create. The orchestrator cannot write the plan.
  Decision: before P9, re-run P1 /plan-create cd-1 to write a fresh plan with its marker. Then P3 and P4 again (review cycles counted from cycle 2 onward).
- P4 plan-update (cycle 2) dropped RUN_BY_COMMAND: plan-create again. plan_create_gate.py fails; every peer handoff is blocked.
  Repeated twice, so this is systematic for the P4 peer, not a one-off. Recovery by re-running P1 would be undone by the next P4.
  Decision: stop the run at P4 and report. Not a destructive, credential or security stop; logged as a retries-class blocker.
