# Preflight worktree and ownership record

This is the durable transcription of the implementation session's pre-edit
inventory. The verifier requested a file citation after the observations had
initially remained only in session context.

- Base revision:
  `aea89bd0f93660bca0cb9915a14c7f6df4ef6dc8`
- Primary working tree: `/Users/sjaconette/claude`
- Active workers at the destructive-sweep boundary:
  - `/root` — sole implementation owner
  - `/root/cbm_capability_gap` — read-only capability research
  - `/root/cbm_cutover_critic` — read-only spec critique
  - `/root/cbm_upstream_safety` — read-only upstream research
- None of the three supporting workers owned or edited a retirement or
  retained-routing path.

The pre-edit status showed every retained path later enumerated in
`config/codebase-memory-routing-paths.txt` as dirty. Those files carried the
in-progress runtime-portability work already present in the shared worktree.
Their diffs were read before the CBM clauses were merged; unrelated hunks were
preserved. No retained file was replaced from `HEAD` or from a clean checkout.

Two paths in the retirement set were already dirty:

- `.claude/skills/ctx/SKILL.md`
- `context-tree/tests/doc_conformance.rs`

Both diffs were read before deletion. They were wholly inside the retired ctx
product surface. The maintainer's current directive—immediate conversion, no
staged or temporary compatibility path, and no current-tree ctx history—
explicitly superseded that content. The active-worker inventory showed no
foreign owner for either path, so deletion used that ownership basis rather
than assuming a clean worktree.

All other retirement targets were clean relative to the base when reviewed.
Tracked targets were deleted only after the exact manifest was established;
ignored `.context` cache and `context-tree/target` artifacts were removed
under those exact roots. Unrelated dirty paths elsewhere in the worktree were
left in place.
