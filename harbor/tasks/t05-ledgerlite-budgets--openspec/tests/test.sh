#!/bin/bash
# Hidden tests: uploaded by Harbor after the agent finishes, never visible to it.
# reward = 1.0 only when every hidden test passes; pass counts are kept for the report.
set -u
mkdir -p /logs/verifier
cd /app
rm -rf _hidden_tests && cp -r /tests/hidden _hidden_tests
python3 -m pytest -q -p no:cacheprovider -p no:randomly --junitxml=/tmp/junit.xml \
    --rootdir /app _hidden_tests > /logs/verifier/pytest.txt 2>&1
python3 - <<'PY'
import json, xml.etree.ElementTree as ET
passed = total = 0
try:
    for case in ET.parse("/tmp/junit.xml").getroot().iter("testcase"):
        total += 1
        if not any(c.tag in ("failure", "error", "skipped") for c in case):
            passed += 1
except Exception:
    pass
json.dump({"reward": 1.0 if total and passed == total else 0.0, "tests_passed": passed, "tests_total": total},
          open("/logs/verifier/reward.json", "w"))
print(f"hidden tests: {passed}/{total}")
PY
