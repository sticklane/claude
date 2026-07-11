# Runtime-agnostic headless relaunch commands

Status: open
Priority: P2
Breakdown-ready: true

## Problem

Three places build or parse the shell command that relaunches a headless
coding-agent session, and none of them consult `runtimes/*.md` — the exact
directory the toolkit's own convention says should be the single source for
per-runtime CLI shapes:

- `.claude/skills/drain/reference.md:855-861` hardcodes the baton relaunch
  grammar as a literal `nohup claude -p "..." --allowedTools ... &` template,
  even though a separate pointer earlier in the same file
  (`reference.md:704-705`) already says other runtimes should substitute
  their own `## Headless` template — the baton section just doesn't follow
  its own file's stated rule.
- `.claude/skills/workboard/workboard.py:557` parses relaunch commands out of
  `DRAIN-BATON.md` files with `BATON_CMD_RE = re.compile(r'claude\s+-p\s+"[^"]*"')`.
  When the match fails, `cm` is `None`, the baton's `command` field silently
  becomes `""` (workboard.py:583-588), and the dashboard's relaunch button
  disappears with no error (workboard.py:1569) — a `gemini -p`, `codex exec`,
  or Antigravity-flavored baton would all vanish this way today.
- `evals/run.sh:85` hardcodes `claude -p ...` as the default runner. It has a
  `RUNNER_CMD` escape hatch (lines 79-83) for overriding this per invocation;
  `drain/reference.md`'s baton relaunch has the same shape of escape hatch,
  `DRAIN_RELAUNCH_CMD` (verbatim override, `reference.md:870-875`). Both
  overrides are explicit, human-set opt-outs and stay untouched by this spec
  — the gap in both places is the *default* path, which doesn't derive from
  the repo's configured runtime at all.

`runtimes/claude-code.md` and `runtimes/gemini-cli.md` already each carry a
`## Headless` section whose fenced example is, in practice, a matchable and
generatable shape (`claude -p "<prompt>" \`, `gemini -p "<prompt>" \`) —
this convention already exists informally, just unenforced and unconsulted.
`runtimes/antigravity.md:44` states plainly that no scriptable relaunch
exists ("None exists" — Agent Manager only), a real, permanent case the
parser has to handle without trying to match a shell command that will never
exist.

The user's ask is explicit: adding a fourth or fifth coding-agent runtime
(Codex is already spec'd in `specs/codex-cli-port/SPEC.md`; Antigravity
mirroring is active) should be "as simple as a config change" — not an edit
to three separate hardcoded call sites.

## Solution

Formalize the existing informal convention rather than inventing a new field:
a runtime profile's `## Headless` section either (a) contains exactly one
fenced shell block whose first non-continuation line is the base invocation
shape using the literal token `<prompt>` for the prompt argument (e.g.
`claude -p "<prompt>" \`), or (b) contains no fenced block at all, signaling
"no scriptable relaunch — human-driven launch only" (Antigravity's case
today). Document this contract in `runtimes/README.md`. The contract covers
only the *foreground* invocation (binary, prompt, flags) — none of today's
`## Headless` sections include a backgrounding wrapper, and this spec doesn't
add one to the per-runtime contract. Detaching the process (`nohup … &`) is a
drain-level orchestration decision, not a per-runtime one: drain applies the
same fixed POSIX wrapper around whatever foreground invocation the resolved
runtime's template renders, for every runtime alike. This is what keeps R9
true — a new `runtimes/<name>.md` never needs to say anything about
backgrounding.

Add one shared parser, `runtimes/parse_headless.py`, that both real
consumers call instead of hand-rolling their own copy:
- Given a runtime name, it returns either the joined generation template
  (backslash-continuations collapsed to one command, placeholders left
  intact for the caller to substitute) or a `NONE` sentinel.
- It also derives a *match shape* for parsing: the first line's invocation
  prefix up to and including `<prompt>`, turned into a regex by collapsing
  each run of literal whitespace to `\s+` (preserving today's `BATON_CMD_RE`
  tolerance for `claude  -p` / tab variants) and escaping everything else
  literally, then replacing `<prompt>` with `"[^"]*"`.
- An unresolvable runtime name — no `runtimes/<name>.md` file, or a
  `.claude/runtime.md` naming one that doesn't exist — is not an error: the
  parser returns the same result as `claude-code` and logs a warning,
  mirroring `reference.md:707-708`'s existing "absent in plugin installs and
  eval fixtures, where the claude-code defaults apply" rule. Nothing in this
  spec's design may crash a workboard scan or a drain baton pass over a bad
  or missing runtime name.

**Where `workboard.py` loads profiles from.** `workboard.py` scans many
repos across the machine (per its own description), and most of them have no
`runtimes/` directory at all — only the toolkit checkout does. Each scanned
repo's `.claude/runtime.md` (when present) only *names* a profile; it never
hosts a copy of the profile's content. `workboard.py` always loads
`runtimes/*.md` from the toolkit installation it ships from (the same
directory `parse_headless.py` lives in), regardless of which repo's
`DRAIN-BATON.md` is being parsed, and falls back to `claude-code` per the
resolution rule above when a scanned repo has no `.claude/runtime.md`.

Three consumers change to use it:

1. **`drain/reference.md` baton grammar (~line 855)** stops embedding a
   literal `claude -p` example. It instructs the generating worker to
   resolve the repo's active runtime (`.claude/runtime.md`, default
   `claude-code`, per `runtimes/README.md`'s existing selection rule), fetch
   that runtime's template via `runtimes/parse_headless.py`, substitute the
   real `/drain <spec> (generation G+1, baton: ...)` prompt plus the
   project's allowlist/turn-cap, and wrap the result in drain's own fixed
   POSIX backgrounding wrapper (`nohup … &`, unchanged from today, and not
   sourced from the runtime profile — see Solution's contract paragraph
   above). When the parser returns `NONE` (Antigravity today), the grammar
   renders a
   plain-language instruction instead of a shell command: "No scriptable
   relaunch for `<runtime>` — reopen generation G+1 from `<runtime>`'s Agent
   Manager, pointed at `DRAIN-BATON.md`." This also reconciles the
   already-existing pointer at `reference.md:704-705`, which said the right
   thing but wasn't actually followed by the baton section.

2. **`workboard.py`** replaces the single hardcoded `BATON_CMD_RE` with a
   per-runtime regex table built from every `runtimes/*.md` profile via the
   shared parser. When scanning a repo's `DRAIN-BATON.md`, it resolves that
   repo's active runtime the same way drain does, tries that runtime's regex
   first, then falls back through the other known runtimes' regexes (covers
   a baton written before/after a runtime switch). If the resolved runtime
   has no fenced template, it skips regex matching and sets a
   `manual_relaunch` field instead of leaving `command` silently blank; the
   HTML rendering (~line 1569) shows that phrase rather than omitting the
   relaunch block. If nothing matches at all (a genuinely unrecognized
   shape), `command` stays `""` but a new `parse_warning` field gets set so
   the needs-attention inbox can surface it — strictly better than today's
   silent disappearance.

3. **`evals/run.sh`** keeps its `RUNNER_CMD` override as the explicit
   one-off escape hatch, but its *default* (when `RUNNER_CMD` is unset) is
   derived from the repo's active runtime profile via the shared parser,
   falling back to today's hardcoded `claude -p` line only when no
   `.claude/runtime.md` exists or it names `claude-code` — preserving "the
   inline Claude default" per CLAUDE.md's own convention while making the
   default correct for a repo configured onto another runtime.

Net effect: adding runtime N+1 means writing `runtimes/<name>.md` with a
conforming `## Headless` section (or an explicit no-fence no-scriptable-relaunch
case) and, if it should be a repo's default, a one-line `.claude/runtime.md`
edit — no changes to `drain/reference.md`, `workboard.py`, or `evals/run.sh`.

## Requirements

R1. `runtimes/README.md` documents the `## Headless` section contract:
    single fenced block with `<prompt>` as the placeholder token, or no
    fenced block meaning no scriptable relaunch exists.

R2. `runtimes/parse_headless.py` exists, is unit-tested, and for a given
    runtime name returns either the joined command template (placeholders
    intact) or a `NONE` sentinel; it also exposes the derived match-shape
    regex for that runtime.

R3. `workboard.py`'s baton parsing uses the shared per-runtime regex table
    instead of the hardcoded `BATON_CMD_RE`; a baton containing a
    `gemini -p`-shaped (or other non-Claude) relaunch command is correctly
    extracted.

R4. `workboard.py` renders "no scriptable relaunch — reopen from
    `<runtime>`'s Agent Manager" (not a blank command block) when the
    resolved runtime has no fenced Headless template.

R5. `workboard.py` sets a `parse_warning` field (surfaced by the
    needs-attention inbox) for a baton whose relaunch command matches no
    known runtime shape, instead of silently rendering it blank.

R6. `drain/reference.md`'s baton-relaunch grammar (~line 855) no longer
    hardcodes `claude -p ...`; it instructs resolving the active runtime and
    calling `runtimes/parse_headless.py` to substitute that profile's
    Headless template — the literal path `runtimes/parse_headless.py` must
    appear in this section, both as an unambiguous implementation marker and
    because it's the actual invocation a human/worker following the grammar
    would run — and the section is reconciled with the existing pointer at
    `reference.md:704-705` so the two sections agree.

R7. `drain/reference.md`'s baton grammar documents the no-scriptable-relaunch
    case (render a manual-relaunch instruction, no shell command) for
    runtimes like Antigravity.

R8. `evals/run.sh`'s default runner command (when `RUNNER_CMD` is unset) is
    derived from the repo's active runtime profile, falling back to today's
    hardcoded `claude -p` line only for `claude-code` or an absent
    `.claude/runtime.md`.

R9. Adding a new runtime requires only a new `runtimes/<name>.md` file
    satisfying the Headless contract (plus, optionally, a one-line
    `.claude/runtime.md` change to make it a repo's default) — no edits to
    `workboard.py`, `drain/reference.md`, or `evals/run.sh`.

R10. `workboard.py` always resolves `runtimes/*.md` profiles from the
    toolkit installation it ships from, never from a scanned target repo's
    own tree (most scanned repos have no `runtimes/` directory); a scanned
    repo's `.claude/runtime.md` only selects a profile *name*.

R11. An unresolvable runtime name (missing `.claude/runtime.md`, or one
    naming a profile with no matching `runtimes/<name>.md`) falls back to
    `claude-code` with a logged warning, in both `workboard.py`'s parsing and
    `drain/reference.md`'s generation — never a crash or an unhandled
    exception.

## Out of scope

- Building out a full, production `runtimes/codex.md` profile — that is
  `specs/codex-cli-port/SPEC.md`'s job; this spec only makes the tooling
  runtime-agnostic, it doesn't add a runtime.
- Giving Antigravity a scriptable headless mode — out of scope by design;
  this spec makes the tooling degrade gracefully around that permanent gap,
  not close it.
- Changing drain's live orchestration/dispatch logic beyond the
  baton-relaunch-grammar section.
- Changing `evals/` scenario files (`setup.sh`, `assert.sh`, `prompt.txt`,
  `allowed-tools.txt`) themselves — only `evals/run.sh`'s default runner
  selection changes.
- A GUI or interactive picker for choosing a runtime — `.claude/runtime.md`
  remains the existing, already-documented selection mechanism.

## Acceptance criteria

- [ ] `python3 -m unittest discover -s .claude/skills/workboard` passes,
      including new tests covering: parsing a `gemini-cli`-shaped baton
      command, parsing an Antigravity (no-scriptable-relaunch) baton, an
      unrecognized-shape baton producing a `parse_warning`, and a baton whose
      repo names an unresolvable runtime falling back to `claude-code`
      without raising (R3, R4, R5, R11).
- [ ] `python3 runtimes/parse_headless.py claude-code` exits 0 and writes the
      joined claude-code template (placeholders intact) to stdout; `python3
      runtimes/parse_headless.py antigravity` exits 0 and writes exactly
      `NONE` to stdout (R2).
- [ ] `sed -n '/## Baton pass/,/## Critique intake/p' .claude/skills/drain/reference.md
      | grep -c 'nohup claude -p "\/drain'` returns `0` (the old hardcoded
      literal invocation is gone from the baton section), and the same
      slice piped to `grep -c 'runtimes/parse_headless.py'` returns `1` or
      more — this path does not exist in `reference.md` before this spec is
      implemented, so the check cannot pass as a no-op (R6, R7).
- [ ] `bash evals/run.sh` still passes its existing scenarios unmodified
      when no `.claude/runtime.md` is present (regression check on R8's
      fallback path).
- [ ] End-to-end: add `runtimes/fake-runtime.md` to *this* (toolkit) checkout
      satisfying the Headless contract with a distinct invocation shape
      (e.g. `fakecli run "<prompt>"`) — per R10, this is the only place
      `workboard.py` ever reads profiles from. Point a scratch target repo's
      `.claude/runtime.md` at `fake-runtime`, hand-author a `DRAIN-BATON.md`
      in that scratch repo whose relaunch command matches the new shape, and
      confirm `workboard.py` extracts it correctly with zero code changes to
      `workboard.py`, `drain/reference.md`, or `evals/run.sh` — demonstrates
      R9 directly.

## Open questions

(none)

## Parallelization

Task 01 (`runtimes/parse_headless.py` + `runtimes/README.md` contract doc)
is the shared foundation every other task imports — it fixes the parser's
interface (joined-template-or-`NONE`, plus the derived match-shape regex)
before any consumer is touched, so it must land first and solo.

Tasks 02 (`workboard.py`), 03 (`drain/reference.md`), and 04
(`evals/run.sh`) each depend only on task 01's interface, touch disjoint
files, and share no undecided design once task 01 has fixed the parser
contract — they pass the decision-coupling test and can run concurrently.
Neither 02 nor 03 touches the antigravity mirror or `.claude-plugin/plugin.json`
directly: both are `.claude/skills/` changes (CLAUDE.md's mirror-and-bump
convention applies to both), and bumping the version inside either task
would race the other's concurrent skills change. Task 05 is the single
closing task that depends on both 02 and 03, copies task 02's finished
`workboard.py`/`test_workboard.py` to their antigravity mirror, and bumps
`plugin.json` once — after the whole generation of skills changes has
landed, per CLAUDE.md's "typically one closing task" convention.

- Group: 02, 03, 04
