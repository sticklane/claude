# Drain plugin-cache path resolution

## Problem

The same 11-transcript audit that motivated `drain-read-once-discipline`
also found a distinct, smaller failure: two independent `/drain` sessions
(`personal-vault/a71b86fc`, `fooszone/71294ab5`) — both running against the
_installed marketplace plugin_ rather than the toolkit's own dev checkout —
each first guessed a stale plugin-cache path
(`.claude/plugins/cache/agentic-toolkit/agentic/0.9.19/...`), got nothing,
then had to re-derive the correct current path before proceeding. This isn't
random hallucination: `0.9.19` is a real, recent value this exact repo's
`.claude-plugin/plugin.json` held before being bumped — it appears verbatim
in several committed spec/evidence files still present in the repo (e.g.
`specs/drain-multi-spec-swarm/critique-findings.md:114`,
`specs/commit-message-doctrine/evidence/02-skill-formats-mirrors-and-bump.md:26`).
A session that had recently read one of those files plausibly reused that
number instead of checking the actually-installed version.

Root cause, located precisely: `reference.md:641-642` says a path-pointer
resolves to `.claude/skills/build/SKILL.md` "when the toolkit is in-repo,
otherwise the plugin cache path found at dispatch" — naming no concrete
resolution procedure for the "otherwise" branch. Every session has had to
invent its own method, and at least twice that meant reusing a version
number already sitting in context rather than checking the real one.

The repo already ships an authoritative, tested primitive for exactly the
"what version is actually installed" half of this: `bin/plugin-installed-version`
(reads `claude plugin list --json` — a global CLI call needing no filesystem
path knowledge — and is the shared read `hooks/plugin-staleness` and
`bin/refresh-plugins` already rely on, per its own header comment and
`tests/test_plugin_version_helper.sh`). Confirmed live during this spec's
authoring: the actual installed cache directory is
`~/.claude/plugins/cache/agentic-toolkit/agentic/0.9.21/` (a full mirrored
copy of the repo, `bin/` included) — one patch version ahead of this dev
checkout's own `plugin.json` (`0.9.20`), a live, present-tense illustration
of exactly the drift this spec is about.

**A real architectural constraint found while designing the fix, not
resolved here:** a session running in a _non-toolkit_ repo (the two evidenced
failures) has no reachable copy of `bin/plugin-installed-version` until it
already knows the plugin-cache root — and finding the plugin-cache root is
the very problem being solved (`bin/`'s own location is inside the versioned
directory it's trying to help locate). So the fix cannot be "call this
script" alone for the plugin-cache-install case; it must also give a
self-contained resolution recipe that needs nothing but the `claude` CLI
(already required for the session to exist) and `python3` (already assumed
present elsewhere in `evals/`, per `runtimes/parse_headless.py`).

## Solution

One canonical resolution recipe, expressed as literal runnable code (per
explicit direction: prefer code over prose text here), referenced everywhere
a path-pointer needs plugin-cache resolution — never re-derived ad hoc:

1. **Add the canonical recipe to `reference.md`**, near its existing
   path-pointer convention (the "Worker prompt" section, `reference.md:623-642`
   is the evidenced call site) — a fenced, literally-runnable two-step Bash
   block, not a prose description of steps:
   - Step 1 (cheapest, tried first, no CLI call): does
     `.claude/skills/<skill>/<file>` exist relative to the current repo root?
     If yes, that is the path — toolkit is in-repo, stop here.
   - Step 2 (plugin-cache branch): resolve the installed version via
     `claude plugin list --json` (the exact mechanism `bin/plugin-installed-version`
     already implements — quote its parse logic rather than reinventing a
     second one), then construct
     `$HOME/.claude/plugins/cache/agentic-toolkit/agentic/<version>/.claude/skills/<skill>/<file>`
     and verify it exists before using it. **Never** substitute a version
     number recalled from anywhere else in the session's context (a spec, an
     evidence file, an earlier turn) — only ever the freshly-queried value.
   - Resolve once per session/generation and reuse the resolved path for the
     rest of that run rather than re-resolving per worker dispatch — the same
     "resolve once, reuse" discipline `drain-read-once-discipline` establishes
     for `reference.md`'s own content (cite it, don't restate the rationale).

2. **Add `bin/resolve-skill-path`**, a small script implementing exactly this
   two-step recipe, for the case where it _is_ reachable — running in-repo
   (the toolkit dev checkout itself, where `bin/` sits at a known relative
   path) — so the in-repo path takes one command instead of a hand-run
   fenced block, and so the recipe is unit-testable at all (a fenced
   markdown block cannot be asserted against). Interface:
   `bin/resolve-skill-path <repo-relative-path>` (e.g.
   `bin/resolve-skill-path .claude/skills/build/SKILL.md`) prints the
   resolved path on stdout and exits 0, or exits 1 with a stderr message
   naming what was tried, when neither branch resolves.
   `reference.md`'s recipe explicitly notes this script is the in-repo
   shortcut for the same steps — never claims it's reachable from a
   non-toolkit repo pre-bootstrap.

3. **Sweep for other vague plugin-cache-path phrasings.** `reference.md:645,648`
   ("resolved at dispatch") are the same call site's restatements, not new
   locations. Grep `.claude/skills/*/SKILL.md` and `.claude/skills/*/reference.md`
   for `"resolved at dispatch"` and `"plugin cache path"` and point every hit
   at the same canonical recipe (cite, don't restate) rather than leaving
   each skill to invent its own phrasing.

4. **Mirror only the portable half.** Step 1 (the in-repo existence check) is
   the same procedure in every runtime, modulo its own path convention, and
   is _incidental_ divergence per `.claude/rules/mirror-procedure-discipline.md`
   — port it. Step 2 (the `$HOME/.claude/plugins/cache/agentic-toolkit/...`
   construction) is Claude-Code-specific: `antigravity/.agents/workflows/drain.md:290`
   has no plugin-cache branch at all today, and `codex/.agents/skills/drain/SKILL.md:212`
   uses a different install layout entirely — this is _load-bearing_
   divergence (a capability/primitive difference), not incidental, so it
   must NOT be copied verbatim into either mirror. Each mirror instead gets
   only the runtime-neutral procedural line — "resolve once per session,
   never reuse a version number seen elsewhere in context" — worded to fit
   whatever resolution mechanism that runtime actually has (or its own
   documented absence of one). Manifest entry, plugin.json bump — same
   pattern as `drain-read-once-discipline`'s R6.

## Requirements

- R1: `reference.md`'s path-pointer convention (the "Worker prompt" section)
  states the two-step recipe as a fenced, runnable Bash block — not prose
  paraphrase — replacing the vague "the plugin cache path found at dispatch"
  phrasing at `reference.md:641-642`. Removing the old phrase is necessary
  but not sufficient: the acceptance check below separately confirms the
  recipe's own content was actually added, not just that the old vague
  phrase was deleted or reworded into something equally vague.
- R2: `bin/resolve-skill-path` exists, implements the two-step recipe,
  exits 0 with the resolved path on stdout on success, exits 1 with a
  stderr diagnostic on failure (neither in-repo nor plugin-cache resolves).
- R3: `tests/test_resolve_skill_path.sh` exists (mirroring
  `tests/test_plugin_version_helper.sh`'s shim-based approach — stub
  `claude plugin list --json` output rather than depending on a real
  installed plugin) covering: in-repo path exists → returns it without
  calling the CLI shim; in-repo absent, shim reports a version whose
  constructed plugin-cache path exists → returns that path; shim reports no
  matching plugin or the constructed path doesn't exist → exit 1 with a
  non-empty stderr message.
- R4: Every other `"resolved at dispatch"` / `"plugin cache path"` phrasing
  found by the Solution's step-3 sweep is repointed at the same canonical
  recipe (cite it by section name, don't restate the steps).
- R5: Only Step 1 (the in-repo check) is ported to
  `antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` in the same commit, classified
  _incidental_ per `.claude/rules/mirror-procedure-discipline.md`. Step 2
  (the `$HOME/.claude/plugins/cache/agentic-toolkit/...` construction) is
  classified _load-bearing_ (a Claude-Code-specific primitive neither mirror
  runtime has) and must NOT be copied verbatim into either mirror file —
  each gets only the runtime-neutral procedural line per Solution point 4.
- R6: `tests/mirror-procedure-manifest.txt` gets a new
  `<source>|<mirror>|<phrase>` entry for a phrase drawn from the
  runtime-neutral procedural line ("resolve once per session, never reuse a
  version number seen elsewhere in context" or a close paraphrase settled at
  breakdown time) — never from Step 2's Claude-Code-specific cache-path
  literal, since that text must not appear in the mirrors at all (R5).
- R7: `.claude-plugin/plugin.json`'s `version` is bumped.

## Out of scope

- Solving the deeper bootstrap question of whether Claude Code exposes a
  stable, version-independent way for a _live agent session_ (not a
  hook-config `${CLAUDE_PLUGIN_ROOT}` substitution) to learn its own
  currently-loaded skill's absolute install path. If such a mechanism
  exists and is confirmed during breakdown/implementation, it would obsolete
  the plugin-cache branch of the recipe entirely (no CLI call needed at
  all) — worth a fast-follow spec, but not blocking this one, which ships
  the CLI-based recipe that's confirmed to work today.
- `drain-read-once-discipline`'s re-read-repetition problem — distinct root
  cause (a stale/reused version number, not a redundant read of
  already-loaded content), tracked in that separate spec.
- Any skill other than `drain` that might have its own vague path-pointer
  phrasing — Solution step 3's sweep is scoped to `.claude/skills/*/SKILL.md`
  and `.claude/skills/*/reference.md`, so it will find and fix any that
  exist, but this spec's Problem statement has direct evidence only for
  drain's call site.

## Acceptance criteria

- [ ] `grep -c "plugin cache path found at dispatch" .claude/skills/drain/reference.md`
      → 1 today (verified 2026-07-20), 0 after the fix — R1, the vague
      phrase is gone.
- [ ] `grep -q "plugins/cache/agentic-toolkit/agentic" .claude/skills/drain/reference.md`
      → no match today (verified 2026-07-20; confirms the recipe literal
      isn't already present by coincidence), matches after the fix — R1's
      positive check: the recipe's own content was actually added, not just
      that the old vague phrase was deleted or reworded into something
      equally vague. Both criteria must hold together for R1.
- [ ] `[ -x bin/resolve-skill-path ]` — R2, script exists and is executable.
- [ ] `bash tests/test_resolve_skill_path.sh` passes — R3, the deterministic
      shim-based behavioral check (does not require a real installed
      plugin or network access).
- [ ] `grep -rn "resolved at dispatch\|plugin cache path" .claude/skills/*/SKILL.md .claude/skills/*/reference.md`
      — every hit after the fix is inside `reference.md`'s own canonical
      recipe section or a citation of it, none is an independent,
      unexplained "found at dispatch"-style phrase — R4. Depth ceiling: a
      grep-and-manually-classify check is the correctness-checkable floor
      for a sweep whose exact hit count can't be pinned before breakdown
      names every location; R3's script test is the behavioral complement
      for the primary evidenced call site.
- [ ] `bash tests/test_mirror_procedure_coverage.sh` passes, AND a direct
      grep for the R6 phrase (named at breakdown time, drawn only from the
      runtime-neutral procedural line) hits `reference.md` and both mirror
      files, AND `grep -c "plugins/cache/agentic-toolkit" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      shows 0 in both — R5/R6: the triple-file phrase grep is the
      non-vacuous positive check, the zero-count grep confirms the
      load-bearing Step 2 literal was correctly excluded from both mirrors.
- [ ] `grep -n '"version"' .claude-plugin/plugin.json` shows a value greater
      than `0.9.20` (today's dev-checkout value, verified 2026-07-20) — R7.

## Open questions

(none — the bootstrap question noted in Out of scope is explicitly deferred,
not open within this spec's scope)
