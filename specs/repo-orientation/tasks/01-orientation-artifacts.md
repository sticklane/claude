# Task 01: Root AGENTS.md, CLAUDE.md pointer, status dashboard

Status: done
Depends on: ../../review-fixes/tasks/01-plugin-manifest.md, ../../chaining-antipatterns/tasks/03-antipattern-guards.md
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R2, R3)

## Goal

Create the orientation layer: root `AGENTS.md` (repo map / state /
commands, <=60 lines), the `@AGENTS.md` line in CLAUDE.md's first 10
lines, and the deterministic `specs/status.sh` dashboard. Follow the
spec's R1-R3 exactly, including the Status-parse rule (first `^Status:`
match anywhere in the file; none -> `none`) and re-running every
command listed in `## Commands` (rf-01 has landed, so
`claude plugin validate .` qualifies only if it exits 0 when you run it).

## Touch

- AGENTS.md (new)
- specs/status.sh (new)
- CLAUDE.md (one line; also edited by context-management 01, chaining-antipatterns 02/03 — deps above serialize this)

## Steps

1. Write AGENTS.md per R1 (three sections, pointers not descriptions,
   map reflects directories existing now).
2. Add the `@AGENTS.md` import/pointer line in CLAUDE.md's first 10
   lines (R2); keep CLAUDE.md <=200 lines; duplicate no content.
3. Write specs/status.sh per R3 (<=40 lines, executable, POSIX tools
   only, TOTAL summary, empty-queue exit 0).
4. Do NOT bump plugin.json (review-fixes 99 owns the combined bump).

## Acceptance

- [x] `test -f AGENTS.md && grep -q "^## Repo map" AGENTS.md && grep -q "^## State" AGENTS.md && grep -q "^## Commands" AGENTS.md && [ "$(wc -l < AGENTS.md)" -le 60 ]` -> exit 0 (R1) — verifier: exit 0, 35 lines, all three sections (../evidence/01-orientation-artifacts.md)
- [x] `grep -q "specs/QUEUE.md" AGENTS.md && grep -q "status.sh" AGENTS.md && grep -q "HANDOFF.md" AGENTS.md && grep -q "Status:" AGENTS.md` -> exit 0 (R1) — verifier: exit 0, all four State pointers present
- [x] `head -10 CLAUDE.md | grep -q "AGENTS.md" && [ "$(wc -l < CLAUDE.md)" -le 200 ]` -> exit 0 (R2) — verifier: pointer at line 8, CLAUDE.md 89/200 lines, no duplicated orientation content
- [x] `test -x specs/status.sh && bash -n specs/status.sh && [ "$(wc -l < specs/status.sh)" -le 40 ]` -> exit 0 (R3) — verifier: exit 0, 33 lines, POSIX sh/grep/sed/sort/uniq only
- [x] `out=$(mktemp) && ./specs/status.sh > "$out" && grep -q "TOTAL" "$out" && for f in specs/*/tasks/*.md; do grep -q "$f" "$out" || exit 1; done` -> exit 0 (R3) — verifier: all 30 task files rendered, TOTAL done: 20 / in-progress: 2 / pending: 8
- [x] `d=$(mktemp -d) && mkdir -p "$d/specs" && (cd "$d" && bash "$OLDPWD/specs/status.sh")` -> exit 0 (R3 empty-queue; run from repo root) — verifier: empty-queue notice printed, exit 0; first-^Status:-anywhere and no-Status->none rules confirmed via constructed fixture
- [x] Manual dry-read per the spec's end-to-end criterion: opening ONLY AGENTS.md and running ./specs/status.sh answers what the repo is, where things live, which commands are verified, what work is open, and where a handoff would be — verifier dry-read: all five questions answerable; Commands section re-verified truthful; plugin.json untouched (0.6.2)
