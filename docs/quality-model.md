# Quality model: what "great code" means in this benchmark

Status: **proposed** for criteria v2 (October 2026). Criteria v1 used one blind grader with four
1–10 dimensions (design, correctness, readability, tests: measure M7). That rubric is a judgment. It is not a
published standard, and nobody can recompute it. This model replaces it as a measure of quality with measures that come
from published, widely used standards and tools. Each one has a fixed threshold, and a script
recomputes it ([`scripts/quality_metrics.py`](../scripts/quality_metrics.py)). A grader still judges
the two things no tool can measure, against a fixed checklist.

## The standard behind it

[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) (Systems and software Quality
Requirements and Evaluation, SQuaRE) is the international model of software product quality. The
characteristics that a code change can affect, and how this benchmark measures each one:

| ISO/IEC 25010 characteristic | Sub-characteristic | Measure here | Source of the method and threshold |
|---|---|---|---|
| Functional suitability | Functional completeness and correctness | **Acceptance (M1):** hidden tests of the task pass | The task's oracle ([criteria §4](criteria.md#4-measures)) |
| Functional suitability, reliability | Functional correctness, faultlessness | **Reproduced defects (M2):** each with a command and its output, by severity | [criteria §5](criteria.md#5-blind-review-protocol); severity rule in [`defects.json`](experiments/2026-10-12-iteration-4/defects.json) |
| Maintainability | Testability | **New-code coverage**: line coverage of the executable lines the change adds, ≥ 80%. Line and branch coverage of the whole package are reported | SonarQube "Sonar way" quality gate, the most widely used default gate for new code |
| Maintainability | Testability | **Mutation score** on the changed lines: ≥ 80% after removing equivalent mutants | Mutation testing ([criteria M4](criteria.md#4-measures)); coverage shows that code ran, a mutant shows that a test checks it |
| Maintainability | Analysability, modifiability | **Cognitive complexity** per function: no function that the change takes above 15 (new and above it, or above it now and not before) | SonarSource, *Cognitive Complexity* (G. Ann Campbell, 2017); 15 is the Sonar default |
| Maintainability | Analysability, testability | **Cyclomatic complexity** per function: no function that the change takes above 10, by the same rule | McCabe, *A Complexity Measure* (IEEE TSE, 1976); 10 is McCabe's own limit |
| Maintainability | Analysability | **Maintainability index**, reported, not gated | Coleman et al. (1994), as computed by radon (the Visual Studio variant, 0–100) |
| Reliability | Faultlessness | **No new bug-class static findings**: undefined or redefined names and broken statements (pyflakes F82, F811, F63, F7), syntax errors, flake8-bugbear, pylint errors | The "no new bugs" condition of the Sonar way gate, measured with ruff |
| Maintainability | Analysability | **Code smells per 100 new lines** (the other ruff rules, including the other pyflakes rules such as unused imports: pycodestyle without line length, pylint conventions and refactors, simplify, pyupgrade, mccabe), reported | The Sonar maintainability rating idea (smells relative to code size) |
| Maintainability | Modifiability | **No new type errors** (mypy with `--check-untyped-defs`, so unannotated code is checked too) | Static type checking, the Python community standard checker |
| Maintainability | Modularity, reusability | **Design fit**, judged against a checklist (below) | Reviewer judgment; no tool measures it |

Line length (pycodestyle E501) is formatting, not quality, and the Sonar way gate does not use it, so
it is left out. Duplication was not measured in iteration 4; the owner criteria below add it (`jscpd`).

## Stronger measures for the next run set

These measure "good design" and "good tests" by outcome, not by inspection:

| Measure | How | What it shows |
|---|---|---|
| **Follow-up task success** | After each trial, one fixed agent (the same model and prompt for every arm) gets a second task built on that trial's code, scored by its own hidden tests. Each golden task gains a `followup/` folder | Maintainability (ISO/IEC 25010 modifiability), measured directly: does the next change go well |
| **Hidden-suite pass fraction** | 30 or more hidden tests per task, including edge cases the spec implies and property-based tests; report the fraction passed, not only pass or fail | Functional correctness with more resolution than M1 |
| **Escaped defects, test-confirmed** | The form M2 takes from the next run set on: a blind reviewer files a defect only with a reproduction test that fails on the trial's code and passes on the reference solution; count confirmed defects per trial, by severity | Faultlessness, with no human call needed for "confirmed" |
| **Test strength** | Run each arm's own tests against mutants of the reference solution; report the kill rate | Testability: tests that catch real faults, on one fixed set of mutants for every arm |
| **Pairwise judging, as a tie-breaker only** | Two or three LLM judges compare solutions A against B, each pair twice with positions swapped; report a win rate | Design preference, where the measures above tie |

## Owner criteria (2026-10-14): DRY, SOLID, extensible, traceable, cheap

The owner's success question for the long tasks: **which arm comes closest to a DRY, SOLID and
extensible system, whose path we can understand, and at what cost.** Each part has a measure:

| Part | Measure | How |
|---|---|---|
| DRY | **Duplicated lines on new code ≤ 3%** | `jscpd` (one tool for Python, SQL, Scala and YAML), minimum block 5 lines; the threshold is the Sonar way gate's duplication condition |
| SOLID: single responsibility, dependency inversion | **Module coupling**: per module, efferent and afferent coupling and instability (Martin, *Agile Software Development*, 2002), from the import graph; plus the design checklist items below | An import-graph script per language; reported, not gated |
| SOLID: open for extension | **Edit radius of the follow-up task**: the existing files (not new ones) the follow-up change has to modify, and their changed lines | From the follow-up diff. A small radius means the system was open for that extension |
| Extensible | **Follow-up task success and cost**: the follow-up's hidden checks, and its dollars and wall time | Each long task has a follow-up (for the pipeline family: a new data mart and a dashboard). The same arm builds it on its own delivered code |
| Traceable ("how we got there") | **Audit scores**: diagnosis accuracy, origin accuracy, audit cost, repair cost | The [audit protocol](tasks/pipeline-family.md#audit-protocol) |
| Cheap | **Dollars for build + follow-up + repairs**, at list prices from token counts | `pricing.json`; Claude Code's own figure is not used for models it does not price |

[`scripts/quality_metrics.py`](../scripts/quality_metrics.py) measures the first three rows. Duplication:
jscpd 5.4.1 over Python, SQL, Scala and YAML in the package, minimum block 5 lines (and jscpd's default
of 50 tokens), run as `uvx --from nodejs-wheel==24.19.0 npx --yes jscpd@5.4.1`, so Node is pinned from
PyPI and the host's Node is not used. jscpd gets an empty config file of its own and `--no-gitignore`,
so a `.jscpd.json`, a `package.json` "jscpd" key or a `.gitignore` that the measured solution ships cannot
change what is scanned. Both sides of each clone count, and the measure is the share of
added lines inside a clone (`new_code_duplication`, gate `new_code_duplication_at_most_3`). Coupling:
`module_coupling`, from the Python import graph (imports inside the package only; SQL, Scala and YAML
readers are not written yet and plug into `IMPORT_GRAPHS`). Edit radius: `--follow-up REPO BASE HEAD`
adds `edit_radius` (existing files modified or deleted and their added and removed lines, apart from new
files; a rename counts as a deletion plus a new file). It is reported twice: `edit_radius.package` counts
only files under `--package`, and `edit_radius.repo` counts every file, tests and docs included. The
owner criterion ("the existing files the follow-up change has to modify") reads `package`, so that plan,
ledger or docs files an arm writes do not enlarge its radius; `repo` is kept beside it for context.

Design checklist additions, each yes or no with a file and line, by two blind reviewers:

- Each module has one reason to change (sources, transforms, sinks, orchestration and configuration are
  separate).
- Sources and sinks sit behind one interface each; adding one does not edit the others.
- Configuration, not code, holds what differs between pipelines where the spec asks for it (P2).
- No logic is copied between the batch and the stream paths where one shared function fits.

**Ranking.** Arms that pass the checks (layer 1) are ranked on design (duplication, checklist, edit
radius), then on traceability. Cost is reported beside each, and the answer to "which is cheapest" is the
cheapest arm in the top design tier, not the cheapest overall.

## How the parts combine

A solution is **great code** for this benchmark when all three layers hold:

1. **It does what the spec says.** Every hidden test passes (M1), and the blind reviewers reproduced no
   critical or major defect (M2).
2. **It passes the tool gate.** New-code coverage ≥ 80%, no function that the change takes over
   cognitive complexity 15 or cyclomatic complexity 10, no new bug-class finding, no new type error,
   duplicated lines on new code ≤ 3%.
   Test strength (the kill rate on the reference solution's mutants) ≥ 80% joins the gate when it is
   built. The tool gate is reported for every arm; it does not rank arms. The decision rule
   ([next steps](next-steps.md#decision-rule-for-this-question)) decides on M2 defects, test-confirmed,
   critical or major. Follow-up success and the hidden-suite pass fraction are reported beside it.
3. **It fits the design.** Two reviewers check the design checklist. Each item is yes or no, with a
   file and line as evidence:
   - The change follows the existing module boundaries (no new logic in the CLI layer that belongs in
     the model or the storage layer).
   - It adds nothing the spec did not ask for, or each addition is recorded as a decision.
   - Names say what the code does; no dead code; no duplicated logic.
   - Tests check behavior through the public interface and cover the failure paths the spec names.

No layer replaces another. Iteration 4 shows why: Haiku 4.5's multi-currency solution passes the tool
gate, but its monthly report never converts currencies (a spec failure, layer 1). And on budgets, every
one-shot passes the hidden tests but ships crashes that only a reviewer reproduced (layer 1, M2).

## Iteration 4, measured this way

Computed by [`scripts/quality_metrics.py`](../scripts/quality_metrics.py) (tool versions pinned) on the
delivered trees against the untouched baseline (`quality_metrics.py SOLUTION BASELINE`, with each
solution's `CHANGE.diff`). A lint or type finding counts only on a line the change added, and a function
counts as too complex only when the change takes it over the threshold, so fixing an old problem cannot
hide a new one. The reference rows apply each task's `reference.patch` to the same baseline. A tool that
fails leaves its measure unmeasured, and the gate then fails. Raw data: [`quality_metrics.json`](experiments/2026-10-12-iteration-4/quality_metrics.json).
Mutation score is not included: mutmut 3 does not run on this code (it imports modules by bare name).

| Arm | Tool gate passed | New-code coverage | Branch coverage | Highest cognitive complexity | New bug findings | New type errors |
|---|---|---|---|---|---|---|
| Opus one-shot | **3 of 3** | 96.3–97.5% | 82.0–88.5% | 12–15 | 0 | 0 |
| Cadence | 1 of 3 | 100% | **90.7–93.3%** | 12–19 | 0 | 0–1 |
| ship-feature (2 delivered) | 0 of 2 | 100% | 90.3–93.8% | 13–18 | 0 | 0–3 |
| Sonnet one-shot | 1 of 3 | 97.0–100% | 82.6–87.0% | 12–21 | 0 | 0 |
| Haiku 4.5 one-shot | 1 of 3 | 95.2–100% | 82.4–86.1% | 12–32 | 0 | 0–1 |
| *Reference solution (task author)* | *1 of 3* | *100%* | *89.3–91.9%* | *11–15* | *0* | *0–1* |

What the tools add to the picture:

- **New-code coverage does not separate the arms.** Every solution covers 95–100% of its new lines.
  Criteria v1 already found this. Branch coverage separates more: the harnesses reach 90–94%, the
  one-shots 82–89%.
- **The harness solutions fail the gate on complexity and types, not on tests.** Cadence's audit-undo
  has one function at cognitive complexity 19 (cyclomatic 13), and its budgets solution adds one type
  error. That matches the graders' "heavier than needed".
- **The gate is not calibrated on these tasks.** The reference solutions fail it on budgets and
  audit-undo: each adds a subcommand, which takes the CLI dispatcher `cli.run` (cyclomatic 7 in the
  baseline) to 11 or 12, and audit-undo's adds one type error. Every failing solution fails on that
  same function or on type errors. So the complexity condition here mostly records whether a solution
  moved the dispatch out of `cli.run`. Opus alone is the only arm that passes on every task, but that is
  not yet evidence of simpler code. Criteria v2 should adopt the gate only on tasks whose reference
  passes it, or record why not.
- **The tools miss what the reviewers found.** The Opus budgets solution passes the gate and still ships
  two crashes. Layer 1 needs the reviewers.

## Adopting it

This model is proposed, not in force. It becomes part of the criteria only as criteria v2, written
before the next run set, with a changelog entry, as [criteria v1](criteria.md) requires. The work:

1. Pin the tools (ruff, radon, complexipy, mypy, coverage.py, and a mutation tool that runs on this
   code, such as cosmic-ray or a diff-scoped runner) in the lockfile, so the numbers reproduce.
2. Two reviewers per task for M2 and the design checklist (criteria §5), blind, with the repro script.
3. Decide how the layers report: one table per arm with the three layers side by side, and no single
   blended score, so a reader sees where a solution falls short.
