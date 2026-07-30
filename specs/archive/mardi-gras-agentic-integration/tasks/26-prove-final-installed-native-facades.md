# Task 26: prove the final installed native façades

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status is always the frozen initial display value `pending`; workers and orchestrators update bd, never this line. -->
<!-- Task definitions are immutable after registration. Workers report progress, decisions, and deferred questions to the orchestrator; they do not rewrite task files. -->

Status: pending
Depends on: 01, 17, 25, 38, 37
Priority: P0
Budget: 24 turns
Spec: ../SPEC.md (requirements R9, R11, R15, R17, R19)
Touch: HUMAN.md, specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json

## Goal

MANUAL-PENDING: install the exact Task 25 immutable package and run the full
native façade matrix through authenticated Claude Code, Codex, and
Antigravity managers. The resulting canonical report binds the package
manifest and execution-environment hashes plus each exact runtime binary
fingerprint, and it is the only artifact this task may produce besides
removing its own HUMAN blocker.

## Touch

This is authenticated runtime evidence, not implementation. Do not modify
skills, profiles, package files, the tracker, Task 27's HUMAN entry, or promote
unsupported Antigravity drain/resume. If the required matrix or final package
changes after registration, create a new dependent immutable task and wire it
before Task 27; do not rewrite this definition or append live acceptance prose.

## Steps

1. MANUAL-PENDING because real authenticated native runtime managers and
   interactive PTYs are required; verify the exact committed HUMAN entry and
   Task 25 source revision before starting.
2. Install Task 25's source revision into the normal verified package
   location, resolve it with `agentic package current --json`, and require the
   reported manifest and execution-environment hashes to match the installed
   files before any canary.
3. Run Task 38's `run-native-facade-matrix.sh` for Claude Code and Codex
   work/build/drain and Antigravity work/build, including explicit
   pre-spawn rejection of Antigravity drain/resume.
4. Validate the atomic complete report, prove cross-package and
   cross-fingerprint merges fail and a changed runtime resets only that
   runtime, then rerun the final package-current verification.
5. In the same evidence commit, remove only Task 26's exact unchecked HUMAN
   line and retain Task 27's line byte-for-byte.

## Acceptance

- [ ] `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/run-native-facade-matrix.sh` → authenticated Claude Code and Codex work/build/drain plus Antigravity work/build complete claim, work, independent review, one gate, close, and cleanup against the exact installed Task 25 package; unsupported modes fail before spawn (L3; manual-pending for credentials and real PTYs).
- [ ] `python3 -c 'import json; p="specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json"; d=json.load(open(p, encoding="utf-8")); assert d["schema"]=="agentic.facade-canary/v1" and d["complete"] is True'` → the bounded report is schema-tagged and complete; the preceding L3 matrix validates its package identity pair and per-runtime fingerprints (L2).
- [ ] `python3 -m pytest tests/test_mardi_gras_registration_migration.py -q -k 'manual_blocked or final_certification'` → registration and live graph fixtures keep Tasks 26 and 27 blocked until their distinct authenticated human actions resolve (L2).
- [ ] `python3 specs/mardi-gras-agentic-integration/tests/validate-manual-certification.py --task 26 --commit HEAD --facade-report specs/mardi-gras-agentic-integration/FACADE-CANARY-REPORT.json` → the evidence commit changes only the façade report and HUMAN.md, deletes exactly Task 26's attested line in that same commit, and leaves every other HUMAN byte—including Task 27's blocker—unchanged (L3).
