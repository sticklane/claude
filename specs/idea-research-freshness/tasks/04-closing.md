# Task 04: version bump, link-checker recheck, manual-pending evidence

Status: pending
Depends on: 01, 02, 03
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R8)
Touch: .claude-plugin/plugin.json, specs/idea-research-freshness/evidence/manual-live-idea-run.md

## Goal

`.claude-plugin/plugin.json`'s `version` is bumped (skill behavior
changed in `/idea`, and its antigravity mirror). A manual-pending
evidence stub is created recording the one criterion this spec cannot
verify unattended: a human or attended session running `/idea` against
the `fresh/`, `stale/`, and `no-stamp/` fixtures (plus one paraphrase-only
rewording of the `fresh/` idea carrying the same grounding intent with no
listed trigger phrase) and confirming behavior matches the mechanical
checks — `fresh/` dispatches no research agent and cites the existing
location; `stale/`/`no-stamp/` dispatch research and write back a
refreshed stamp.

## Touch

Do not touch any SKILL.md — tasks 01-03 must already be merged (see
Depends on).

## Steps

1. Read the live `.claude-plugin/plugin.json` version at this task's own
   base commit (tasks 01-03 don't touch it, but unrelated work elsewhere
   in the repo may have bumped it since this spec was authored — always
   re-check live, don't trust a stated snapshot).
2. Bump the patch version by one.
3. Run `bash tests/test_doc_links.sh` once more as a final sanity check
   (task 01 already ran it after the stamp additions; this confirms
   nothing in tasks 02-03 broke a doc link).
4. Write `specs/idea-research-freshness/evidence/manual-live-idea-run.md`
   with unchecked checkboxes for the four manual-pending scenarios
   (fresh/stale/no-stamp/paraphrase) per the Goal above — Steven ticks
   these himself after running `/idea` live; this task does not run
   `/idea` itself (an unattended worker cannot — CLAUDE.md's execution-
   stage launch-authorization contract requires a live user request
   naming the stage).

## Acceptance

- [ ] `git show HEAD~1:.claude-plugin/plugin.json | grep -o '"version": "[^"]*"'`
      differs from the current file's `"version"` value, and the current
      value is a one-patch-level increment above it (never a decrease).
      `HEAD~1` is the commit immediately before your own version-bump
      commit.
- [ ] `bash tests/test_doc_links.sh` exits 0
- [ ] `test -f specs/idea-research-freshness/evidence/manual-live-idea-run.md`
      and it lists all four manual-pending scenarios as unchecked
      checkboxes
