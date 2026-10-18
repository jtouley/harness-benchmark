"""Lines flagged per ast-grep rule family at checkpoint 6, before scb-check's own thresholds.

usage: python count_rule_lines.py ast-grep-rules-checkpoint_6.txt.gz
The input is `sg scan --rule <family>.yaml --json=compact` run on the reference solution's
cfgpipe.py for each of scb-check 0.1.3's rule files, each preceded by a `#FILE <family>.yaml` line.
"""

import collections
import gzip
import json
import sys

family, lines, per_rule = None, collections.defaultdict(set), collections.defaultdict(set)
for line in gzip.open(sys.argv[1], "rt"):
    line = line.strip()
    if line.startswith("#FILE"):
        family = line.split()[1].removesuffix(".yaml")
    elif line:
        for match in json.loads(line):
            span = range(match["range"]["start"]["line"], match["range"]["end"]["line"] + 1)
            lines[family].update(span)
            per_rule[match["ruleId"]].update(span)
print(json.dumps({"all": len(set().union(*lines.values())),
                  "by_family": {f: len(v) for f, v in sorted(lines.items(), key=lambda kv: -len(kv[1]))},
                  "top_rules": {r: len(v) for r, v in sorted(per_rule.items(), key=lambda kv: -len(kv[1]))[:5]}},
                 indent=1))
