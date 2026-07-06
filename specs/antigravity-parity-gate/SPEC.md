# Mechanical parity gate: every .claude/ skill has a documented Antigravity counterpart or exemption

Priority: P0

## Problem

CLAUDE.md states the mirroring convention as a MUST ("when a skill
changes here, mirror the change there in the same commit... an unlisted
mirror silently ships un-mirrored") but nothing mechanically enforces it —
diligence is the only backstop. This session demonstrated the gap is real,
not hypothetical: **four separate specs written today** initially forgot
the antigravity mirror requirement entirely (`retire-static-dashboards`,
`narrow-autopilot`, `build-doc-currency-check`, `idea-research-freshness`)
and only caught it because a `critic` pass happened to check. There is
also a pre-existing, undetected gap: `.claude/skills/fleet/` and
`.claude/skills/workflow-author/` have **no** antigravity counterpart at
all. `fleet`'s absence is at least documented (`antigravity/README.md`:
"`/fleet` open-agents dashboard | Not ported — Antigravity's Agent
Manager is this surface natively") — `workflow-author`'s is not documented
anywhere.

## Solution

A new gate, `tests/test_antigravity_parity.sh`, checking **existence
parity only** — not "the right kind" of port (skill vs. workflow vs.
both), which is a judgment call this spec deliberately leaves to
humans/critique, per the ambiguity already visible today: 7 skills
(`breakdown`, `design`, `distill`, `gate`, `handoff`, `idea`, `onboard`)
currently exist as *both* a skill and a workflow in
`antigravity/.agents/`, which may be intentional convenience or drift —
reconciling that is out of scope here (see Out of scope). This gate only
asks: for every name under `.claude/skills/*/` and `.claude/agents/*.md`,
does **at least one** of `antigravity/.agents/skills/<name>` or
`antigravity/.agents/workflows/<name>.md` exist, OR is `<name>` listed as
an intentional exemption in `antigravity/README.md`'s "What maps to what"
table? `workflow-author` currently satisfies neither — this spec makes a
real decision to close that gap: **exempt it**, with a documented
rationale, rather than port it. `workflow-author`'s entire job is
authoring `.claude/workflows/*.js` scripts for the `Workflow` tool, a
Claude-Code-harness-specific orchestration primitive Antigravity has no
equivalent for (per the README's own existing row: "Ultracode workflow
scripts... Human-dispatched launch-list workflows — no scripted fan-out in
Antigravity") — there is nothing for a ported `workflow-author` to
produce there.

## Requirements

- **R1**: `tests/test_antigravity_parity.sh` lists every directory under
  `.claude/skills/` **except `_shared`** (a shared library, not a skill —
  17 directories exist there today, 16 of them skills) and every `.md`
  file under `.claude/agents/`, and for each name checks: does
  `antigravity/.agents/skills/<name>/` OR
  `antigravity/.agents/workflows/<name>.md` exist? (Agent names map by
  the same rule — `.claude/agents/critic.md` → `antigravity/.agents/
  skills/critic/`, matching the existing scout/critic/verifier pattern.)
- **R2**: If neither exists for a given name, the script checks whether
  `antigravity/README.md`'s "What maps to what" table contains a row
  exempting it — matching **only against the FIRST delimited token
  (backticked or slash-prefixed) of the table's first (left) `|`-delimited
  cell**, not anywhere within that cell. First-token anchoring, not mere
  "appears as a delimited token somewhere in the left cell," is required:
  the self-chaining row's left cell is "Skill self-chaining (/idea
  invokes /breakdown via the Skill tool)" — `/idea` and `/breakdown` ARE
  slash-prefixed delimited tokens *within* that cell, so a
  match-anywhere-in-the-cell rule still false-exempts both (that row's
  right cell does contain "Not ported"). Anchoring to the cell's FIRST
  token excludes this row correctly, since it begins with the prose word
  "Skill," not `/idea`. A matching row counts as an exemption **only if**
  its right cell also contains the literal string "Not ported" verbatim —
  no "or equivalent language" judgment call a bash parser can't make. If
  no such row exists, the script fails, printing the missing name.
- **R3**: `antigravity/README.md`'s table gains a new row for
  `workflow-author`, whose left cell **begins with** the delimited token
  `` `workflow-author` `` (satisfying R2's first-token anchor — not
  merely mentioning the name later in the cell) and whose right cell
  contains the literal string "Not ported" (per R2's exact-token
  requirement — not just a cross-reference to the existing "Ultracode
  workflow scripts" row's different wording, which doesn't contain that
  token), with the rationale from Solution ("no scripted fan-out primitive in
  Antigravity") stated alongside it.
- **R4**: The script exits 0 with no output when every name is covered
  (ported or exempted), and exits non-zero listing every uncovered name
  otherwise — same convention as `tests/test_doc_links.sh`.
- **R5**: This gate checks existence only, never content — it does not
  verify a mirrored skill's *behavior* matches its `.claude/` counterpart
  (that's what critique/review catches; this spec only catches "forgot to
  mirror at all" and "forgot to exempt").

## Out of scope

- Reconciling why 7 skills (`breakdown`, `design`, `distill`, `gate`,
  `handoff`, `idea`, `onboard`) currently exist as both a skill and a
  workflow in `antigravity/.agents/` — existence-parity is satisfied
  either way; this is a separate, human design question about Antigravity
  authoring conventions, not a gap this gate flags.
- Verifying mirrored content is behaviorally equivalent, current, or
  correctly translated (skill vs. workflow choice for a *specific* new
  skill) — R5.
- Wiring this into `evals/run.sh` or CI beyond the existing `tests/
  test_*.sh` auto-discovery (`for t in tests/test_*.sh; do bash "$t";
  done`, per AGENTS.md) — no new runner needed.
- Retroactively fixing any *other* undiscovered mirror-content drift
  beyond the fleet/workflow-author existence gap — this spec's fix is
  scoped to what R1-R4 mechanically detect.

## Acceptance criteria

- [ ] `bash tests/test_antigravity_parity.sh` exits 0 against the current
      repo state, after `workflow-author`'s exemption row (R3) is added —
      confirming every one of the 16 skills + 3 agents is either mirrored
      or exempted.
- [ ] Temporarily removing `fleet`'s "Not ported" row from
      `antigravity/README.md` and re-running the script (fixture): it
      fails, naming `fleet` as uncovered.
- [ ] Temporarily creating a fake new `.claude/skills/zzz-test-skill/`
      with no antigravity counterpart and no exemption row, then
      re-running: it fails, naming `zzz-test-skill`.
- [ ] `grep -n "workflow-author" antigravity/README.md` shows the new
      exemption row from R3.
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` (the existing runner)
      picks up and runs the new script with no additional configuration.

## Open questions

(none)
