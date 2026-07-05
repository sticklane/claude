# Fail loudly when a Claude-internal format drifts

Status: done
Priority: P2
Source: holistic best-practices review (2026-07-04) — critic findings #2, #4, #5

## Problem

Parts of the dashboard depend on internal Claude formats with **no supported
CLI**: `~/.claude/projects/<esc>/sessions-index.json` (recent/stale session
history), the `bundled-skills/` tmp path, and residual PID-record fields. The
parsing is defensive (won't crash), which is good — but on a format change the
affected section renders **empty and indistinguishable from "no work."** The
dashboard could quietly lie for weeks after a Claude Code update. This is the
exact fragility the tool's value rests on, so it must be *observable*.

Related silent-misclassification bugs:
- **Path matching is byte-exact** (finding #4): `collect_sessions` keys on
  `projectPath`; `_resolve`/`repo_keys` compare un-`realpath`'d REPOS.md paths.
  A symlinked or trailing-variant path drops every session for that repo into
  "orphans."
- **PID-reuse** (finding #5): `os.kill(pid, 0)` alone can mark a recycled PID as
  an active session.

## Scope

1. Add a lightweight "source health" check: when a source **exists** but yields
   **zero** parsed records (e.g. `sessions-index.json` present but `entries`
   empty-after-filter; PID dir non-empty but nothing parsed; a plugin dir with
   no readable `SKILL.md`), surface a small muted "source unreadable?" marker on
   that section instead of a clean-empty render.
2. Canonicalize both sides of session→repo matching with `os.path.realpath`
   (or `Path.resolve()`) before comparison.
3. Cross-check PID liveness with the process's start time / name (or prefer the
   `claude agents --json` status once [supported-cli-migration] lands) so a
   recycled PID isn't reported as an active session.
4. Isolate each internal-format parser behind a single function with a one-line
   comment naming the exact undocumented file + the Claude Code version last
   verified against, so drift is easy to locate.

## Acceptance

- Simulating a schema change (rename a key in a fixture) makes the section show
  the "source unreadable?" marker rather than empty; unit test covers this.
- A session whose `cwd` is a symlink to a tracked repo nests under that repo,
  not orphans (unit test with a realpath fixture).
- `scripts/check.sh` green.

## Out of scope

- Replacing sessions-index with a CLI — none exists; revisit if Anthropic ships
  a `claude sessions --json`. Track in README's known-limitations note.
