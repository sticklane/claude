# Verification: task 06-skill-invokes-admission

Verdict: PASS

Branch: task/06-skill-invokes-admission, HEAD 8db1359. Base for task-file
diff: 3435855. Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a3244b9248b0ec524

## Criterion 1 — grep count ≥ 2

Command:

```
grep -c "admission.py" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md
```

Output:

```
.claude/skills/drain/SKILL.md:2
.claude/skills/drain/reference.md:3
```

Combined = 5 ≥ 2. PASS. (L0 — text-presence only; this criterion is
explicitly an L0 grep by the task's own framing, superseded by criterion 3
for the behavioral claim.)

## Criterion 2 — SKILL.md ≤ 500 lines

Command: `wc -l < .claude/skills/drain/SKILL.md`
Output: `499`
499 ≤ 500. PASS (L1 — structural bound, exactly what the criterion asks).

## Criterion 3 — judgment: admission.py scoped correctly, rolling-window stays prose

Read SKILL.md lines 66–111 ("## 1. Inventory", "Claim the owner lease"
block) and reference.md's "Cross-spec admission & merge (R1–R12)" section
(lines 1706–1784+).

SKILL.md, "Claim the owner lease" block (lines 92-101):

> "`python3 .claude/skills/drain/admission.py --frontier <drain_frontier.py
JSON>` executes the DRAIN-OWNER.md git-CAS lease claim ... AND the two
> cross-spec checks it owns: R1 spec-lease claim eligibility (up-to-3
> Touch-disjoint specs) and R2 the two-level `W ≤ 5` per-spec / `≤ 10`
> global cap. ... Same-spec `Group:`/Touch rolling-window logic stays
> prose-driven (step 2)."

This explicitly scopes admission.py to R1 (spec-lease claim eligibility)
and R2 (two-level cap) ONLY, and explicitly excludes same-spec
`Group:`/Touch rolling-window logic, naming it prose-driven. Satisfies the
criterion's "specifically... not the same-spec Group/Touch logic" test.

reference.md, "Cross-spec admission & merge (R1–R12)" section — invocation
contract (lines 1735-1753):

> "`python3 .claude/skills/drain/admission.py --frontier <path>` ...
> CONSUMES the drain_frontier.py JSON above and never re-derives it (R14).
> `--frontier` takes a drain_frontier.py report path, or `-` to read it
> from stdin; optional `--spec-cap N` (default 3, the R1 lease cap),
> `--window N` (default 5, the per-spec `W`, hard-capped at 5), and
> `--global-cap N` (default 10, the R2 shared pool) override the caps. On
> success it exits 0 and writes a JSON object to stdout with two keys:
> `claimed_specs` ... and `admitted_tasks` .... A malformed or unreadable
> frontier exits **2** ...; drain treats ANY non-zero exit as a **claim
> failure** — falling back to this section's by-hand rules ..., never
> working around it as a crash. The module owns ONLY R1 spec-claim
> eligibility and the R2 two-level cap; the same-spec `Group:`
> co-admissibility and per-task Touch-disjointness within one claimed spec
> (below) stay prose-driven and are computed from drain_frontier.py's
> `admissible` field, not by admission.py."

This documents arguments (`--frontier`, `--spec-cap`, `--window`,
`--global-cap`), JSON output shape (`claimed_specs`, `admitted_tasks`),
and non-zero-exit-as-claim-failure handling, and reiterates the R1/R2-only
scope. PASS. Evidence ladder: L2 (behavior/contract documented and
internally consistent with SKILL.md's step-1 prose) — no live invocation
of admission.py against a real frontier report was run as part of this
criterion (that would be L3); the task's own framing calls this a
judgment/reading criterion, not an execution one, so L2 is adequate here.

## Criterion 4 — project gates exit 0

```
bash specs/status.sh            -> exit 0
claude plugin validate .        -> exit 0
./bin/check-agent-model-pins    -> exit 0
bash evals/lint-ultra-gate.sh   -> exit 0
bash evals/lint-skill-size-gate.sh -> exit 0
for f in tests/test_*.sh; do bash "$f"; done
  test_antigravity_content_parity.sh  -> 0
  test_antigravity_parity.sh          -> 0
  test_check_token_discipline.sh     -> 0
  test_codex_parity.sh               -> 0
  test_deep_research_synthesis_guard.sh -> 0
  test_doc_links.sh                  -> 0
  test_drain_owner_protocol.sh       -> 0
  test_drain_scheduler_window.sh     -> 0
  test_hook_templates.sh             -> 0
  test_install_docs.sh               -> 0
  test_install_gates.sh              -> 0
  test_mirror_procedure_coverage.sh  -> 0
  test_plugin_version_helper.sh      -> 0
  test_review_skip.sh                -> 0
  test_screen_stub.sh                -> 0
  test_sync_workflows.sh             -> 0
```

All exit 0. PASS.

## Touch-scope and append-only checks

`git diff --name-only 3435855 HEAD`:

```
.claude/skills/drain/SKILL.md
.claude/skills/drain/reference.md
```

Exactly the Touch-scoped two files, nothing else changed. PASS.

`git diff 3435855 HEAD -- '*/tasks/*.md'` produced NO output — the task
file itself (specs/drain-multi-spec-swarm/tasks/06-skill-invokes-admission.md)
was not modified at all between base and HEAD. This trivially satisfies the
"append-only" constraint (nothing beyond the allowed set changed, because
nothing changed), but it also means:

- Status line still reads `in-progress`, not `done`.
- No acceptance checkboxes are ticked.
- No evidence-citation lines were added to the task file.

This is a process gap (the task file was never updated to record
completion/evidence) but is NOT a scope violation — no disallowed edit was
made to the task file, and it is not itself one of the four acceptance
criteria under verification. Flagging it as a finding for the caller to
address (e.g. tick boxes / flip Status / add evidence pointer in a
mechanical follow-up), separate from the PASS/FAIL of criteria 1-4.

## Scope-creep check

No files outside `.claude/skills/drain/SKILL.md` and
`.claude/skills/drain/reference.md` were modified (confirmed above). No
other specs'/tasks' files were touched. No version bumps, plugin.json
edits, or formatting sweeps outside Touch scope.

## Overfitting check

The changes are prose-only edits to two markdown skill files describing a
CLI contract; there is no test-input special-casing risk here (no
executable logic was added in this diff — admission.py itself was task
04's scope and is unmodified, confirmed via `git diff --name-only` showing
only the two Touch-scoped files).

## Criteria-adequacy summary

1. grep count ≥ 2 — L0 text-presence. Adequate only as a coarse
   sanity check; the task itself flags this and criterion 3 supplies the
   L2 behavioral evidence needed to actually entail the requirement.
2. line count ≤ 500 — L1 structural bound; directly entails the numeric
   requirement.
3. correct scoping of admission.py vs prose-driven same-spec logic — L2
   behavior/contract-documentation evidence (quoted prose read and judged);
   entails the requirement as framed (a reading/judgment criterion, not an
   execution one).
4. gates exit 0 — L2 behavior (all gate scripts actually executed);
   entails the requirement.

Overall: PASS. All four acceptance criteria hold under direct exercise;
Touch scope respected; task file unmodified (append-only trivially true,
but flagged as an incomplete-bookkeeping finding, not a criterion failure).
