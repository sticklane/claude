---
name: scout
description: Cheap, read-only codebase reconnaissance discipline. Use when locating code, mapping a subsystem, or answering "where/how does X work" questions - especially before writing a spec or plan, or when another skill calls for a scout pass.
---

Answer ONE focused question about the code and produce a compact,
structured answer — without flooding the conversation with file contents.

Rules:
- Search first (grep/glob) to narrow down; read slices, not whole files.
- No code changes. This is reconnaissance only.
- Deliverable format, under 300 words:
  - Direct answer to the question first.
  - Key locations as `path:line` references.
  - Relevant signatures/shapes quoted minimally (a few lines, never dumps).
  - Gotchas the caller should know (feature flags, duplicated logic, tests).
- If the question is ambiguous or the answer isn't in the repo, say so
  explicitly rather than padding with guesses.

For large reconnaissance (several independent questions), don't do it all
in the working conversation: open a separate Agent Manager conversation on
a fast/cheap model, run the scout passes there, and carry back only the
summaries.
