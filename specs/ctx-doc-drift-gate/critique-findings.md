# Critique findings — READY WITH NITS (settled 2026-07-21)

SPEC.md sha256: 182b8c81d03529bd9c49ff2309ad2bbc4f86e89b01f695eef7dc200bfb1695c2
Verdict: READY WITH NITS — all findings from three critic rounds were
applied to the SPEC.md before this hash was taken; nothing remains open.

## 2026-07-21 — three-round critique (rounds bounded per token-discipline)

Round 1 (NOT READY): R2's single `grep -q 'depth'` acceptance was
gameable and left 7 of 8 flags uncheckable; R1's single-level tokenizer
would falsely reject the skill's nested `notes list`/`notes add` rows
(verified: `--file`/`--kind` live on the nested subcommands); waiver
under-specified against the antigravity mirror's identical row;
registry insertion left token-doctrine's "SEVEN specs" count and
cujs/02's frozen SLOT-7/6-marker gate stale. All applied.

Round 2 (NOT READY): waiver removal was delegated to cujs/02, whose
Touch has no grant to the test file (fix: retirement task owned by this
spec; stale waiver = R3 warning, never a failure); Landing-order (c)
under-enumerated cujs/02's stale counts (chain length, "SIX OTHER
specs" list, 6-marker gate, echo string); `--limit`/`--json` checks not
runnably section-scoped (fix: fixed `## Output-shaping flags` anchor +
sed-scoped greps). All applied.

Round 3 (READY WITH NITS): "in one commit" vs "defer the amendment"
ambiguous under a live cujs drain lease (fix: a live lease defers the
ENTIRE registry commit atomically, R2 filed blocked); the retirement
task's own acceptance was unstated (fix: "R1 test green with the
seeded entry removed" — premature runs self-detect); the rust-caution
acceptance was prose-only (fix: `grep -c 'NOT rust'` = 0 +
`grep -q 'ctx tree context-tree/src'`). All applied.

Live-lease note at settle time: specs/ctx-cujs/DRAIN-OWNER.md showed an
active lease (gen 7, 2026-07-21) — the breakdown session must re-check
it before the registry commit.
