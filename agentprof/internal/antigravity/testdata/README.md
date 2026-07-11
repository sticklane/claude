# Antigravity conversation fixture — ground truth

## Fixture

`conversations/d147c9da-7c14-4e02-a386-156a72b7bf99.db` — a real, unmodified
Antigravity CLI (`agy`) session `.db`, copied verbatim from
`~/.gemini/antigravity-cli/conversations/`. No fields extracted, re-encoded,
or edited.

## Capture conditions

- **Captured:** 2026-07-11, ~18:49 local time.
- **Command:** `agy --new-project --add-dir <scratch-dir> --model "Gemini 3.5 Flash (Medium)" --print "Reply with exactly these three words and nothing else: quick brown fox"`, run in a throwaway scratch git repo (not this repo).
- **Requested model:** `Gemini 3.5 Flash (Medium)`.
- **Observed model (gen_metadata field 21, the display string):**
  `Gemini 3.5 Flash (Medium)` — matches the request. (A different,
  secondary field — 28 — separately holds an internal tag
  `gemini-3.5-flash-low`; field 21 is the one Task 03's pricing table keys
  on, and it matches the existing `"Gemini 3.5 Flash (Medium)"` rate row
  with no new row needed.)
- **CLI output (the model's final visible response):** exactly
  `quick brown fox` — matched the requested format precisely, no extra
  text.

## Hand-counted ground truth (approximate, my own visible turn only)

These counts cover only the human-authored instruction and the model's
final visible reply — **not** the full request Antigravity actually sent
to the model, which additionally includes a large injected system
prompt (identity block, workspace/user info, `<slash_commands>`,
`<guidelines>`, `<communication_style>`, and an IDE lint-feedback
instruction — all visible as plaintext inside the `gen_metadata` blob).
That system-prompt overhead is real and large; it is why the raw
candidate token fields below (thousands of tokens) are far bigger than
what a hand count of just my sentence would suggest.

- My instruction: "Reply with exactly these three words and nothing
  else: quick brown fox" — 13 words, hand-counted approx **15-18 tokens**.
- Model's visible reply: "quick brown fox" — 3 words, hand-counted approx
  **3-4 tokens**.

## Candidate raw field values (NOT confirmed — for Task 04 to verify)

Decoded via `protoc --decode_raw` against the single `gen_metadata` row
(`idx=0`, `steps.step_type=15`). The most plausible usage-count location
found, nested under top-level field `17.2`:

```
17 {
  2 {
    1: 1020
    2: 17234
    3: 71
    6: 24
    9: 68
    10: 3
  }
}
```

Working hypothesis (magnitude-based, unconfirmed): sub-field `2` (17234)
is a plausible total **prompt/input token** count (consistent with the
large injected system prompt this session actually sent, not just my
13-word instruction), and sub-field `3` (71) is a plausible **completion
token** count (larger than my 3-word visible reply alone would suggest —
Gemini may have generated additional non-displayed content, e.g. an
internal stop-sequence or thinking tokens, even with no reasoning summary
shown). Sub-fields `6`, `9`, `10` (24, 68, 3) are unidentified — possibly
cache-read tokens, a step/turn counter, or tool-call counts. None of this
is certified; Task 04 owns confirming which sub-field is which against
this fixture plus its own corrupted-copy fixture.

## Regenerating a fresh fixture

If this fixture is ever invalidated (e.g. Antigravity's schema changes),
repeat the capture command above with `/opt/homebrew/bin/agy` (or
whatever `agy` resolves to once installed — see `runtimes/antigravity.md`),
locate the newest `.db` under `~/.gemini/antigravity-cli/conversations/`,
and update this README's cascade_id and observed values.
