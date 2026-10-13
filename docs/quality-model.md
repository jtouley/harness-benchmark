# Quality model: what "great code" means in this benchmark

Status: **proposed** for criteria v2 (October 2026). Criteria v1 used one blind grader with four
1–10 dimensions (design, correctness, readability, tests). That rubric is a judgment. It is not a
published standard, and nobody can recompute it. This model replaces it with measures that come
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
| Maintainability | Testability | **New-code coverage**, line and branch, on the lines the change adds: ≥ 80% | SonarQube "Sonar way" quality gate, the most widely used default gate for new code |
| Maintainability | Testability | **Mutation score** on the changed lines: ≥ 80% after removing equivalent mutants | Mutation testing ([criteria M4](criteria.md#4-measures)); coverage shows that code ran, a mutant shows that a test checks it |
| Maintainability | Analysability, modifiability | **Cognitive complexity** per function: no new function above 15 | SonarSource, *Cognitive Complexity* (G. Ann Campbell, 2017); 15 is the Sonar default |
| Maintainability | Analysability, testability | **Cyclomatic complexity** per function: no new function above 10 | McCabe, *A Complexity Measure* (IEEE TSE, 1976); 10 is McCabe's own limit |
| Maintainability | Analysability | **Maintainability index**, reported, not gated | Coleman et al. (1994), as computed by radon (the Visual Studio variant, 0–100) |
| Reliability | Faultlessness | **No new bug-class static findings**: pyflakes, syntax errors, flake8-bugbear, pylint errors | The "no new bugs" condition of the Sonar way gate, measured with ruff |
| Maintainability | Analysability | **Code smells per 100 new lines** (the other ruff rules: pycodestyle without line length, pylint conventions and refactors, simplify, pyupgrade, mccabe), reported | The Sonar maintainability rating idea (smells relative to code size) |
| Maintainability | Modifiability | **No new type errors** (mypy, default settings) | Static type checking, the Python community standard checker |
| Maintainability | Modularity, reusability | **Design fit**, judged against a checklist (below) | Reviewer judgment; no tool measures it |

Line length (pycodestyle E501) is formatting, not quality, and the Sonar way gate does not use it, so
it is left out. Duplication is not measured yet (no Python duplication tool in the pinned set); it is a
known gap.

## Stronger measures for the next run set

These measure "good design" and "good tests" by outcome, not by inspection:

| Measure | How | What it shows |
|---|---|---|
| **Follow-up task success** | After each trial, one fixed agent (the same model and prompt for every arm) gets a second task built on that trial's code, scored by its own hidden tests. Each golden task gains a `followup/` folder | Maintainability (ISO/IEC 25010 modifiability), measured directly: does the next change go well |
| **Hidden-suite pass fraction** | 30 or more hidden tests per task, including edge cases the spec implies and property-based tests; report the fraction passed, not only pass or fail | Functional correctness with more resolution than M1 |
| **Escaped defects, test-confirmed** | A blind reviewer files a defect only with a reproduction test that fails on the trial's code and passes on the reference solution; count confirmed defects per trial | Faultlessness, with no human severity call needed for "confirmed" |
| **Test strength** | Run each arm's own tests against mutants of the reference solution; report the kill rate | Testability: tests that catch real faults, on one fixed set of mutants for every arm |
| **Pairwise judging, as a tie-breaker only** | Two or three LLM judges compare solutions A against B, each pair twice with positions swapped; report a win rate | Design preference, where the measures above tie |

## How the parts combine

A solution is **great code** for this benchmark when all three layers hold:

1. **It does what the spec says.** Every hidden test passes (M1), and the blind reviewers reproduced no
   critical or major defect (M2).
2. **It passes the tool gate.** New-code coverage ≥ 80%, no new function over cognitive complexity 15
   or cyclomatic complexity 10, no new bug-class finding, no new type error. Test strength (the kill
   rate on the reference solution's mutants) ≥ 80% joins the gate when it is built. The tool gate is
   reported for every arm; it does not rank arms. Arms are ranked by the outcome measures above (escaped
   defects, follow-up success, hidden-suite pass fraction).
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

Computed by [`scripts/quality_metrics.py`](../scripts/quality_metrics.py) on the delivered trees
against the untouched baseline. Raw data: [`quality_metrics.json`](experiments/2026-10-12-iteration-4/quality_metrics.json).
Mutation score is not included: mutmut 3 does not run on this code (it imports modules by bare name).

| Arm | Tool gate passed | New-code coverage | Branch coverage | Highest cognitive complexity | New bug findings | New type errors |
|---|---|---|---|---|---|---|
| Opus one-shot | **3 of 3** | 96.3–97.5% | 82.0–88.5% | 12–15 | 0 | 0 |
| Cadence | 1 of 3 | 100% | **90.7–93.3%** | 12–19 | 0 | 0–1 |
| ship-feature (2 delivered) | 0 of 2 | 100% | 90.3–93.8% | 13–18 | 0 | 0–3 |
| Sonnet one-shot | 1 of 3 | 97.0–100% | 82.6–87.0% | 12–21 | 0 | 0 |
| Haiku 4.5 one-shot | 1 of 3 | 95.2–100% | 82.4–86.1% | 12–32 | 0–2 | 0–1 |

What the tools add to the picture:

- **New-code coverage does not separate the arms.** Every solution covers 95–100% of its new lines.
  Criteria v1 already found this. Branch coverage separates more: the harnesses reach 90–94%, the
  one-shots 82–88%.
- **The harness solutions fail the gate on complexity and types, not on tests.** Cadence's audit-undo
  has one function at cognitive complexity 19 (cyclomatic 13), and its budgets solution adds one type
  error. That matches the graders' "heavier than needed".
- **Opus alone is the only arm that passes the tool gate on every task.** Together with its blind
  quality score, that is consistent: on small, precise tasks, Opus alone writes simple, well-typed code.
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
