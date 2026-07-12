# Handoff: cross-runtime (claude/codex/antigravity) parity testing

## Task

User ask (repeated verbatim twice): "perform a thorough test that
functionality is the same across codex, agy, and claude. find a
lightweight way to automatically test that" — freehand work, no spec/task
file. All work is on `main` directly (not a spec/task branch), committed
and pushed through `1dd1417`.

## State — done, with evidence

1. **`tests/test_codex_parity.sh`** (commit `a05c5bc`) — structural +
   symlink-resolution gate for `codex/.agents/skills/`, sibling to the
   pre-existing `tests/test_antigravity_parity.sh`. Found and fixed two
   real bugs: missing `prose-review` symlink (added), and `critique`/
   `fleet`/`workflow-author` had no exemption (added a "What's not
   ported" table to `codex/README.md`). Green.

2. **`runtimes/codex.md`** (commit `c4229d8`) — new runtime profile;
   codex had a working port but no profile, so `evals/run.sh`'s existing
   generic runtime dispatch (via `runtimes/parse_headless.py`) had
   nothing to resolve. Headless template `codex exec --skip-git-repo-check
   --ephemeral --sandbox workspace-write "<prompt>"`, confirmed live via
   `codex/verify-live.sh`'s pre-existing results (not re-tested by me
   this session). Known limitation, already documented: the four
   launch-gated skills' explicit `$name` invocation is unreliable on
   Codex (upstream bugs openai/codex #19695/#10585/#23454) — auto-trigger
   works fine.

3. **`evals/run.sh` provisioning** (commit `c4229d8`, further generalized
   by another concurrent session in `4a58ecd` with `SKILLS_ROOT`/
   `AGENTS_ROOT`/`MAX_TURNS` — compatible, not conflicting) — every
   fixture now gets BOTH `.claude/skills/` and `.agents/skills/` layouts
   unconditionally, so a fixture is runtime-portable without
   re-provisioning.

4. **4 new evalsets** (commit `6a8fd6c`): `evals/build/01-single-task/`,
   `evals/autopilot/01-security-refusal/`, `evals/critique/01-clean-spec/`,
   `evals/evals/01-scaffold-new-skill/`. Coverage went from 2 skills
   (breakdown, drain) to 6. Each verified structurally: `setup.sh` runs
   clean, `assert.sh` correctly RED pre-skill (except autopilot, whose
   correct behavior is a no-op — verified RED by simulating a wrongful
   launch instead). **None of the 4 new evalsets have been run live**
   (real paid model spend) — only structural/RED-state verification.
   `./evals/run.sh <skill>` fires real spend; that's a user decision.

5. **Antigravity doctrine — corrected TWICE this session** (commits
   `686da64`, `1dd1417`):
   - First wrong claim: "Antigravity has no headless harness at all." I'd
     tested the wrong binary — `~/.antigravity/antigravity/bin/agy`
     (the Antigravity.app bundle's OWN launcher script) shadows
     `/opt/homebrew/bin/agy` (the REAL `antigravity-cli` Homebrew
     package) on PATH. The impostor's `chat` subcommand just opens a GUI
     window and returns instantly with empty stdout.
   - Second, bigger finding: the REAL `agy -p "<prompt>"` genuinely
     blocks and prints to stdout (confirmed live: a plain reply, AND a
     real skill auto-trigger — `list-specs` ran its bundled
     `specs/status.sh` correctly). BUT wiring it into `evals/run.sh`
     end-to-end, it did NOT confine itself to the isolated `$EVAL_DIR`
     — it edited real tracked files elsewhere in this actual checkout
     instead (`tests/fixtures/workboard/demo-repo/...`), apparently
     reusing a stale workspace from an earlier manual test. **Caught
     immediately, reverted cleanly** (`git checkout --` + `rm` the new
     file; `tests/test_workboard_render.sh` still passes). This is a
     real, reproduced risk, not theoretical.
   - Net result: `runtimes/antigravity.md` now documents `agy -p`
     accurately (real, live-tested, but flagged **UNSAFE for
     isolated/unattended use**). `evals/run.sh` **hard-blocks**
     `.claude/runtime.md: antigravity` with a clear error (not just a
     doc warning — one already wasn't enough). Antigravity functional
     parity stays blocked, now for a precise, live-verified reason
     (workspace isolation) instead of a wrong one (no CLI).
   - `runtimes/test_parse_headless.py`'s NONE-sentinel tests were moved
     off antigravity onto a new synthetic fixture,
     `runtimes/fake-runtime-no-headless.md`, since antigravity no longer
     exemplifies "no headless template."

## Design direction for next session: sync via genericity, not just gates

User's explicit ask when handing this off: don't just keep adding
parity *tests* that catch drift after the fact — also make skills
generic enough that drift is structurally harder to introduce in the
first place, so the three runtimes stay in sync with less mirroring
effort to maintain. This session added detection (test_codex_parity.sh,
the evalsets); it did NOT address the underlying cause. Concretely, for
a future session to investigate:

- **Audit where the port chain (`.claude/` → `antigravity/` → `codex/`)
  carries runtime-specific content that COULD be runtime-agnostic
  instead.** E.g., the four launch-gated skills (`drain`/`build`/
  `autopilot`/`evals`) are real, separately-maintained content in all
  three trees today (Claude Code SKILL.md, antigravity workflow +
  skill, codex real-content wrapper) specifically because each runtime's
  launch-gating mechanism differs (`disable-model-invocation` vs.
  `allow_implicit_invocation: false` vs. Antigravity's human-launched
  workflow convention) — that's inherent, not accidental duplication.
  But other divergences may be incidental: e.g., the antigravity-mirrored
  `evals.md` I just edited twice this session (manual-launch vs.
  scripted `agy -p`) is exactly the kind of runtime-specific procedural
  detail that drifts because it's spelled out per-runtime rather than
  factored into something shared.
- **Look at what `runtimes/*.md` already generalizes well as a model**:
  the tier language (scout/session/deep/frontier) plus the `## Headless`
  contract shape already let ONE mechanism (`parse_headless.py`) serve
  claude-code/antigravity/codex/gemini-cli without per-consumer
  special-casing — new runtime, no consumer edits. Where else in the
  skill bodies themselves (not just the runtime-profile layer) could a
  similar abstraction replace three hand-maintained copies of the same
  procedure with one procedure plus a thin per-runtime adapter?
- **This is a real architecture investigation, not a quick fix** — don't
  start it inside an already-over-budget session. Likely shape: a scout
  pass cataloging every place `.claude/skills/*/SKILL.md`,
  `antigravity/.agents/{skills,workflows}/*`, and
  `codex/.agents/skills/*` diverge in PROCEDURE (not just existence),
  then a design pass on which divergences are load-bearing
  (runtime-mechanism differences) vs. incidental (would read identically
  if factored out), consistent with `docs/anthropic-playbook.md` and
  this repo's own `/design` skill for exactly this kind of
  architecture-choice work.

## Next step (if continuing this exact ask)

Untested candidate fix for antigravity's workspace-isolation bug:
`agy`'s `--new-project` flag ("Create a new project for this session") —
NOT tried yet, deliberately, to avoid a second uncontrolled file
mutation while investigating. If picking this up:
1. Test `--new-project` in an isolated scratch dir FAR from any real repo
   first (e.g. `/tmp/agy-isolation-test`), never directly against
   `$EVAL_DIR` inside `~/claude` again without that isolation proven.
2. If it reliably confines `agy -p` to the invoking directory, update
   `runtimes/antigravity.md`'s Headless template to add `--new-project`,
   remove the hard-block in `evals/run.sh`, and restore the automated
   run step in `antigravity/.agents/workflows/evals.md` (currently
   reverted to manual Agent Manager launch).
3. If `--new-project` doesn't fix it, that's a legitimate place to stop
   — antigravity's functional parity remains manual-pending per this
   repo's own `mirror-verification.md` doctrine (a documented, accepted
   escape for runtimes without a safe scriptable relaunch).

Other legitimate next steps, not started: live-run the 4 new evalsets
(real spend, user's call); author evalsets for more of the remaining
~13 skills not yet covered; verify `--model`/`--mode` flag *values* on
`agy` live (only flag *existence* was confirmed, per `runtimes/
antigravity.md`'s own "unverified" caveats).

## Files touched this session

- `tests/test_codex_parity.sh` (new), `codex/README.md`,
  `codex/.agents/skills/prose-review` (new symlink)
- `runtimes/codex.md` (new), `runtimes/antigravity.md` (rewritten twice),
  `runtimes/README.md`, `runtimes/fake-runtime-no-headless.md` (new),
  `runtimes/test_parse_headless.py`
- `evals/run.sh` (provisioning + antigravity hard-block),
  `.claude/skills/evals/SKILL.md` (doc fix)
- `evals/build/01-single-task/*`, `evals/autopilot/01-security-refusal/*`,
  `evals/critique/01-clean-spec/*`, `evals/evals/01-scaffold-new-skill/*`
  (all new)
- `.claude/rules/mirror-verification.md` (stale citation fixed)
- `antigravity/.agents/workflows/evals.md` (reverted to manual launch,
  with the finding cited)

## Gotchas learned the hard way

- **`agy`/`antigravity` name collision is real on this machine**:
  `~/.antigravity/antigravity/bin` precedes `/opt/homebrew/bin` in
  `$PATH`. Always verify `agy --version` (one line = real
  `antigravity-cli`, three lines = the app-bundle impostor) or use the
  absolute path. Personal memory file saved:
  `~/.claude/projects/-Users-sjaconette-claude/memory/feedback_antigravity_cli.md`.
- **Never trust "has a headless template" as "safe for isolated use"**
  without a live end-to-end test through the actual isolated-fixture
  path — the raw CLI working in a scratch dir does NOT prove it stays
  confined to that dir under different invocation patterns.
- This repo has multiple concurrent Claude Code sessions active in the
  same checkout regularly (confirmed via `claude agents --json` and live
  file changes mid-session) — commit+push immediately after each small
  chunk rather than batching, to surface collisions early
  (`~/.claude/.../memory/feedback_commit_push_cadence.md`).

## Verification

- `for t in tests/test_*.sh; do bash "$t"; done` — all green as of
  `1dd1417`.
- `python3 -m pytest runtimes/test_parse_headless.py -q` — 13 passed.
- `bash evals/runner-selftest.sh` — OK.
- `bash tests/test_doc_links.sh` — pass: 16 fail: 0.
- `./bin/check-agent-model-pins`, `claude plugin validate .`,
  `./specs/status.sh` — all OK (run mid-session, not re-verified at
  final commit but no touched file should affect them).
