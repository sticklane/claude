# Bootstrap authority worker and reviewer workflow

This workflow is executable only when launched by the source-attested
`bootstrap-registration.py` controller. It handles one of Bootstrap Tasks
00A--00D in an isolated Git worktree. It never creates, claims, closes, or
edits a Bead; installs a provider schema; publishes a commit; or changes
bootstrap evidence.

Read the canonical JSON file named by `AGENTIC_BOOTSTRAP_ENVELOPE`. Reject it
unless its closed schema is `agentic.registration-bootstrap-launch/v1`, its
intent/run/issue/task/role values agree with the pointer prompt and
environment, its task realpath is a contained regular file in the named
worktree, and the task bytes, definition hash, base commit, configuration hash,
attestation commit, actor, and result path agree exactly. Reject controls,
symlinks, unknown fields, a dirty worktree, or any existing result file. The
result path and all temporary provider artifacts must remain below the
envelope's controller-owned bootstrap state root; they are not Git artifacts.

For `role:"worker"`:

1. Re-read the task and implement only its `Touch:` boundary. 00A owns the
   authority-core patch/helper/tests; 00B owns conditional authority; 00C owns
   supersession; 00D owns the toolkit adapter. Do not borrow later authority.
2. Use normal test-first build discipline. Run the task's focused acceptance
   while developing, but do not edit its immutable task definition.
3. Commit the complete task change once. Require the worktree to be otherwise
   clean and the commit to descend from the envelope base.
4. For 00A--00C, use the task-owned deterministic helper to write the exact
   executable provider into the controller-owned `outputs/<bootstrap-id>/`
   directory, outside Git. The executable must correspond to the just-created
   commit and contain exactly fragments A, A+B, or A+B+C respectively. Do not
   commit, install, or execute that artifact. 00D returns no new provider.
5. Atomically write canonical JSON with no trailing LF and mode 0600 to the
   exact result path. Use schema `agentic.registration-bootstrap-worker-result/v1` and
   exactly: `schema_version`, `ok:true`, `intent`, `run_id`, `bootstrap_id`,
   `issue`, `base_commit`, `commit`, and `provider`. For 00A--00C, `provider`
   is an object with absolute `path`, lowercase SHA-256 `sha256`, and
   `source_commit` equal to `commit`; for 00D it is `null`.

For `role:"review"`:

1. Do not edit. Require the worker commit to remain worktree HEAD and require
   tracked, untracked, ignored, and recursive submodule state to be clean.
2. Review the complete base-to-HEAD diff against the selected immutable task,
   its Touch boundary, and the provider-profile sequencing above. Confirm the
   focused acceptance result independently from source and diff evidence.
3. Atomically write canonical JSON with no trailing LF and mode 0600 to the
   exact result path. Use schema `agentic.registration-bootstrap-review-result/v1` and
   exactly: `schema_version`, `ok:true`, `verdict:"READY"`, `intent`, `run_id`,
   `bootstrap_id`, `issue`, `base_commit`, `commit`, `reviewer`, and
   `diff_sha256`. Any finding returns `ok:false` and a non-READY verdict.

The parent revalidates both results, re-runs every acceptance command, checks
that review did not move or dirty the worktree, fast-forwards the unchanged
serialized target, copies the provider into content-addressed bootstrap state,
and performs provider-backed tracker transitions. A worker or reviewer must
not attempt those parent operations.

The provider response contract is future behavior owned only by 00A--00C.
Every `identity`, `install`, `bootstrap-finalize`, `guarded-create`, and
conditional-transaction response must use the exact closed response schema in
`bootstrap-registration-v1.json`. Install and mutation responses carry the
exact request digest, actor, reason/profile, before/after schema or issue
revision, and history cursor in a durable receipt. `authority identity`
re-exposes those receipts verbatim for ambiguous recovery and committed-stage
re-observation. Unknown fields, self-reported success without the receipt,
foreign history, or a receipt that disappears after a later profile install
is a provider failure; the controller never infers or fabricates it.
