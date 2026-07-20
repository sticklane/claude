Status: done
Discovered-from: 01-enforce-section-read-and-worker-prompt-delivery.md
Spec: ../SPEC.md
Priority: P3
Promotion-ready: true
Promoted-by-run: afeb2e0118315ce0
Budget: 3 turns
Touch: .claude-plugin/plugin.json

# Bump plugin.json version for the drain skill behavior change

Task 01 changed `/drain`'s documented procedure (Grep-then-offset reads,
path-pointer Worker prompt delivery) but did not touch
`.claude-plugin/plugin.json`, which CLAUDE.md says to bump whenever skill
behavior changes. Confirmed 2026-07-20 via `git log --oneline --all --
.claude-plugin/plugin.json`: neither task 01's merge (17831e1) nor task
02's merge (ce174fa) touched plugin.json; the file's current version is
0.9.20 (last bumped by an unrelated commit-message-formats change).

## Acceptance

- [x] `grep -q '"version": "0.9.21"' .claude-plugin/plugin.json` exits 0
      (current version is 0.9.20, confirmed absent "0.9.21" as of
      2026-07-20) — verified: exit=0 on branch task/04-plugin-json-version-bump
- [x] `jq . .claude-plugin/plugin.json >/dev/null` exits 0 (JSON stays
      valid) — verified: exit=0

## Original report

Bump plugin.json version for the drain skill behavior change

Task 01 changed `/drain`'s documented procedure (Grep-then-offset reads,
path-pointer Worker prompt delivery) but did not touch
`.claude-plugin/plugin.json`, which CLAUDE.md says to bump whenever skill
behavior changes. Confirm whether task 02 or 03 already covers this bump;
if not, bump the version.
