# Task 12: ctx hooks install/uninstall

Status: done
Depends on: 05, 10
Priority: P2
Budget: 40 turns
Spec: ../SPEC.md (requirement R16; contract C5)
Touch: context-tree/src/cmd/hooks.rs, context-tree/src/hooks_templates/**, context-tree/src/cli.rs, context-tree/Cargo.toml, context-tree/tests/fixtures/hooks/**, context-tree/tests/*.rs

## Goal

`ctx hooks install` installs opt-in hooks: git's post-checkout/post-merge/
post-commit pre-warm hooks (each running `ctx sync` in the background,
journaled per C5 with `trigger: hook`) and a printed snippet for a harness
PostToolUse hook that runs `ctx sync` plus `ctx notes list --file
<edited-file>`, emitting any output as hook additional context — plus a
pre-commit hook that writes pending anchor updates (task 10's
`--write-anchors` logic) and stages the touched note files, applying
task 10's partial-commit rule: a given update is written only when the
re-anchored NEW path's file is itself in the staged set. Hook files are
managed as delimited marked blocks: install appends a marked `ctx` block
to an existing hook file (creating an executable file only if absent),
preserving all existing content; `ctx hooks uninstall` removes exactly
that block and deletes only files `ctx` itself created. Under git, install
also enables `core.fsmonitor` when the git version supports the builtin
monitor, reporting enabled/skipped in its output; uninstall reverts only
settings it set.

## Touch

Only `cmd/hooks.rs`, the hook-template snippets, and CLI wiring for `ctx
hooks install`/`uninstall`. This task may call task 10's
`--write-anchors` logic from the pre-commit hook template but must not
modify `src/notes/reanchor.rs` itself.

## Steps

1. RED/GREEN: in a throwaway git fixture whose `post-checkout` hook
   already contains non-ctx content, `ctx hooks install` preserves that
   content and appends the marked `ctx` block.
2. RED/GREEN: after install, a checkout in that fixture produces a
   `trigger: hook` record in the sync journal (C5) within a bounded poll
   (assert within 10s).
3. RED/GREEN: install's output reports the fsmonitor decision (enabled,
   or skipped with a stated reason) when git supports `core.fsmonitor`'s
   builtin monitor.
4. RED/GREEN: the printed PostToolUse snippet's text invokes `ctx notes
list --file` (assert the printed snippet contains that invocation).
5. RED/GREEN: pre-commit partial-commit rule — a fixture where a refactor
   moves a symbol from file A to file B; stage only file A (the moved-FROM
   file), not file B; commit; assert the anchor update for that symbol is
   left pending (not staged/written), because file B is not itself in the
   staged set.
6. RED/GREEN: pre-commit full-commit case — stage both A and B; commit;
   assert the note-file anchor-path update appears staged in the same
   commit (ties to task 10's leg-(c)/(a)/(d) scenarios where applicable).
7. RED/GREEN: `ctx hooks uninstall` restores the original hook bytes
   exactly (byte-for-byte, proving only the marked block was removed) and
   reverts only settings (`core.fsmonitor`) it itself set — a
   pre-existing fsmonitor setting from before install is left untouched.

<!-- PLAN (worker, task/12-hooks)
Design:
- cli.rs: add `Hooks(HooksArgs)` (Install/Uninstall + hidden PreCommit used by the
  installed pre-commit hook) and a hidden `--hook` flag on `Sync` (→ Trigger::Hook).
- lib.rs/cmd/mod.rs (wiring, off-Touch, reversible): dispatch to cmd::hooks::run.
- src/cmd/hooks.rs: install/uninstall/pre-commit. Marked-block manager (BEGIN/END
  markers). Appended block byte-exact-removable; ctx-created files carry an in-block
  sentinel and are deleted on uninstall. fsmonitor via git version parse (>=2.37),
  only set when unset, tracked by `ctx.hooksFsmonitorSet` config marker so uninstall
  reverts only self-set. Pre-warm hooks run `<ctxbin> sync --hook &`; pre-commit runs
  `<ctxbin> hooks pre-commit`. PostToolUse snippet printed (contains `ctx notes list
  --file`). Hooks dir via `git rev-parse --git-path hooks`; ctxbin via current_exe().
- pre-commit logic: run_sync(Hook) → read pending_reanchors (note_id→new qpath) →
  all_symbols map qpath→file → staged set via `git diff --cached --name-only` → write
  + `git add` only notes whose new qpath's file is staged; leave rest pending
  (replace_pending_reanchors with remainder). Reuses notes::rewrite_anchor_path;
  does NOT modify reanchor.rs or sync::write_anchors.
- Templates under src/hooks_templates/**, include_str! with __CTX_BIN__ placeholder.
- Tests: tests/hooks.rs (7 named tests matching acceptance).
-->

## Acceptance

- [x] `cd context-tree && cargo test hooks_install_preserves_existing` →
      passes (non-ctx content preserved, marked block appended)
      — evidence: `cargo test hooks_ --test hooks` → hooks_install_preserves_existing ok
- [x] `cd context-tree && cargo test hooks_checkout_triggers_sync` →
      passes (journal `trigger: hook` record within 10s of a checkout)
      — evidence: hooks_checkout_triggers_sync ok
- [x] `cd context-tree && cargo test hooks_fsmonitor_reporting` → passes
      (enabled/skipped reason reported)
      — evidence: hooks_fsmonitor_reporting ok
- [x] `cd context-tree && cargo test hooks_posttooluse_snippet` → passes
      (printed snippet invokes `ctx notes list --file`)
      — evidence: hooks_posttooluse_snippet ok
- [x] `cd context-tree && cargo test hooks_precommit_partial_commit` →
      passes (moved-TO file unstaged -> anchor update left pending, not
      staged) — evidence: hooks_precommit_partial_commit ok
- [x] `cd context-tree && cargo test hooks_precommit_full_commit` →
      passes (both files staged -> anchor update staged in the same
      commit) — evidence: hooks_precommit_full_commit ok
- [x] `cd context-tree && cargo test hooks_uninstall_restores_original` →
      passes (byte-exact restoration; only self-set settings reverted)
      — evidence: hooks_uninstall_restores_original ok
- [x] `bash context-tree/scripts/check.sh` → exits 0
      — evidence: full suite green, EXIT=0
