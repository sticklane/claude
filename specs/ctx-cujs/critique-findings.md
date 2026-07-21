# Critique findings — NOT READY (2026-07-21, round 1; fixes applied same day, NOT re-verified)

No content hash recorded ON PURPOSE: the round-1 verdict was produced
against pre-fix bytes and the critic (agentic plugin) was unavailable
for a re-run — the next /critique must re-run, not skip.

Round-1 findings (all applied same day):
1. R4 acceptance broken: glob couldn't match ctxignore-git-overlay
   (which is SHIPPED — vcs/mod.rs overlay), and matched the three new
   specs pre-annotated. Fixed: three in-flight specs enumerated
   explicitly; ctxignore excluded with shipped citation.
2. R1 (8 headings) contradicted R2 (table section). Fixed: 9 headings,
   last is `## Gap table`.
3. R3 re-created the SKILL.md merge trap + had no acceptance. Fixed:
   registry SLOT 7 in token-doctrine's Landing order (now enumerating
   all seven editors); grep acceptance added.
4. `map --limit` doesn't exist (cli.rs: `--tokens`). Fixed in CUJ 1 +
   R3 now corrects the shipped skill table too.
5. Gap-table statuses gameable. Fixed: every status must cite code or
   spec path evidence.
