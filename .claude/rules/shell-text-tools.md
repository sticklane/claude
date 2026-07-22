# Shell text tools vs dedicated tools

Dedicated Read/Edit/Glob/Grep tools carry safety shell text tools lack —
Edit's uniqueness validation, its read-before-write requirement, and
reviewable diffs vs `sed -i`'s silent regex corruption (the drift
anthropics/claude-code issue #21697 tracks). This rule states when each
applies.

## (a) Writes go through Edit/Write, never in-place shell writes

Never `sed -i`, in-place `awk`, or `cat >`/`>>` onto a tracked source or
docs file — always Edit or Write. Two documented exceptions, cited not
re-litigated per file:

- **Formatter-reflow `.md` heredoc case**: when a PostToolUse formatter
  reflows Edit/Write output on a fenced-code `.md` file, editing Bash-side
  (a heredoc `cat >`) is the documented workaround, per-repo (fooszone's
  `CLAUDE.md` precedent). Don't generalize it beyond that documented case.
- **Generated/derived files**: fixture or output files a build step
  regenerates (e.g. eval-sandbox fixtures) aren't hand-edited source, so
  in-place shell writes there aren't a violation.

## (b) Reads of a file you're about to edit use Read

If you will Edit or Write a file, Read it first — never `sed -n`/`head`/
`cat` a file you're about to modify. Read gives you the exact current
content Edit's uniqueness check needs.

## (c) Shell text tools: read-only extraction, bounded output

`grep`/`sed`/`awk`/`cat` are for read-only extraction outside Read/Grep's
reach (log slicing, pipelines, acceptance-command checks) — never
unbounded. Every example caps its output: `head -n`, `grep -l`/`-m`/`-c`,
`sed -n` line ranges, or `awk` anchored ranges (`/^func /,/^}/`). No
cat-the-whole-file, no unbounded `grep -rn`.

## (d) Acceptance-command authoring: anchor to structure

Anchor greps to structure, not file-wide literals: function/section
ranges, line-starts (`grep -c '^## '`), or frontmatter extraction
(`sed -n 's/^description: *//p'`). A file-wide literal can collide with an
unrelated doc comment (the fooszone go-cmd-shared-helpers R3 collision,
fixed with a function-anchored `awk` range) — anchor first, don't ban
shell tools over it.

## (e) Cross-references

- The gate skill's Stop hook covers Edit/Write only; pair it with
  `Bash(sed -i *)` permission `deny` rules when write protection must be
  hard (gate/reference.md).
- Delegate exploratory reads to the `scout` agent rather than reading
  files into main context to look around (token-discipline.md's
  delegation default).
