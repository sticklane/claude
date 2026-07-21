spec review: 0 findings, 0 fixed, 3 discovered

Ref range: b57398146061c2407f3043e10506bb3f835914fa..origin/main (pinned
flip-commit merge-base), restricted to the spec's union `Touch:` across
tasks 01-07 (drain admission.py/reference.md/SKILL.md/mirrors,
token-discipline.md, plugin.json). Product lines: 2120 (admission.py,
touch_disjoint.py, drain_frontier.py across .claude/skills, antigravity/,
codex/ copies) — above the 25-line skip threshold, so a review-fix worker
was dispatched.

Method: critic-agent pass over the product code (admission.py,
touch_disjoint.py, drain_frontier.py, test_admission_concurrency.py — the
three admission/frontier/touch mirror copies confirmed byte-identical)
plus a direct read of the doc/procedure diffs (SKILL.md, reference.md,
token-discipline.md, codex SKILL.md, antigravity drain.md + README.md,
plugin.json). `/code-review` was not invocable in this dispatch context;
the fallback subagent shape was used instead.

Gates: `evals/lint-ultra-gate.sh` OK; all 17 relevant `tests/test_*.sh`
pass; `test_admission.py` (12/12) and `test_admission_concurrency.py`
(scenarios a/b/c) pass. `tests/test_eval_coverage_lint.sh` fails on this
machine — confirmed pre-existing, unrelated to this spec (macOS bash 3.2
vs. `declare -A` in evals/lint-eval-coverage.sh) — not fixed, out of this
spec's Touch.

No high-confidence correctness/behavior findings kept; nothing fixed;
branch `task/drain-multi-spec-swarm-spec-review` carries zero commits.
Three findings routed to Discovered (materialized as draft stubs 08-10 in
this spec's tasks/ dir): SKILL.md overstating what the `admission.py` CLI
writes (does not itself call `git_cas_claim`), mangled markdown in
codex/.agents/skills/drain/SKILL.md's new "Admission command" block, and
`git_cas_claim` raising uncaught on an idempotent no-op re-claim commit.
