# Task 04: skillcheck subcommand wiring, flags, and report output

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
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

- [ ] `cd agentprof && go build ./...` succeeds.
- [ ] `cd agentprof && go test ./... -run TestSkillcheck` passes (red-first),
      using tasks 02/03's fake-judge-backed functions (no real subprocess):
      end-to-end over a small fixture transcript set, asserting the
      assembled report's category counts and evidence citations, and that
      `misfired`/`unresolvable` invocations never reach outcome scoring
      (assert task 03's fake judge received zero calls for them).
- [ ] `agentprof skillcheck --help` documents `--days`, `--since`,
      `--skill`, `--judge-tier`, `-o`, `--format`.
- [ ] A command-construction test (no subprocess executed, mirroring
      `agentprof/internal/naming/cli_test.go`'s pattern) asserts the real
      `judge.CLI`-backed implementation's built command carries
      `CLAUDE_CONFIG_DIR=<scratch>` in its environment when wired through
      `skillcheck`'s actual invocation path (not just task 01's isolated
      unit test — this proves the wiring, not just the package).
- [ ] `agentprof skillcheck --format table` over a fixture with known
      trigger/outcome counts emits output that a small parser (e.g. split
      on whitespace/columns) confirms contains the expected category
      counts — parse-then-assert, not a substring/exact-string match.
- [ ] An explicit `--judge-tier session` errors rather than silently
      falling back to `scout` (unit test, fake judge/no subprocess needed).
- [ ] MANUAL-PENDING (requires a live `claude -p` judge call and real
      accumulated history — not runnable by an unattended worker; a human
      or an attended session runs this and records the result in this
      task's evidence): run `agentprof skillcheck` against this machine's
      real accumulated `~/.claude/projects/-Users-sjaconette-claude/*.jsonl`
      history and manually confirm at least 5 distinct verdicts (spanning
      trigger and outcome categories) against their cited evidence lines
      are plausible on read.
- [ ] MANUAL-PENDING (same reason as above): a `SKILL.md` with an
      `outcome-rubric:` frontmatter field, when included in the real
      end-to-end run above, produces a report whose per-finding evidence
      for that skill's invocations reflects the custom rubric having been
      applied (the automated proof is task 03's judge-input assertion;
      this is a real-world sanity read, not the primary verification).
