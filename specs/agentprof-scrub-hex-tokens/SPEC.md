# agentprof: scrub lowercase-hex API tokens from turn frames

Status: open
Priority: P1
Breakdown-ready: true

## Problem

The turn-frame secret scrub (`agentprof/internal/claude/scrub.go`) has two
classes: (a) known secret prefixes, and (b) maximal `[A-Za-z0-9_-]{24,}`
runs mixing digits, uppercase, AND lowercase. A lowercase-hex API token
matches neither — no known prefix, no uppercase — so it reaches turn
frames verbatim. Observed 2026-07-11: a 40-char lowercase-hex Todoist API
token pasted into an automation-session prompt appeared un-redacted in a
turn frame, flowing into the rolling profiles the launchd refresh job
generates and the workboard serves. The observed frame's exact preceding
bytes were `Todoist token: ` — the keyword `token` plus a colon and space
immediately before the hex run — so the keyword-gated rule below redacts
this incident's shape verbatim. (Rotation of that token is filed in
HUMAN.md.)

The gap is not an oversight to fix with a blanket hex rule: git SHAs are
40-char lowercase hex too, and README documents that UUIDs, git SHAs, and
kebab-case slugs are deliberately unmatched — turn frames like
"revert commit 3f4a…" must stay readable. Shape alone cannot separate a
40-hex token from a 40-hex SHA.

## Solution

Add class (c): keyword-gated hex redaction. A maximal case-insensitive hex
run of 24+ chars is redacted only when a secret keyword — token, key,
secret, password, bearer, credential, apikey / api-key / api_key — occurs
within a short window (proposed: 40 chars) of text immediately before the
run. "Todoist token: 23596f…" redacts; "revert commit 3f4a90…" does not.
False positives like "the commit token 3f4a…" are acceptable and
documented — over-redaction of a frame costs readability (recoverable via
`--name-turns`, which renames `[redacted]` frames); under-redaction leaks
a credential into served artifacts.

Residual risk, stated plainly: this closes the keyword-adjacent subclass
only. A bare hex paste with no secret keyword in the window remains
unredactable by shape — it is byte-for-byte indistinguishable from a git
SHA, which README's carve-out deliberately preserves. The rest of the
class is carried operationally: token rotation on discovery, paste
hygiene, and the frame denylist for known-value strings.

Rejected alternative: unconditionally redacting all 24+/32+ hex runs —
it would blank every SHA-bearing turn frame, and `--name-turns` recovery
is best-effort (it failed on this machine's stale-auth scratch config on
2026-07-12), so the readability loss is not reliably recoverable.

## Requirements

- R1 **Keyword-gated hex class in scrub.** `scrub()` gains class (c),
  applied strictly after (a) and (b) — a keyword-adjacent hex sub-run
  inside a larger mixed-case token run is therefore consumed by (b)'s
  whole-run redaction first, and (c) only sees text (a)/(b) left behind:
  a maximal `[0-9a-fA-F]{24,}` run is replaced with
  `[redacted]` iff a secret keyword (case-insensitive: `token`, `key`,
  `secret`, `password`, `bearer`, `credential`, `api[-_]?key`) appears in
  the 40 characters preceding the run's token-run start. Runs already
  inside a `[redacted]` replacement are not double-processed.
- R2 **Behavior-pinning tests.** Table-driven tests in `scrub_test.go`
  covering at minimum: the observed incident's shape verbatim — a prompt
  containing `Todoist token: ` followed by a SYNTHETIC 40-char
  lowercase-hex value (never the real one) → redacted; keyword+40-hex →
  redacted; bare 40-hex SHA in
  prose (no keyword in window) → untouched; keyword more than the window
  before the run → untouched; 24-hex with keyword → redacted; 23-hex with
  keyword → untouched; mixed-case hex with keyword → redacted; a keyword
  followed by a larger mixed-case token run embedding a hex sub-run →
  one whole-run `[redacted]` (pins the (b)-before-(c) order); existing
  class (a)/(b) cases unchanged (no edits to existing test expectations).
- R3 **Docs.** README's "Turn frames: secret scrubbing and naming"
  section documents the keyword-gated hex rule and its deliberate
  false-positive trade-off; the "deliberately not matched" sentence is
  updated so SHAs-in-prose remain the documented carve-out. SCHEMA.md
  needs no change unless it restates scrub classes (it does not today).

## Out of scope

- Rotating the leaked token and regenerating `~/.local/state/agentprof/*`
  (operational; HUMAN.md blocker).
- Backfilling committed evidence profiles (none under `specs/` contain
  the observed token — they predate 2026-07-11; the pinned-evidence
  denylist rule already governs future pins).
- Entropy-based or provider-database secret detection.
- The frame denylist mechanism (`denylist.go`) — separable and shipped.

## Acceptance criteria

- [ ] `cd agentprof && go test ./internal/claude/ -run Scrub` passes with
  the R2 table (`grep -c 'keyword' agentprof/internal/claude/scrub_test.go`
  ≥ 1; the word is absent from that file at authoring time) (R1, R2)
- [ ] A 40-char lowercase-hex run preceded by `token:` within the window
  redacts to `[redacted]`; the same run preceded only by `commit ` does
  not (asserted in the R2 table, not by string-diffing full output) (R1)
- [ ] `grep -ci 'keyword-gated' agentprof/README.md` ≥ 1 (phrase absent at
  authoring time) (R3)
- [ ] `bash agentprof/scripts/check.sh` green (gofmt, vet, tests)

## Open questions

- Window size: 40 chars is proposed; a keyword and colon plus whitespace
  fits well inside it. Widen only with a concrete missed-leak example.

## Parallelization

01 = R1+R2 (TDD, one session); 02 = R3 docs (after 01). No group — 02 is
minutes of work and depends on 01's final rule wording.
