# Task 01: Shared `runtimes/parse_headless.py` parser + Headless contract doc

Status: done
Depends on: none
Priority: P0
Budget: 35 turns
Spec: ../SPEC.md (requirements R1, R2, R11)
Touch: runtimes/parse_headless.py, runtimes/test_parse_headless.py, runtimes/README.md

## Goal

A new `runtimes/parse_headless.py` module exists, is unit-tested, and is the
single place that (a) reads a runtime name, resolves `runtimes/<name>.md`'s
`## Headless` section, and returns either the joined command template
(backslash-continuations collapsed, placeholders like `<prompt>` left
intact) or the literal string `NONE` when the section has no fenced block;
and (b) derives a match-shape regex from that template for parsing existing
relaunch commands back out of text. `runtimes/README.md` documents the
`## Headless` section contract so a future `runtimes/<name>.md` author knows
the rule without reading this module's source. This task is purely additive
— no other file changes yet; tasks 02-04 depend on this module's interface.

## Touch

New files only, plus a doc addition to `runtimes/README.md` (which today has
no `## Headless` section — see SPEC.md's Solution section). Do not touch
`.claude/skills/workboard/workboard.py`, `.claude/skills/drain/reference.md`,
or `evals/run.sh` — those are tasks 02-04.

## Steps

1. Write `runtimes/test_parse_headless.py` first (red): cases for
   `claude-code` (returns the joined template from
   `runtimes/claude-code.md`'s `## Headless` fenced block, lines ~50-62,
   `claude -p "<prompt>" \` continuation lines collapsed to one string,
   placeholders intact), `gemini-cli` (lines ~41-49 of
   `runtimes/gemini-cli.md`, `gemini -p "<prompt>" \`), `antigravity`
   (returns `NONE` — `runtimes/antigravity.md:42-47` states "None exists",
   no fenced block), an unresolvable runtime name (no matching
   `runtimes/<name>.md` — returns the same result as `claude-code` and logs
   a warning; assert on the warning via `caplog`/captured stderr, not by
   parsing prose), and the derived match-shape regex for `claude-code`
   matching `claude -p "..."` and `claude  -p "..."` (tab/extra-whitespace
   tolerant, preserving today's `BATON_CMD_RE` tolerance) but not matching
   an unrelated string.
2. Run the tests, confirm they fail (module doesn't exist yet).
3. Implement `runtimes/parse_headless.py`:
   - A function to locate and read a runtime's `## Headless` section from
     `runtimes/<name>.md` (resolve relative to this module's own directory,
     per SPEC.md's "Where workboard.py loads profiles from" — this matters
     for task 02, which imports this module rather than reimplementing path
     resolution).
   - Parse out the first fenced shell block (if any); join
     backslash-continuation lines into one line, preserving all tokens
     including `<prompt>`.
   - No fenced block at all → return the sentinel string `NONE`.
   - Unresolvable name (file missing) → resolve as if `claude-code` were
     requested, and log a warning (Python `logging`, module-level logger) —
     never raise.
   - A second function: given the joined template (or `NONE`), derive the
     match-shape regex — take the first line's invocation prefix up to and
     including `<prompt>`, collapse each run of literal whitespace to
     `\s+`, escape everything else literally (`re.escape` per literal
     chunk), replace `<prompt>` with `"[^"]*"`. When the template is
     `NONE`, this function returns `None` (no regex to match against).
   - A CLI entry point (`if __name__ == "__main__":`) taking a runtime name
     as `sys.argv[1]`, printing the joined template or `NONE` to stdout,
     exiting 0.
4. Run the tests again, confirm green.
5. Add a section to `runtimes/README.md` documenting the `## Headless`
   contract: exactly one fenced shell block whose first non-continuation
   line is the base invocation using literal `<prompt>` as the placeholder,
   OR no fenced block at all — signaling no scriptable relaunch exists. Use
   that exact phrase, "no fenced block", verbatim in the new section (grep
   confirms it does not appear anywhere in `runtimes/README.md` today —
   this is what makes the acceptance check below a real assertion that the
   contract got documented, not a pre-existing string that already
   matched). Reference `runtimes/parse_headless.py` as the tool that
   enforces/derives this mechanically, so nothing hand-rolls the parsing
   again.

## Acceptance

- [x] `python3 -m unittest discover -s runtimes` → all tests pass
- [x] `python3 runtimes/parse_headless.py claude-code` → exit 0, stdout is
      the joined claude-code Headless template with `<prompt>` intact
- [x] `python3 runtimes/parse_headless.py antigravity` → exit 0, stdout is
      exactly `NONE`
- [x] `python3 runtimes/parse_headless.py totally-not-a-real-runtime` →
      exit 0, stdout matches the claude-code template, a warning is logged
      to stderr
- [x] `grep -q 'no fenced block' runtimes/README.md` → found (contract
      documented)
