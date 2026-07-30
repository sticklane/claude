# The acceptance-block grammar

When: writing a SPEC.md `## Acceptance criteria` block, critiquing one, or
building a consumer that runs one (`bin/spec-gate`).

A block is machine-runnable only if every criterion line follows one shape, so
a parser can recover the criterion's identity, who may run it, and what command
to run. This file owns that syntax. How *deep* a criterion should reach — the
L0–L3 ladder and the vacuous/trivially-satisfiable traps — is
[anchored-acceptance-criteria.md](anchored-acceptance-criteria.md)'s, and is
not restated here. The executable definition of the acceptance-block grammar is
`tests/test_acceptance_block_grammar.sh`'s reference parser; this file is its
prose.

## The line

```
- [ ] A<k> (<cheap|expensive>): `<command>` — <expected>
```

- `- [ ]` — an unchecked markdown task box. `- [x]` parses too; the checkbox
  is human bookkeeping and carries no machine meaning.
- `A<k>` — the criterion id: a literal `A` followed by one or more digits.
- `(<tier>)` — exactly `cheap` or `expensive`. No other word parses.
- `` `<command>` `` — the command to run, in backticks, non-empty, with no
  backtick inside it.
- ` — ` — a literal space, em dash, space.
- `<expected>` — non-empty prose stating what the command must produce.
  Requirement ids (`(R2)`, `(EP11)`) belong here.

Continuation lines that do not start with `- ` are ignored, so a criterion's
annotation may wrap. Ids must be unique within a block.

## Id stability

Ids are permanent handles, not positions. A consumer keys a stored result to
an id (`bin/spec-gate` writes `{id, tier, pass|fail|skip, ts}` into
`specs/<slug>/acceptance-status.json`), so renumbering silently rewrites
history.

- Never renumber a published id. Adding a criterion takes the next unused
  `k`, never a gap-filling one, and never a shuffle of the ones below it.
- A removed criterion's id is retired, not reused. `A4` deleted means `A4`
  never appears in that spec again.
- Ids are scoped to their spec. `A1` in two specs are unrelated.
- Reordering lines is free; ids travel with their criterion.

## What the tiers encode

The tiers name **who may run a criterion**, not how long it takes.

- **`cheap`** — anything an unattended worker may execute under the command
  policy: argv-0 resolves to a regular executable under an allowlisted root,
  it runs directly and never through a shell, its arguments survive POSIX
  shell-word lexing with no ASCII control characters, cwd is the repo root,
  bounded timeout, no network grant. Drain runs the cheap tier every pass.
- **`expensive`** — a paid or gated run: an eval scenario, a human-driven
  browser walk, anything metered. **Only a human launches it, and a human
  records its result** in `specs/<slug>/acceptance-status.json`. No
  unattended loop may execute an `expensive` criterion, and no agent may
  write its result.

Both tiers obey one further rule: **every criterion is read-only or
idempotent.** A gate runs the block against the live repository on a schedule
and commits the result, so a criterion that mutates state pollutes every
later pass. A criterion needing state builds it in a fixture — under
`mktemp -d` or `tests/fixtures/` — never in the live tracker or the working
tree. The gate does not sandbox a criterion that ignores this; enforcement is
`/critique`'s READY bar, at authoring time.

## Worked example

- [ ] A1 (cheap): `bash tests/test_acceptance_block_grammar.sh` — exits 0 and reports 0 failures (EP11)
- [ ] A2 (cheap): `bin/spec-gate drain-economy --tier cheap` — exit 0 with every cheap criterion `pass` (EP12)
- [ ] A3 (expensive): `evals/run.sh critique` — the NOT-READY fixture is refused; a human records the verdict (EP16)

## Backfill is lazy

Nothing sweeps existing specs into this grammar. A block written before it
stays as it is until someone drains that spec.

When a focus drain hits a spec whose block does not parse, it files **one**
blocking child, titled `conform acceptance block to grammar`, and moves on.
It never guesses what a non-conforming criterion meant, never rewrites the
line, and never drops it — a wrong id or a wrong tier is worse than an
unparsed block, because the first is silently trusted and the second is
loudly skipped.
