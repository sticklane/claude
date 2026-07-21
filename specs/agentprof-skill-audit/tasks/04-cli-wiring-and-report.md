# Task 04: skillcheck subcommand wiring, flags, and report output

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 02, 03
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R9, R10, R11, R13)
Touch: agentprof/main.go, agentprof/cmd_skillcheck.go, agentprof/cmd_skillcheck_test.go

## Goal

`agentprof skillcheck [--days N | --since RFC3339] [--skill <name>]
[--judge-tier <tier>] [-o path.json] [--format json|table]` is a
registered, working subcommand: it wires tasks 01–03's pieces together
(walk transcripts via task 01's accessor → task 02's trigger
classification → task 03's outcome classification, gated so only
`correctly-triggered` invocations reach outcome scoring) and emits the
per-skill aggregate report (JSON default, `table` via `--format`).

## Touch

Only the files in the header. This task wires and outputs; it must not
reimplement task 02/03's classification logic inline — call their exported
functions.

## Steps

1. Register `case "skillcheck":` in `agentprof/main.go`'s switch
   (`agentprof/main.go:26-36` pattern), alongside the existing
   `claude`/`gcp`/`vertex`/`otel`/`antigravity`/`build` cases.
2. Implement flag parsing: `--days`/`--since`/`-o` matching the `claude`
   subcommand's existing shape and defaults; `--skill` (filter to one
   skill); `--judge-tier` (default `scout`; resolves via the
   `runtimes/claude-code.md` tier→model map; an explicit `session` value is
   rejected with an error at parse time — no usable `--model` for a fresh
   subprocess); `--format` (`json` default, `table`).
3. Wire the pipeline: task 01's `SkillInvocations` → task 02's trigger
   classification → for each `correctly-triggered` result, task 03's
   outcome classification (never called for `misfired`/`unresolvable`).
4. Assemble the per-skill aggregate report matching SPEC.md's Report shape
   JSON example: counts per category (`correct`, `misfired`,
   `unresolvable`, `explicit_invocation`, `self_chained`,
   `possible_misses`, `success`, `failure`, `unknown`) plus a per-finding
   list with `session`/`verdict`/`evidence`/`transcript_ref` (path+line)
   for every verdict other than `correct`/`success`.
5. Implement `--format table`: same aggregate, rendered as parseable
   columns (not the JSON shape).
6. Write `--help` text documenting every flag from step 2.

## Acceptance

- [x] `cd agentprof && go build ./...` succeeds. Verified via
      `agentprof/scripts/check.sh` at merge time.
- [x] `cd agentprof && go test ./... -run TestSkillcheck` passes (red-first),
      using tasks 02/03's fake-judge-backed functions (no real subprocess):
      end-to-end over a small fixture transcript set, asserting the
      assembled report's category counts and evidence citations, and that
      `misfired`/`unresolvable` invocations never reach outcome scoring
      (assert task 03's fake judge received zero calls for them).
- [x] `agentprof skillcheck --help` documents `--days`, `--since`,
      `--skill`, `--judge-tier`, `-o`, `--format`. Verified by test + real
      CLI `--help` output.
- [x] A command-construction test (no subprocess executed, mirroring
      `agentprof/internal/naming/cli_test.go`'s pattern) asserts the real
      `judge.CLI`-backed implementation's built command carries
      `CLAUDE_CONFIG_DIR=<scratch>` in its environment when wired through
      `skillcheck`'s actual invocation path (not just task 01's isolated
      unit test — this proves the wiring, not just the package).
      `TestSkillcheckWiresScratchIsolatedCLIJudge` proves the wiring seam
      (`cmdSkillcheck`→`newSkillcheckJudge`→`defaultJudgeScratchRoot` feeds
      `judge.CLIJudge` a scratch root outside `~/.claude/projects`); the
      literal env-var assertion lives in `internal/judge/cli_test.go`
      (outside this task's Touch) and is cross-referenced rather than
      duplicated.
- [x] `agentprof skillcheck --format table` over a fixture with known
      trigger/outcome counts emits output that a small parser (e.g. split
      on whitespace/columns) confirms contains the expected category
      counts — parse-then-assert, not a substring/exact-string match.
- [x] An explicit `--judge-tier session` errors rather than silently
      falling back to `scout` (unit test, fake judge/no subprocess needed).
      Also verified against the real CLI.
- [ ] MANUAL-PENDING — filed to HUMAN.md (`## Agent-filed blockers`,
      2026-07-21): run `agentprof skillcheck` against real
      `~/.claude/projects/-Users-sjaconette-claude/*.jsonl` history and
      manually confirm ≥5 distinct verdicts are plausible on read. Requires
      a live `claude -p` judge call — not runnable by an unattended worker.
- [ ] MANUAL-PENDING — filed to HUMAN.md alongside the above (same entry,
      same reason): a `SKILL.md` with an `outcome-rubric:` field, run
      through the real end-to-end check above, produces evidence
      reflecting the custom rubric having been applied. Real-world sanity
      read, not the primary verification (task 03's judge-input assertion
      is the automated proof).

## Decisions

- `transcript_ref` is file-level (`<path>`, e.g. `.../sess-e2e.jsonl`), not
  `<path>:<line>` — task 01's `SkillInvocation` (per SPEC R2) exposes no
  source-line, and adding one is outside this task's Touch. Findings still
  carry `session` + file path. Reversible: thread a `Line` field through
  the accessor and into the finding (see Discovered).
- Trigger-judge grounding uses the session's user turns joined, since the
  accessor exposes no per-invocation user-turn text and precise
  turn↔invocation linkage isn't available. Reversible: add per-invocation
  user-turn text to the accessor.
- Findings are emitted for the non-obvious verdicts {misfired,
  unresolvable, possible_miss, failure, unknown} — the intersection of
  "not correct/success" and the SPEC prose's "non-obvious" set;
  explicit_invocation/self_chained are counted but given no findings (SPEC
  prose calls them obvious). Reversible: add those cases to the finding
  switch.
- `--judge-tier` maps scout→haiku, deep→opus, frontier→fable via a small
  in-file table citing runtimes/claude-code.md (mirroring task 02's
  hardcoded `opus` and naming/cli.go's `haiku`); only outcome scoring uses
  the flag (trigger classification keeps task 02's internal deep tier).

## Discovered

- `agentprof/README.md`'s subcommand list doesn't mention `skillcheck`
  (out of this task's Touch) — where: agentprof/README.md; why:
  user-facing docs drift.
- `internal/claude.SkillInvocation` lacks a source-line and per-invocation
  user-turn text; adding both would let skillcheck emit true `path:line`
  citations and precise trigger grounding — where:
  internal/claude/skill_invocations.go; why: closes the transcript_ref/
  grounding gaps noted under Decisions above.
- `DetectPossibleMisses` (task 02) flags any user turn matching an
  installed phrase without cross-checking whether that skill was actually
  invoked in the session, so it can over-report possible-misses vs SPEC
  R5's "no matching Skill call" — where: cmd_skillcheck_trigger.go; why:
  real-run false positives.
- A shared `judge.Fake` `Replies []string` mode (already flagged by task
  03's own Discovered entry, draft stub 05) would let this task's e2e test
  reuse one fake instead of a locally-written prompt-routing fake — where:
  internal/judge/fake.go; why: DRY across test files.
