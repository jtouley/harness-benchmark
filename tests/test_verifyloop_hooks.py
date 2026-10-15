"""The verifyloop arm's enforcement hooks: run_contract.sh (runs CONTRACT.md) and stop_gate.sh (the Stop hook).

These hooks are the mechanism of a measured arm. If they fail open, the arm is a one-shot with extra tokens;
if they fail forever, the trial is a timeout. Both would be scored as the model's result.
"""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "harnesses/verifyloop"
RUNNER = PLUGIN / "hooks/run_contract.sh"
GATE = PLUGIN / "hooks/stop_gate.sh"
CAP = 10


def run_contract(tmp_path, text, timeout=60):
    f = tmp_path / "CONTRACT.md"
    f.write_text(text)
    return subprocess.run(["bash", str(RUNNER), str(f)], capture_output=True, text=True, timeout=timeout)


def gate(project, stdin="{}"):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "CLAUDE_PLUGIN_ROOT": str(PLUGIN)}
    r = subprocess.run(["bash", str(GATE)], input=stdin, capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


# run_contract.sh

def test_contract_with_failing_and_passing_checks_reports_each_and_fails(tmp_path):
    r = run_contract(tmp_path, "Req 1 fails\n```check\nfalse\n```\nReq 2 passes\n```check\ntrue\n```\n")
    assert r.returncode == 1
    assert "FAIL Req 1 fails" in r.stdout
    assert "PASS Req 2 passes" in r.stdout


def test_contract_with_only_passing_checks_passes(tmp_path):
    r = run_contract(tmp_path, "Req 1\n```check\ntrue\n```\n")
    assert r.returncode == 0, r.stdout
    assert "PASS Req 1" in r.stdout


@pytest.mark.parametrize("fence", ["bash", "sh", ""])
def test_contract_with_no_check_blocks_fails(tmp_path, fence):
    r = run_contract(tmp_path, f"# Contract\n\nReq 1: the endpoint returns 200\n```{fence}\ntrue\n```\n")
    assert r.returncode != 0, "a contract with zero check blocks must not pass the gate"
    assert "NO CHECKS" in r.stdout


def test_contract_reports_its_check_count(tmp_path):
    r = run_contract(tmp_path, "a\n```check\ntrue\n```\nb\n```check\ntrue\n```\n")
    assert "CHECKS 2" in r.stdout


def test_setup_that_backgrounds_a_process_does_not_block_the_runner(tmp_path):
    start = time.time()
    r = run_contract(tmp_path, "Start server\n```setup\nsleep 8 &\n```\nok\n```check\ntrue\n```\n")
    assert r.returncode == 0, r.stdout
    assert time.time() - start < 4, "setup must return when its foreground command exits"


def test_failing_setup_fails_without_a_traceback(tmp_path):
    r = run_contract(tmp_path, "s\n```setup\necho boom; exit 3\n```\nok\n```check\ntrue\n```\n")
    assert r.returncode == 1
    assert "SETUP FAILED" in r.stdout and "boom" in r.stdout
    assert "Traceback" not in r.stdout + r.stderr


def test_check_with_an_empty_label_line_is_still_run(tmp_path):
    r = run_contract(tmp_path, "\n```check\nfalse\n```\n")
    assert r.returncode == 1
    assert "FAIL (unlabelled check)" in r.stdout


def test_missing_contract_file_fails(tmp_path):
    r = subprocess.run(["bash", str(RUNNER), str(tmp_path / "CONTRACT.md")], capture_output=True, text=True)
    assert r.returncode == 1


# stop_gate.sh

def test_gate_allows_stop_when_all_checks_pass(tmp_path):
    (tmp_path / "CONTRACT.md").write_text("ok\n```check\ntrue\n```\n")
    assert gate(tmp_path) is None
    assert "rc=0" in (tmp_path / ".contract_gate.log").read_text()


def test_gate_blocks_on_a_failing_check_and_names_it(tmp_path):
    (tmp_path / "CONTRACT.md").write_text("Req 1 fails\n```check\nfalse\n```\n")
    out = gate(tmp_path)
    assert out["decision"] == "block"
    assert "FAIL Req 1 fails" in out["reason"]


def test_gate_blocks_on_a_contract_without_checks(tmp_path):
    (tmp_path / "CONTRACT.md").write_text("Req 1\n```bash\ntrue\n```\n")
    out = gate(tmp_path)
    assert out["decision"] == "block"
    assert "NO CHECKS" in out["reason"]


@pytest.mark.parametrize("contract", [None, "Req 1 fails\n```check\nfalse\n```\n"], ids=["missing", "failing"])
def test_gate_stops_blocking_after_the_cap_for_every_block_reason(tmp_path, contract):
    if contract is not None:
        (tmp_path / "CONTRACT.md").write_text(contract)
    outs = [gate(tmp_path) for _ in range(CAP + 2)]
    assert all(o and o["decision"] == "block" for o in outs[:CAP])
    assert outs[CAP] is None and outs[CAP + 1] is None


def test_gate_logs_a_missing_contract_as_its_own_outcome(tmp_path):
    gate(tmp_path)
    log = (tmp_path / ".contract_gate.log").read_text()
    assert "no CONTRACT.md" in log


def test_gate_logs_when_the_cap_lets_the_session_end(tmp_path):
    (tmp_path / ".contract_attempts").write_text(str(CAP))
    assert gate(tmp_path) is None
    assert "cap reached" in (tmp_path / ".contract_gate.log").read_text()


# repository hygiene for calibration outputs

@pytest.mark.parametrize("path", [
    "calibration/swebench-pro/tasks/x",
    "calibration/swebench-pro/sample20/x",
    "calibration/swebench-pro/hard3/x",
    "calibration/swebench-pro/runs/x",
    "calibration/swebench-pro/jobs/x",
    "private/x",
])
def test_machine_local_outputs_are_ignored(path):
    r = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    assert r.returncode == 0, f"{path} must be ignored"
