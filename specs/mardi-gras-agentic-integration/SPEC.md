# Live Beads and Agent Control Surface

Priority: P0
Rigor: production
Breakdown-ready: true

## Problem

Developers using this toolkit have separate surfaces for Beads, workflow skills, drain progress, runtime sessions, and recovery. The existing browser Workboard combines a machine-wide inventory with execution controls, but it has not been dependable as the repository work surface. Mardi Gras already supplies a terminal-native Beads list, live refresh, filtering, dependency/detail views, comments, and agent affordances, but its direct launch path bypasses this toolkit's `/work`, `/build`, and `/drain` procedures and sees only agents it launched itself.

The replacement must provide a stable, no-scrollback terminal view and convenient launch controls without creating another scheduler, claim database, or recovery engine.

## Decision

Contribute a first-class `agentic` provider to Mardi Gras and extend five existing toolkit seams:

- `agentic live [--check]` validates the local installation and starts Mardi Gras in its alternate-screen UI with the provider enabled. It resolves Mardi Gras explicitly and rejects macOS `/usr/bin/mg`.
- `agentic launch --prepare` validates a user-selected target and produces an immutable dispatch record plus an absolute `agentic supervise --dispatch-id <id>` argv. `agentic supervise` runs in the PTY or tmux pane created by Mardi Gras, invokes a native runtime with a pointer to the real toolkit skill, forwards signals, waits for the child, and records process lifecycle.
- The existing positional claim boundary becomes `agentic claim <options> -- <id>` with strict ready/open preconditions, canonical cross-worktree locking, fresh actual-repository capability authorization and post-mutation Beads verification, JSON outcomes, and idempotent session-claim bookkeeping for installed top-level `/work`, `/build`, and `/drain` skills. The first release accepts only probed permanent-claim, conditional-mutation, and supersession-redirect Beads profiles and creates no persistent lease or second owner record; a future lease-backed Beads profile fails compatibility until the toolkit also owns its heartbeat contract.
- The existing `agentic event` substrate gains a version-2 record with optional, validated `dispatch_id`, `process_pid`, and `process_start` correlation fields. New readers merge and normalize the legacy version-1 log and the version-2 partition; old strict readers continue to see only their version-1 path. A UI-started skill copies the supervisor-provided correlation environment into its post-claim event; direct skills omit it. No independent trace system or ownership store is introduced, and events never authorize work.
- `agentic activity` emits bounded, read-only JSON joining Beads, launch records, run/child-agent events, `.beads/session-claims`, `.beads/session-inflight`, registered worktrees, and runtime liveness. Its repository toolkit-agent projection replaces duplicate drain-progress plumbing but deliberately complements, rather than retires, `fleet`'s session-wide native inventory.

The initial upstream patch set is developed and tested against Beads v1.1.0
commit `8e4e59d` and Mardi Gras commit `70e36ff`; production support begins
only when trusted upstream releases advertise the corresponding protocols.

Beads remains the only durable work-ownership boundary. Launch does not claim or reserve an issue. `/work`, a top-level `/build`, and `/drain` use the strengthened claim command when it is installed; its canonical-repository lock exists only long enough to authorize the actual repository and serialize the fresh ready check and claim across participating toolkit sessions, replacing the current per-worktree lock/sync behavior for this operation. Each attempt has a UUIDv7 run ID and claims with the session-unique Beads actor `agentic:<workflow>:<run-id>`, so a raw or toolkit claim that wins between read and update causes the other actor's claim to fail instead of succeeding idempotently under the same human identity. The run ID becomes canonical only after claim succeeds; the Bead owner retains the human identity while the assignee identifies the active run. A direct skill and a UI-started skill may race; one claims, while every loser stops before reading untrusted task prose into a worker prompt or editing files. Drain rechecks each claim result and skips a loser. A crash after Beads changes but before marker/event output leaves an ordinary in-progress Bead assigned to the exact run for the existing orphan/recovery procedure; every toolkit-owned requeue path first applies its existing dead-session and worktree-safety checks, then uses the certified revision-conditional update to reopen and clear the assignee before removing marker lines. Observation never guesses, overwrites a newer actor, or rolls ownership back. This costs an occasional short-lived runtime but avoids a second durable ownership store.

The skills remain the workflow engine. They own untrusted-data screening, claims, worktrees, orchestration, verification, closure, discoveries, and orphan recovery. Mardi Gras owns browsing, drill-down, explicit intent, confirmation, presentation, and PTY/tmux topology. Activity and trace data are advisory observation only.

## Developer experience

1. Install the `agentic` plugin, its self-contained CLI package, and trusted Beads and Mardi Gras releases advertising the R17 capability profiles and `agentic.control/v1`. Once per repository/database, an administrator explicitly runs `agentic bd-authority install --repo <physical-repo> --confirmed`; this is the only production schema-install path and is never implied by live preflight. `agentic live --check` then reports the repository, `bd`, authority schema, Mardi Gras, runtime adapter, immutable skill package, plugin compatibility, tmux support, and protocol compatibility without changing state.
2. Run `agentic live` from any Beads repository. The alternate-screen TUI updates in place without terminal scrollback growth.
3. Browse, search, filter, graph, and drill into Beads with Mardi Gras. Tracker status stays separate from observed activity. A row may show launching, active, claimed, draining, completed, failed, or unknown; stale evidence is visibly stale rather than promoted to an active state. The detail view names the evidence and confidence behind the state.
4. Press `a` on an unblocked issue in the fresh ready set to launch it. The confirmation shows the resolved workflow, runtime, and cwd. `external_ref=spec-task:<contained-path>` resolves to `/build <path>`; another issue resolves to `/work <id>`. No issue title, description, comment, or other tracker prose enters the launch prompt.
5. The new runtime runs the actual packaged skill. It claims through Beads before work. If a direct session or drain wins the claim first, this runtime reports the collision and exits without editing. A top-level `/build` may not treat an arbitrary pre-existing claim as drain ownership.
6. Use a separate `D` action to launch `/drain` for the repository or selected spec. The confirmation explains that it can launch multiple workers. Drain remains responsible for ready ordering, per-issue atomic claims, worker isolation, verification, closing, and orphan reclamation. It skips any issue whose claim it loses.
7. Inside tmux, the dashboard stays visible and the runtime opens in a new pane/window; a switch action is available while Mardi Gras still owns that pane handle. Outside tmux, Mardi Gras uses its existing foreground process handoff and resumes after the runtime exits. Quitting or crashing the dashboard does not kill a tmux-hosted runtime.
8. Direct `/work`, `/build`, and `/drain` use remains supported. When the CLI is installed, these skills use the strengthened claim command and emit the extended existing run events so the board can correlate them. If event emission fails, workflow behavior is unchanged. If the CLI is absent, the skills keep their direct Beads behavior, including reopening and clearing the assignee during authorized orphan recovery, and the integrated UI is unavailable.
9. Handoffs are visible and inspectable as normal Beads, but the v1 provider does not launch `/resume-handoff` or offer generic recovery/kill controls. Recovery remains the existing interactive `/resume-handoff` or `/drain` procedure, where authorization and orphan handling already live. This also avoids promising an interactive gate through Antigravity's headless `agy -p` path.
10. Uninstall removes the stable resolver, unreferenced CLI package versions, and provider configuration. Dispatch history remains unless `--purge-state` is explicitly requested; the existing run-event retention policy is unchanged. Direct skills continue with their current Beads-only behavior.
11. The machine-wide Workboard remains available as a read-only cross-repository inventory, session, and cost view; a repository-scoped TUI does not pretend to replace that breadth. Only after an installed released provider passes `agentic live --check` and the full terminal parity gate do the Workboard/kanban routes lose task mutation and agent-dispatch controls. Their repo cards then point developers to the explicit `agentic live` command for interactive work. The `workboard` skill continues to open the cross-repo overview, but its guidance distinguishes that read-only view from repository-scoped control.

## Requirements

1. R1: `agentic live --check` is read-only and fails closed on a non-Beads cwd, missing or R21-untrusted/incompatible `bd`, macOS `/usr/bin/mg`, incompatible `agentic.control/v1`, missing or unverifiable immutable skill package/execution environment, plugin/package mismatch, unsupported runtime/workflow pair, or current runtime-binary fingerprint that differs from its complete canary. Beads compatibility includes all three closed R17 behavioral profiles. V1 accepts only permanent claims without lease, heartbeat, or reclaim semantics plus certified revision-conditional update/close/history and supersession-redirect behavior; detecting lease fields, `bd heartbeat`, an absent conditional/redirect primitive, or another unknown ownership capability fails closed until a later package implements and tests the complete contract. `agentic live` starts nothing unless the same checks pass.
2. R2: `agentic launch --prepare --issue <id> --workflow auto|work|build --runtime auto|claude|codex|antigravity --cwd <repo> --json` accepts only an existing repo-local Bead that appears in a fresh `bd ready --json` result and whose provider-launch ID matches the closed ASCII grammar `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. This provider boundary is narrower than R12's opaque tracker-ID class: imported or forced tracker IDs outside the provider grammar remain usable through direct Beads/toolkit workflows when they satisfy that class, but fail provider preparation before prompt construction. `auto` physically resolves an exact `spec-task:` external reference, requires a regular authored `specs/*/SPEC.md` or `specs/*/tasks/*.md` file below the physical repository root, and otherwise selects `work`.
3. R3: Drain uses `agentic launch --prepare --workflow drain --cwd <repo> [--spec <contained-SPEC.md>] --runtime <...> --confirmed --json`. It is never selected by `auto` and refuses without the confirmation flag. A drain target has no `issue_id` member; its optional `path` is the physically contained spec path. The Antigravity adapter supports only single-issue work/build in v1; drain and resume-handoff fail before spawn.
4. R4: Prepare returns within three seconds with `agentic.control/v1` JSON containing a fresh dispatch ID and absolute `agentic supervise --dispatch-id <id>` argv. It does not claim or reserve Beads, and v1 never reuses a dispatch: every successful reply has `reused:false`. Under the dispatch-record lock, supervise permits exactly one atomic `prepared`→`starting` transition; every retry or concurrent supervisor after that transition returns the typed `dispatch_already_started` error without spawning. Duplicate prepares remain independent intents whose children later race at the Beads claim boundary.
5. R5: Mardi Gras creates the tmux pane or invokes its foreground process handoff. The supervisor inherits FDs 0/1/2, records PID, process-start identity, and boot identity, starts exactly one child without a shell, forwards termination signals, waits/reaps it, and appends started, failed-to-start, and exited events atomically. The process-start identity uses the bounded `agentic.process-start/v1` string grammar: `linux-procfs:<start_ticks>` from `/proc/<pid>/stat` field 22 or `darwin-proc-bsdinfo:<start_seconds>:<start_microseconds>` from `PROC_PIDTBSDINFO`. Linux ticks and Darwin seconds are canonical positive decimal integers of at most 20 digits. Darwin microseconds are canonical decimal `0..999999`, encoded as `0` or a nonzero value with no leading zero and at most six digits. Boot identity uses `agentic.process-boot/v1`: `linux-boot-id:<lowercase-uuid>` from `/proc/sys/kernel/random/boot_id`, or `darwin-kern-boottime:<start_seconds>:<start_microseconds>` from `kern.boottime`, with the same canonical integer bounds. An unsupported platform or unavailable start/boot identity records no value and can never produce an exact live-process join. The supervisor always exports validated `AGENTIC_DISPATCH_ID` and `AGENTIC_SUPERVISOR_PID`; it exports `AGENTIC_SUPERVISOR_START` and `AGENTIC_SUPERVISOR_BOOT` only when their corresponding values validate. Unavailable identities omit the environment variables and lifecycle/event JSON fields rather than emitting empty or sentinel values. Dashboard exit does not kill a tmux child. One shared round-trip fixture, including zero/maximum microseconds, omission, malformed boundaries, wrong-platform values, and boot changes, is the source of truth for supervisor, event, and activity parsers.
6. R6: The runtime prompt is exactly four LF-separated lines with no trailing material: `Read and follow the workflow skill at <absolute-skill-path>.`, `The user explicitly authorizes this workflow to act only on the supplied target.`, `Target: <target>`, and `Dispatch: <uuidv7>`. `<absolute-skill-path>` is the contained physical path obtained by joining the verified package root to the manifest-listed relative path and must contain no controls. `<target>` is exactly `issue <validated-issue-id>`, `artifact <canonical-repo-relative-posix-path>`, or `repository .`. Artifact paths are derived from the physically contained realpath, encoded relative to the physical repository root with `/`, no leading slash, dot segment, symlink traversal, control, or invalid UTF-8; spec-scoped drain uses the `artifact` form. No tracker prose or shell quoting is added. Claude and Codex run interactively in the inherited PTY. Antigravity uses its verified headless single-issue invocation. Prepare accepts only the exact runtime fingerprint certified by R15; supervise re-fingerprints the recorded executable immediately before spawn and fails before execution on any mismatch.
7. R7: `agentic/package-files-v1.txt` is the closed source inventory: canonical UTF-8, one repository-relative POSIX path per LF-terminated line, sorted by unsigned UTF-8 bytes, unique, and containing itself. Absolute paths, empty or dot segments, backslashes, controls, normalization collisions, symlinks, hardlinks, and non-regular files are rejected. Each listed source must be byte-identical to its blob at the recorded clean source commit. Installation copies exact blob bytes and normalizes mode to `0755` exactly when that commit records Git mode `100755`, otherwise to `0644`; other source modes fail.

   The installer writes `agentic-package-manifest-v1.json`, which is not a manifest member and contains only `schema`, `version`, `source_commit`, and `files`. `files` is in inventory order; each entry contains `path`, string mode `0644|0755`, unsigned byte length, and lowercase SHA-256. The manifest contains no timestamp, absolute path, uid/gid, filesystem traversal order, or embedded self-hash. Its bytes use R12's canonical serialization with no trailing LF. The package manifest hash is the lowercase SHA-256 of those exact bytes. Building the same committed inventory twice must produce byte-identical manifest bytes and hash; any member path, byte, normalized mode, version, or source commit change changes the identity.

   The package includes a self-contained `runtime/` Python distribution: interpreter, complete standard library, extension modules, and every non-stdlib dependency including `jsonschema`; it never imports an ambient stdlib or site package. Source member `trusted-python-runtimes-v1.json` is the closed supplier allowlist. Each entry contains only schema version, supplier, immutable artifact URL, upstream checksum-manifest URL and SHA-256, release, OS, architecture, archive format, archive SHA-256, archive byte length, one relative archive root, Python implementation/version/ABI, and the expected `agentic-runtime-files-v1.json` SHA-256. Entries are admitted only from an upstream-published immutable artifact and checksum manifest; an unlisted URL, moving tag, self-reported version, missing provenance field, or digest mismatch fails before extraction.

   Runtime extraction accepts only the allowlisted `tar.zst` profile, walks members in unsigned-UTF-8 path order, strips exactly the allowlisted root, and rejects duplicate or non-NFC paths, absolute/dot/empty/backslash/control paths, case-fold collisions, symlinks, hardlinks, devices, sockets, FIFOs, sparse files, extended attributes, and every non-regular/non-directory member. It writes regular files exclusively below `runtime/`, normalizes each mode to `0755` only when the allowlisted inventory says executable and otherwise `0644`, and verifies the complete sorted `agentic-runtime-files-v1.json` inventory of runtime-relative path, byte length, mode, and SHA-256 before packaging. The committed source manifest contains only committed inputs, including the supplier allowlist and extraction code; downloaded and extracted outputs are never misrepresented as source-commit members.

   Construction writes a separate canonical `agentic-installed-runtime-v1.json` beside the source package manifest. It contains the selected allowlist-entry digest, immutable artifact URL/digest/length, upstream checksum-manifest URL/digest and verified entry, extraction-profile version, complete runtime file inventory, and its hash. The downloaded archive and upstream manifest are temporary inputs, never executed or retained as package members; their exact provenance and digest are retained in this installed-runtime record. Its hash changes on any supplier/provenance/archive/extraction/file/mode change and is a required member of `agentic.execution-environment/v1`. Package-current verifies the installed-runtime record and every extracted file on every invocation.

   Installation probes the installed interpreter and every extension module under the closed launch environment to produce installation-specific `agentic-loader-closure-v1.json`. Linux entries for the interpreter and every transitively loaded native library contain absolute physical path, byte length, and SHA-256. Darwin standalone-file entries use the same fields; a dyld-shared-cache image instead contains no fabricated path or file hash and is identified by OS build, architecture, dyld cache UUID, Mach-O install name, image UUID, and code-directory hash obtained from the running loader. The closed schema rejects any other evidence kind and binds loader implementation/version plus the exact probe argv. Fixtures cover Linux files, Darwin standalone files, and Darwin shared-cache images; a missing UUID/hash, changed cache/OS build, or an image that changes evidence kind fails. The closure record lives beside the package manifest, is immutable after atomic installation, and is bound by the execution-environment hash rather than the reproducible source manifest.

   Installation records canonical `agentic.execution-environment/v1`: the contained interpreter's package-relative path and executable byte length/SHA-256, implementation/name/version, ABI/cache tag, SOABI, platform/architecture, OS/loader identity, `unicodedata.unidata_version`, installed-runtime-manifest hash, runtime-inventory hash, and loader-closure hash. Its hash is the SHA-256 of R12-canonical bytes. The effective immutable package identity is the ordered pair `{manifest_hash, execution_environment_hash}`; neither member alone authorizes execution.

   The stable resolver invokes that contained interpreter with `-I -S`, explicit contained package/runtime import roots, sanitized native-loader variables, and a closed environment that removes `PYTHONPATH`, `PYTHONHOME`, user-site and ambient import hooks, sets `PYTHONHASHSEED=0`, `TZ=UTC`, and admits only documented terminal/state-directory variables. Before every command it verifies the supplier/runtime inventories and all standalone loader files; on Darwin it re-reads the OS build/cache and loaded-image UUID/code-directory identities through the loader API. The child then verifies `sys.executable`, its own executable bytes, ABI/version/Unicode fields, every loaded Python module's contained runtime/package path, and every actually loaded native library against the closure before command dispatch. An ambient import, unregistered library, stdlib/extension/shared-library swap, dyld-cache identity change, OS/loader drift, fingerprint drift, or unverifiable path fails `execution_environment_changed`; no claim, prepare, supervise, or report merge continues.

   Construction occurs in a private temporary directory, verifies every member, `fsync`s files and directories, and atomically installs the directory under the R8-resolved physical account home at `.local/share/agentic-cli/<version>`. A pre-existing version is reused only after full manifest/member/environment verification; a different identity at that version fails `package_version_collision` and is never overwritten. The owned `.local/bin/agentic` below that same physical home is updated atomically. `agentic package current --json`, prepare, supervise, canary merge, and cutover revalidate both identity hashes and every member before returning or executing from it. Prepare records package root, version, package identity, and runtime fingerprint; supervise continues to use and verify that recorded identity after resolver upgrades or plugin-cache pruning. Packages referenced by nonterminal dispatches are retained.
8. R8: Every production coordination artifact—dispatch, envelope, repository lock, cohort, credential, and migration evidence—uses one environment-independent state root. The resolver obtains the current effective user's physical home from the OS account database, not `HOME` or `XDG_STATE_HOME`, and appends `Library/Application Support/agentic` on macOS or `.local/state/agentic` on Linux. Unsupported platforms fail closed. The root and every ancestor below the physical account home are owned by that effective UID, directories are mode 0700, files are mode 0600, and all opens are descriptor-relative and reject symlinks. No production environment variable or public CLI flag overrides this root; isolated tests inject a private resolver dependency rather than changing the namespace.

   Dispatch records live under that root partitioned by canonical repository identity. Intent is immutable and lifecycle is append-only under file lock with temp-file-plus-rename writes. Prepare records monotonic time, display-only wall time, and R5's validated `agentic.process-boot/v1` identity. Same-boot starting grace uses monotonic time; a changed or unavailable boot identity yields unknown/stale evidence, never wall-clock expiry or an exact-live result. `agentic activity` never appends events, repairs state, releases anything, or changes Beads.
9. R9: The canonical top-level positional form is `agentic claim --workflow work|build|drain [--run-id <uuidv7>] --json -- <id>`. Every option precedes the mandatory end-of-options delimiter and exactly one opaque tracker-ID argv element follows it; no `--issue` replacement or ambiguous subcommand is introduced. Installed top-level skills use only this form. A compatibility parser may accept the former layout only for IDs matching R2's provider-launch grammar and not beginning with `-`.

   Before envelope/marker validation, state inspection, marker repair, or mutation, every claim invokes the same Beads authorizer used by live preflight against the physical repository/worktree for that attempt. It resolves `bd` once and returns a ticket containing its absolute physical executable path and fingerprint plus repository/project/database identity, backend mode, schema version, and certified command/schema profiles. Every subsequent `bd context`, `ready`, `show`, `history`, `update`, and `close` subprocess in that attempt uses that exact absolute executable with the actual target repository as cwd, never a shell, wrapper, later `PATH` lookup, cached `live --check` result, or certification-fixture context. The fingerprint is checked before and after each subprocess. A mismatch before mutation fails closed; a mismatch or unverifiable result after mutation is ambiguous, dispatches no worker, and remains subject to the exact post-mutation recovery procedure.

   The command holds a cross-process lock keyed by the authorized `bd context --json` database/repository identity rather than the invoking worktree and re-reads issue and ready state inside that lock. The decision order is exact: an `in_progress` issue whose assignee equals `agentic:<workflow>:<supplied-run-id>` returns `claimed` with `reused:true` and repairs the missing canonical-checkout session-claim marker; an `open` issue in the fresh ready set attempts `<absolute-bd> update --claim --actor agentic:<workflow>:<run-id> --json -- <id>`; every other state returns `lost`.

   The claim command's exit status and JSON are never ownership proof. Still under the same canonical lock, every mutation attempt—including a reported success or ambiguous connection error—is followed by `<absolute-bd> show --json -- <id>` through a fresh process/connection using the same ticket. Only `status:"in_progress"` plus the exact session-unique assignee returns `claimed`. A different assignee/state returns `lost`. If the issue remains open, a second fresh process/connection must obtain a new `<absolute-bd> ready --json` snapshot and find the exact ID before the one bounded retry; the retry is followed by another fresh `show`. A missing ready membership, second unchanged result, fingerprint change, or unverifiable result returns `claim_not_applied` and dispatches no prompt or worker. The accepted profile has permanent claims, so no hidden lease can expire during work. The path performs none of the retired Git/JSONL import/export/commit/push/reset sequence, releases the lock, reports `claimed`, `lost`, or a bounded error, and never leaves a durable lease. Distinct toolkit runs and raw human actors fail against the session-unique assignee. Tests prove no claim path invokes Git or reads/writes `.beads/issues.jsonl`.

   Installed `/work`, top-level `/build`, and `/drain` use this command and stop before edits or worker dispatch on `lost`. After drain claims as `agentic:drain:<run-id>`, it writes the inflight marker and an exclusive mode-0600, nofollow-opened, file-and-directory-fsynced `agentic.drain-worker-envelope/v1` in the canonical repository state partition. Its R12-canonical bytes contain a fresh UUIDv7 handle, exact opaque issue ID, run ID, physical worker cwd, process boot identity, creation monotonic value, and envelope SHA-256. The worker prompt contains only the safe UUID handle plus the authored task pointer—never the opaque issue ID, tracker prose, envelope bytes, state path, or shell text.

   Before accepting the preclaim, the worker invokes the distinct internal form `agentic claim --workflow drain --run-id <uuidv7> --verify-drain-worker --envelope <uuidv7> --json`, which accepts no positional ID or cwd. It resolves the envelope from the canonical state partition, validates canonical bytes/hash/permissions/freshness, and obtains the issue ID and expected physical cwd as data. Before any reuse branch or marker repair, it requires handle/run/cwd/current-boot equality, exact inflight marker, and Bead assignee `agentic:drain:<run-id>`. It does not consult run events. Envelope files are removed only after the corresponding terminal tracker/marker transition succeeds; crash recovery applies the same exact tuple. A top-level build has no envelope handle and rejects the same preclaim even when an inflight marker exists.

   Every toolkit-owned orphan/requeue path retains its existing liveness and dirty-worktree safeguards, obtains a fresh stable issue revision, and changes its final tracker mutation to `<absolute-bd> update --if-revision <cursor> --status open --assignee "" --json -- <id>`; it removes claim/inflight markers only after post-state/history proves that exact actor-bound transaction. A conditional conflict preserves external authority and markers. Every toolkit-owned Beads command carrying an opaque tracker ID—including show, history, update, close, dependency mutation, and recovery—uses the capability-certified executable's per-command end-of-options form and passes the ID as one argv element. If a Beads profile lacks that form, it is incompatible. Leading-hyphen IDs, whitespace-containing IDs, malicious natural-language IDs, and other R12-valid opaque IDs are data, never options or prompt fragments. Event failure cannot authorize, weaken, or block Beads claim semantics. A raw `bd` mutation outside the wrapper remains supported but has no exact agent correlation unless another authoritative event establishes it; it is never auto-recovered by the UI.
10. R10: `agentic activity --repo <repo> --request-seq <uint64> --json` emits bounded `agentic.activity/v1`, echoes `request_seq`, and gives each source a 1.5-second deadline within a three-second total deadline. Each source reports `{ok, observed_at, error_code}` and bounded data. Sources run concurrently or under an equivalent bounded schedule. Its closed `agents` array normalizes every toolkit-orchestrated child in the repository with agent ID, optional parent ID, root run ID, label, role/kind, `queued|running|completed|failed|unknown` status, start/end instants, same-boot elapsed seconds or null, optional worktree/branch, and a bounded typed outcome summary. Rows sort by start instant then agent ID. Summaries come only from bounded lifecycle verdicts, never transcript or arbitrary output-file tails.
11. R11: Activity correlation is evidence-graded. The existing event substrate introduces schema version 2 with optional `dispatch_id` (UUIDv7), `process_pid` (positive integer), `process_start` (`agentic.process-start/v1`), and `process_boot` (`agentic.process-boot/v1`) fields using exactly R5's platform-tagged grammars. It also adds append-only `agent_queued`, `agent_started`, `agent_completed`, and `agent_failed` lifecycle records using R10's normalized IDs/fields. Every native drain/build orchestrator emits queued before dispatch, started after the runtime accepts the child, and exactly one terminal record after collection; event failure never changes workflow authorization or outcome. Version-2 records are written to a versioned log partition that legacy version-1 readers never open; new readers accept, normalize, and merge both partitions under the existing retention and repository-identity rules.

   After a successful claim, a UI-started skill emits one version-2 run event containing the canonical run ID, dispatch ID, and PID exported by `agentic supervise`; it includes the start and boot fields only when their corresponding supervisor environment variables exist and validate. Supervisor, event, and activity implementations consume the same round-trip fixture and reject noncanonical numeric spellings, unknown tags, overflow, empty sentinels, cross-platform substitutions, and changed boot identities. Activity grants an exact live dispatch/run join only when dispatch ID, PID, process-start identity, and boot identity all match the immutable dispatch lifecycle record and the currently observed boot; any missing, invalid, unavailable, or changed bridge value downgrades correlation and is never inferred by issue or time. An issue in `.beads/session-claims` is claimed but not assigned to an arbitrary agent; fresh inflight plus an exact drain run event is draining; transcript timestamps or cwd-only matches are possible activity, never exact ownership. A child with no terminal event after exact parent/process liveness is lost becomes `unknown`, not completed or failed. Branch-prefix heuristics are forbidden. Closed Beads remain completed even when stale failed records exist; a live exact dispatch is shown separately.
12. R12: Every public JSON document is exactly one UTF-8 byte sequence of at most 1,048,576 bytes: no BOM, leading/trailing whitespace, or trailing LF. Duplicate object names are rejected before decoding. Object names and string values are NFC; object members are ordered by unsigned UTF-8 bytes of their names, while arrays retain schema-defined order. Separators are exactly `,` and `:` with no whitespace. Strings emit non-ASCII characters as UTF-8, escape only `"` and `\` as `\"` and `\\`, never escape `/`, and never use `\u` escapes. Literals are exactly `true`, `false`, and `null`. A parser accepts a public artifact only when lossless parsing followed by canonical serialization reproduces the original bytes. Nesting depth is at most 16, arrays contain at most 4,096 elements, and objects contain at most 256 properties. Dynamic object keys are forbidden unless the closed schema names their key grammar and cardinality.

   JSON numbers are integers only and use the token `0`, `[1-9][0-9]*`, or `-[1-9][0-9]*`; plus signs, leading zeroes, negative zero, decimal points, exponents, NaN, and infinities are forbidden. Numeric lexemes are parsed losslessly, never through binary floating point. `agentic/schema/public-json-surfaces-v1.json` registers every numeric leaf exactly once with a semantic class and inclusive decimal minimum/maximum. Its closed initial classes are uint64 `0..18446744073709551615`, positive uint64 `1..18446744073709551615`, int64 `-9223372036854775808..9223372036854775807`, PID `1..2147483647`, exit status `0..255`, signal `1..127`, Beads priority `0..4`, writer capacity `1..5`, Unix second `0..253402300799`, nanosecond `0..999999999`, and microsecond `0..999999`. A numeric output, property, or class absent from the inventory fails the contract test.

   Every public object name and string value rejects ANSI/OSC sequences, Unicode noncharacters, and general categories `Cc`, `Cf`, `Cs`, `Co`, `Cn`, and `Z*` except ASCII space, and is assigned one exact class in the inventory: schema, enum, property, error-code, runtime, evidence-kind, and state tokens are printable ASCII of at most 64 bytes; UUIDs and commit/digest fields use their exact canonical grammars; provider-launch IDs use R2's exact 128-character ASCII grammar; opaque tracker IDs are at most 256 UTF-8 bytes and use the same Unicode safety rule; handles, external refs, and release versions are at most 256 bytes; human-readable labels/details are at most 1,024 bytes; and physical/repository paths plus debug-log pointers are at most 4,096 bytes. Subprocess stderr becomes a bounded error code and debug-log pointer, never raw TUI text. The inventory is the closed set of every public success/error envelope, schema, report, manifest, evidence record, and string or numeric leaf: claim and all three Beads capability profiles; package/runtime/loader current; launch control; dispatch lifecycle; live check/status; Mardi Gras handshake; run and child-agent events; activity; native façade; terminal parity; cutover record/status; documentation review; trusted-release and registration-repair manifests; registration-review and hash-chained migration evidence; integration cohort, capacity, landing, gate/isolation, reconciliation, publication, and errors. Adding a public JSON output, property, dynamic-key family, or string/numeric leaf without registering it fails the contract test; every registered string leaf has valid, aggregate-over-cap, depth/cardinality-over-cap, normalization, forbidden-category/noncharacter, ANSI, and OSC cases, and every numeric leaf has valid/min/max, one-below/one-above, fractional, exponent, and precision-boundary cases through the shared validator.
13. R13: Mardi Gras runs one activity poll at a time on a two-second cadence, skips a tick while one is outstanding, rejects a reply older than the last accepted sequence, and retains last-good data per failed source with a stale/error marker. A first failure renders a bounded source error rather than an empty healthy board. Selection and detail position survive refresh; alternate-screen redraw never writes unbounded scrollback.
14. R14: `agentic live` launches exactly `<absolute-mg> --provider agentic --agentic-command <absolute-agentic> --repo <absolute-repo>`. Before launch it runs `<absolute-mg> agentic-protocol --json` and accepts only the closed member set `{"schema":"mg.agentic-protocol/v1","provider":"agentic","control_majors":[1],"activity_majors":[1],"build_commit":"<40-hex>","release_version":"<bounded-version>"}` with R12-bounded fields. The provider calls only the documented argv forms in R2, R3, and R10. A successful prepare reply uses a closed discriminated target: issue replies contain the member set `{"kind":"issue","issue_id":"<provider-launch-id>","workflow":"work|build"}` and no `path`; drain replies contain `{"kind":"drain","workflow":"drain"}` plus an optional contained `path` and no `issue_id`. The enclosing reply has member set `{"schema":"agentic.control/v1","dispatch_id":"<uuidv7>","target":<target>,"runtime":"claude|codex|antigravity","cwd":"<absolute>","supervisor_argv":["<absolute-agentic>","supervise","--dispatch-id","<uuidv7>"],"reused":false}`. These inline objects define members, not wire order; every emitted and accepted byte sequence must use R12's canonical ordering exactly.

   With the provider active, every existing `a` key, issue-detail action, and command-palette launch entry routes to the same agentic confirmation and prepare call. Direct Mardi Gras prompt construction and provider-owned kill/recover controls are unavailable. Drain remains a distinct confirmed `D` action. The provider passes argv arrays only and stores switchable pane handles in memory only.
15. R15: A runtime/workflow adapter is supported only after a live canary proves that it reads the recorded packaged skill and reaches the skill's preflight before any Beads mutation. A runtime-binary fingerprint is the canonical `agentic.runtime-binary/v1` object containing runtime, resolved absolute physical executable path, executable byte length, SHA-256, bounded adapter-parsed version, OS, and architecture; its identity is the SHA-256 of the R12-canonical object bytes. The canary resolves and fingerprints the executable immediately before spawn, invokes that exact absolute path without a shell or later `PATH` lookup, and re-fingerprints it after the canary reaches preflight; any change invalidates the entry. Canaries cover Claude/Codex work, build, and drain plus Antigravity work/build. Unit-only argv tests never promote an adapter.

   The façade driver atomically accumulates one `agentic.facade-canary/v1` report keyed to one verified R7 package identity pair. Each runtime/workflow entry contains its runtime-binary fingerprint. A merge from another package or execution environment is rejected; entries for one runtime may coexist only when their fingerprint identities are identical, and a changed fingerprint atomically resets that runtime's entries. `complete` requires the full matrix and unsupported-mode checks. Prepare resolves the selected executable through the recorded package profile and accepts the adapter only when its current fingerprint exactly matches the complete canary entry. The immutable dispatch records that absolute path and fingerprint. Supervise re-fingerprints the recorded path immediately before spawn, returns `runtime_binary_changed` on any mismatch, and invokes only the recorded absolute path.
16. R16: Documentation covers install/check, browsing/detail, activity confidence, child-agent monitoring, issue launch, claim-race loss, drain confirmation, direct-skill event correlation, tmux/non-tmux behavior, spawn failure, duplicate launch, stale sources, existing recovery procedures, runtime limitations, upgrades, `fleet` differentiation, and uninstall. It states that the TUI is a repository control and observation surface, Beads owns work, and skills own execution. `fleet` remains the cheap session-local native inventory for every ad-hoc or toolkit child across repositories; `agentic live` shows repository-scoped toolkit runs/children with stronger durable correlation; Workboard remains the machine-wide historical/inventory view. No routing, skill entrypoint, or plugin/marketplace fleet promise is removed by this feature. A bounded documentation-contract test maps every named topic to the guide or README. `vale docs/guides/agentic-live.md README.md` and the normal link checks pass. An independent prose-review and README reader test write `specs/mardi-gras-agentic-integration/DOC-REVIEW.json` with schema `agentic.documentation-review/v1`, the reviewed Git revision, exact reviewed paths, the complete R16 topic list, and `vale`, `prose_review`, and `reader_test` verdicts all equal to `pass`. The contract test requires that revision to be an ancestor and the reviewed paths to be byte-identical at current HEAD. The topic map is L1 evidence; revision-bound independent review is the judgment complement for clarity and completeness.
17. R17: This feature consumes the shipped joined run-event substrate and the existing `agentic claim`/repository-lock seams. Bootstrap Task 00D installs the sole shared Beads capability parser/authorizer and conditional adapter after provider Tasks 00A–00C close and before either the registration migration or retained Task 01 can run. It recognizes three closed profiles: `agentic.bd-claim-capabilities/v1` for no-migrate context identity, ready/show/history, and atomic claim; `agentic.bd-conditional-mutation-capabilities/v1` for one stable authority revision/history cursor per issue, storage-enforced uniqueness of nonempty external refs, atomic guarded create-if-ref-absent, atomic single-issue `update|close --if-revision <cursor>`, and atomic multi-issue authority transactions that bind every expected cursor and apply a closed batch of field, metadata, and dependency operations; and `agentic.bd-supersession-capabilities/v1` for atomic current-dependent redirection plus future redirect/rejection. Every accepted mutation persists actor/reason in the same transaction, accepts opaque IDs only after end-of-options or in canonical request files, and has exact ambiguous-connection recovery.

   The batch argv is exactly `<absolute-bd> authority transact --if-revisions <absolute-canonical-request-file> --actor <bounded-actor> --reason <bounded-reason> --json`. The mode-0600 request has closed schema `beads.authority-transaction/v1`: a sorted nonempty issue array of opaque ID and expected authority revision, plus an ordered nonempty operations array limited to set issue field, replace bounded metadata key/value, add/remove/retype one dependency, or set one of the spec's named blocked/manual states. Every incident dependency endpoint must appear in the issue array; repeated/conflicting operations, an unlisted endpoint, cycles, unknown fields/types, an empty batch, or any cursor mismatch rejects the whole transaction with no history event. Success returns the complete next revisions and actor-bound history events; ambiguous recovery replays only after fresh reads prove exact all-before or all-after state.

   An issue's authority revision advances atomically on every issue-field or provider-visible metadata change, every addition/removal/type change of a dependency incident to that issue, every supersession/redirect change, and every other field included in R20's scheduling fingerprint, regardless of whether the writer is the patched command or an older storage client. A dependency transaction advances both endpoint revisions and writes ordered actor-bound history for both. Therefore add/remove ABA or an older-client edge mutation cannot preserve a close or migration cursor. The prerelease migration driver uses only the exact R21 patched binary, Task 00D authorizer, and revision-bound fixtures and fails before mutation if a required primitive is absent. Replacement Task 14 owns only package-current, runtime capability/profile parsing, process-start/boot grammars, and their shared fixtures; it does not own Beads authorization. Package certification behavior-tests each supported Beads release/profile in isolated embedded and server-backed repositories and records version, command/schema fingerprint, observed claim/ownership/history fields, backend mode, heartbeat/reclaim command presence, create uniqueness, conditional single/batch success and conflict, actor/reason atomicity, cursor monotonicity, history ordering, raw older-client incident-edge movement, and before/during/after supersession dependency races.

   One shared Beads authorizer is mandatory for `agentic live --check` and every direct, UI, drain, migration, requeue, recovery, or close mutation. Each invocation freshly resolves and fingerprints one physical `bd` executable, reads `bd context --json` through that executable in the actual target repository, and binds repository/project/database identity, backend mode, schema version, and command/schema fingerprint to the certified permanent no-lease and conditional-mutation profiles. The caller must use the ticket's same executable for every subsequent subprocess. Binary digest is diagnostic provenance rather than sole authorization; version comparison or cached live status cannot authorize compatibility, live preflight never creates or mutates a repository, and fresh post-mutation state/history remains the outcome decision. A release lacking either conditional form, stable cursor, atomic history semantics, or supported opaque-ID delimiter is incompatible.

   Bootstrap Task 00D owns and lands the shared parser/authorizer, conditional single/batch adapter, no-migrate identity and core/full schema-install client, their toolkit tests, and the migration driver's real-provider inspection/primitive-receipt/snapshot integration fixtures. It does not own the manifest's migration graph, supersession mapping, or release semantics. Retained Task 01 then owns only R9's CLI grammar, canonical repository claim lock, fresh authorizer-ticket consumption, exact claim decision/retry/post-read behavior, drain-envelope verification, and claim/requeue integration. It does not own the provider, authorizer, conditional primitive, package/runtime/process identity, native façade instrumentation, activity, or cohort scheduling. Its authored task file, registered definition hash, live acceptance, and notes remain unchanged during repair; the new immutable Task 00D definition carries the newly required toolkit bootstrap work and blocks Task 01. Replacement Task 14 consumes Task 00D's Beads authorizer while owning the separate package/runtime/process foundation. Replacement Task 17 consumes Task 01's canonical run ID and Task 00D's conditional requeue adapter and owns only the installed work/build/drain claim and requeue migration, including every toolkit-owned requeue surface such as handoff. Replacement Task 38 depends on Task 17 and Task 16's backward-compatible version-2 substrate and owns generic run-event plus native child-lifecycle emission, portable entrypoint/runtime wiring, and the hermetic package/fingerprint-bound façade-canary merger. It absorbs the unfinished toolkit-core task 08 event/conformance obligations while Task 17 proves every final requeue mutation clears the assignee. Task 16 owns the version-2 schema/storage evolution: old packages read only version 1, new packages merge version 1 and version 2, and Task 38's migrated façades emit version 2. The activity projection depends on Task 38. Replacement Task 19 owns reproducible package/runtime construction, the contained resolver, isolated install/upgrade/uninstall, and installation verification while consuming Task 14's package-current identity verifier. Replacement Task 39 owns live activation, authority/provider/runtime preflight, adapter selection, and runtime canaries; it never reimplements package construction or package-current parsing. Every packaged skill/profile/manifest mutation lands before installed native façade certification; certification installs the exact source revision, binds the report to its verified R7 package identity pair and per-runtime binary fingerprints, and atomically replaces or resets stale entries when either identity changes. This spec owns only live-view fields, dispatch-to-run/session correlation, strict same-human multi-session claim outcomes, and provider integration. No independent event writer/store, duplicate runtime capability registry, or orchestration helper is allowed.
18. R18: The upstream contribution is represented in this repository by `specs/mardi-gras-agentic-integration/upstream/mardi-gras-agentic-provider.patch`, generated against exact commit `70e36ff5f180073864163e39739324c9fbec989e`. `specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh` clones or accepts `MARDI_GRAS_CHECKOUT`, verifies that base, applies the patch in a temporary branch, and runs the named Go tests. The terminal E2E obtains its binary through that helper by default. `specs/mardi-gras-agentic-integration/trusted-mardi-gras-releases-v1.json` is a closed allowlist populated only from an upstream-published release and checksum manifest; each entry binds release version, 40-hex build commit, OS, architecture, and artifact SHA-256. For later release certification only, `MARDI_GRAS_BINARY=<absolute> .../e2e-provider-pty.sh --released --report <path>` resolves a regular executable, computes its bytes' SHA-256, validates its R14 version/build handshake against the matching trusted allowlist entry for the current OS/architecture, runs the identical journey, and atomically writes bounded `agentic.terminal-parity/v1` evidence containing that provenance, protocol, package identity, and named journey results. A self-reported handshake without an exact trusted artifact match, a locally patched binary, or `--released` without that binary/report contract fails before the journey. An upstream PR/release is reported as external state, not fabricated by acceptance; production `live` support remains disabled until a released artifact is explicitly allowlisted.
19. R19: Legacy control cutover requires all of: installed Beads and Mardi Gras binaries whose computed digest, version, build commit, OS, architecture, and protocol majors match exact R21 and R18 trusted-release entries; `agentic live --check` passing against its verified immutable package/execution environment; full native façade canaries; and a terminal E2E/parity journey against those same binaries. `agentic live --record-cutover --facade-report <path> --terminal-report <path> --json` is the only mutating certification command. It re-runs the read-only check, rehashes both provider binaries and the R7 package identity pair, re-resolves every supported runtime, requires its path/bytes/version/OS/architecture fingerprint to equal the corresponding complete façade-canary entries exactly, validates both reports, and atomically stores `agentic.cutover/v1` in the R8 state root with both trusted release identities/artifact SHA-256 values, protocol majors, immutable package version, manifest and execution-environment hashes, runtime binary fingerprints, repository fixture revision, façade-report hash, terminal-report hash, and recorded time. `agentic live --cutover-status --json` repeats those exact checks and returns ready only while every receipt identity and current binary fingerprint still match; absence, mismatch, malformed evidence, runtime/interpreter/dependency/Unicode drift, an untrusted handshake, or either patch-only build fails closed. Fleet remains independently available in every cutover state.

   Until that exact receipt is ready, existing Workboard behavior is retained. Afterward, agent-console `/workboard` and `/workboard-kanban` remain live read-only cross-repository inventory/session/cost views but no longer expose dispatch, priority, status, resume, verify, or stop controls; each repo card shows a bounded `agentic live` migration command. The `workboard` skill continues to launch this machine-wide overview and explicitly routes repository-scoped interactive tracking and launch requests to `agentic live`. Historical scanner/research files and agent-console's skills/cost surfaces remain live unless a later measured inventory decision authorizes removal.
20. R20: Drain may execute the current dependency-ready antichain concurrently in isolated Git worktrees even when members' `Touch:` sets overlap. Overlap alone never serializes execution. A dependent is never sealed with its predecessor: the current cohort must publish and close before a later `bd ready` scan can form the next wave. Authored registration definitions are immutable provenance, not a frozen execution plan: the live Beads workset may gain issues, dependencies, field changes, supersessions, and human decisions at any time. Only one sealed cohort's membership is immutable, and each later cohort comes from a fresh live ready/graph snapshot; neither an original task count nor a registered definition hash fixes the future workset.

    A live field change invalidates the member fingerprint and reschedules it; it never silently expands the pointer-only authored work instruction. If critique, discovery, or a human decision adds mandatory implementation or acceptance beyond a registered definition, the cohort records a typed `agentic.workset-extension/v1` action containing the new canonical authored task path and definition hash, the complete new issue envelope, and the affected downstream issue/revision plus intended blocking edge. It never mutates the registered definition or expands the sealed cohort. The coordinator verifies the new authored bytes/hash and consumes that action through Task 00D's storage-guarded complete create-plus-initial-edge transaction; the new issue is absent until that one transaction commits and can appear only in a later fresh ready scan after the current cohort publishes and closes. It does not append acceptance prose that the worker envelope cannot carry, use this repair's forbidden ordinary create-then-edge registrar, or assume the original registered cardinality remains complete. Every unresolved shared schema, name, package identity, or interface decision is likewise represented by a prerequisite bd decision or implementation issue; the coordinator validates those closed edges before dispatch.

    Each shipped runtime profile declares a positive native writer capacity. Capacity has one machine/account-global authority and lock across all runtime profiles under the R8 state root. Admission acquires that account-global capacity lock, then the canonical repository-wide lock, then the target seal lock. Under those locks it validates the one global ledger and every relevant repository active pointer, and appends one content-addressed, fsynced prepared reservation `Q` for the deterministic first `min(fresh-native-slots, selected-profile-cap-minus-Q-filtered-to-runtime-profile, 5-minus-Q-filtered-to-repository)` ready members before creating `A`. Every Q names its runtime profile, repository, and target. There is no per-runtime or repository Q ledger: both limits are filtered views of the same validated chain, so a prepared Q from Codex is visible to a later Claude admission in the same repository before A exists.

    The ledger is exactly `<R8-root>/capacity/global-v1/` with mode-0700 `events/`, mode-0600 immutable canonical events named `<20-digit-sequence>-<sha256>.json`, and atomic mode-0600 `head.json`. Events form one digest chain and are only `reservation_prepared`, `reservation_committed`, or `reservation_released`; each successor names its exact predecessor and Q identity. Append uses an owner-UUID-bound nofollow temp write, file/directory fsync, rename, then head temp/rename/fsync. Recovery accepts head at the last event or exactly one valid unreferenced next child; an owner-bound temp may be removed only after exact-dead proof. A fork, gap, torn/malformed event/head, live/unknown/foreign temp, duplicate terminal, or prepared/committed/released payload mismatch makes all writer capacity zero. Thus Q has one durable authority and every runtime/repository admission/release is an idempotent event transition, not a mutable counter.

    The resume token is generated before `Q`; `Q` contains reservation/cohort/repository/target identities, permit count, owner generation and exact liveness evidence, plus the token digest. Prepared and committed reservations both consume permits. While `A` is absent, Q's owner/liveness/token digest is authoritative: a matching prepared `Q` may be completed only by an exact-live or unknown matching-token owner, or released only after exact-dead proof. Once `A` exists, Q's owner fields are historical and capacity validation binds Q only to fresh `A`, its committed rotation head, and current credential; rotation need not rewrite Q. Terminal release compare-and-swaps `A` away and then appends the released state for that exact Q in the sole global ledger under the same ordered locks; a missing or conflicting transition never frees or duplicates capacity.

    The global ledger is shared across runtimes and repositories; filtered sums enforce each runtime-profile cap and the independent repository hard cap. The Codex profile remains one until native isolated-writer execution is proven; no runtime profile exceeds five and the repository sum never exceeds five. Coordinators using different runtimes, repositories, or target branches therefore cannot double-observe a slot. Tests race same- and cross-runtime admissions within/across repositories and kill holders on both sides of `Q` and `A`. Unselected ready issues remain untouched for a later cohort or another claimant.

    A separate canonical-repository worktree-administration lock covers only `git worktree add`, `lock`, `unlock`, `remove`, `repair`, and `prune` plus any unavoidable shared Git-configuration mutation. Worker execution, review, tests, and edits in existing worktrees never hold it. Workers may not mutate global or common-repository Git configuration. Automated repair/prune is forbidden while any live cohort owns a worktree; cleanup revalidates the recorded physical path, branch, HEAD, owner generation, and dead process before a bounded administrative operation. At launch, the coordinator resolves `git symbolic-ref -q HEAD`, accepts only canonical `refs/heads/*`, records the physical launch worktree and exact destination in the confirmation, and rejects detached, unborn, tag, remote-tracking, pseudo, or other refs. The target branch may be checked out only in that launch worktree. Seal, publication, recovery, and cleanup define clean as all of: `git diff-index --quiet HEAD --`; `git diff-files --quiet`; empty NUL-delimited output from `git ls-files --others --exclude-standard -z`; and empty NUL-delimited output from `git ls-files --others -i --exclude-standard -z`. They reject any index or tree entry with Git mode `160000`, any initialized or uninitialized submodule, and any nested worktree boundary. Thus tracked, staged, untracked, ignored, and submodule state must all be empty or absent; `git status` alone is never cleanliness proof.

    Before any claim, cohort creation holds the account-global capacity lock, repository admission lock, and canonical-repository seal lock keyed by repository identity plus target ref in that order. Permit release takes the same three locks in the same order; a transition needing only its existing cohort/target holds only the target seal lock, so independent execution and integration remain parallel. Each new cohort ID is one canonical lowercase UUIDv7. Its main ref is exactly `refs/agentic/integration/<cohort-id>/head`; diagnostic refs are `refs/agentic/integration/<cohort-id>/diagnostic/<uuidv7>/head`; the sole target-reconciliation ref is `refs/agentic/integration/<cohort-id>/reconcile/1/head`. No ref is an ancestor of another. A CSPRNG-generated 256-bit resume token is encoded as 64 lowercase hex characters. Credential files use exclusive create, mode 0600, file and directory `fsync`, and atomic rename. A token travels only through an inherited dedicated file descriptor or stdin, never argv, environment, public evidence, or logs. Public evidence records only its SHA-256.

    Initial cohort creation is one closed `Q/A/P/N/R/C/K` protocol under the ordered locks. The target-state key is SHA-256 over R12 canonical JSON bytes, without a trailing LF, for the exact two-member object `{"repository_identity":<R9-ticket-value>,"target_ref":<canonical-full-ref>}`. The symlink-safe mode-0700 target directory is exactly `<R8-state-root>/cohorts/<target-state-key>/`; its mode-0600 `active.json` is the sole active pointer and current-owner authority. Cohort evidence is immutable canonical JSON under `<target-directory>/<cohort-id>/events/`; credentials are exactly `credentials/next` and `credentials/current`, with no other owner file. `A` contains cohort ID, `Q` identity, main ref, target/base, membership and ordered-ready digests, runtime/profile and reserved permit count, current owner generation, coordinator run ID, PID/start/boot identity, and credential digest. Generation zero is copied into immutable `P`/`K`; later `A` bytes may change only through the rotation compare-and-swap below, so every liveness or credential decision reads fresh `A` rather than an old prepared event. `P` is a fsynced append-only `agentic.integration-cohort/v1` prepared event containing the generation-zero identity plus complete immutable membership, launch worktree, capacity inputs, and seal second. `N` is the exclusively created and fsynced next credential; it is not yet ownership. `R` is the main ref at the sealed base. `C` is the credential atomically installed as current. `K` is a fsynced committed event hashing generation-zero `A` and `P` and naming the current credential digest. There is no owner artifact outside these named states.

    The only creation order is append/fsync prepared `Q` in the sole global ledger, exclusive-create/rename/fsync compare-and-swap `A`, append/fsync `P`, create/fsync `N` and its directory, compare-and-swap `R` from missing to the sealed base, rename `N` to `C` and fsync the directory, then append/fsync `K` and mark that exact `Q` committed. A second sealer that observes `Q` or `A` must resume, credentialed-adopt, exact-dead-abort, or report `cohort_busy` for that named reservation/cohort; it may never allocate another cohort for the target. No claim, worker dispatch, worktree creation, landing, or gate may occur before both `K` and committed `Q`.

    Liveness is closed as `exact_live`, `exact_dead`, or `unknown`: matching PID/start/boot evidence is live; an observed missing PID, mismatched start identity, or changed boot identity is dead; unavailable or incomplete identity evidence is unknown. An exact-live owner requires the matching token; unknown permits only a matching-token resume; only exact-dead permits uncredentialed abort/takeover. Pre-commit recovery is exhaustive: `Q` only may resume `A` with the matching in-memory token or exact-dead-release; `Q+A` may resume `P`, while exact-dead intended ownership appends `aborted`, compare-and-swap clears only that exact pointer, and releases only that `Q`; `Q+A+P` may resume with the matching token or exact-dead-abort; `Q+A+P+N` with ref missing may resume the ref CAS, or exact-dead recovery validates/removes `N`, fsyncs, appends `aborted`, clears `A`, and releases `Q`; `Q+A+P+N+R` at the sealed base may install `C`, or exact-dead recovery CAS-deletes only that unchanged ref, removes `N`, fsyncs, appends `aborted`, clears `A`, and releases `Q`; `Q+A+P+C+R` without `K` permits the authorized owner to append `K`, while exact-dead recovery first appends `K` and then uses ordinary takeover; committed `Q+A+P+C+R+K` with the ref consistent with its committed landing chain uses normal resume/takeover. Prepared evidence is never erased. The ordinary active pointer is cleared only after every included member is closed, every excluded disposition and marker transition is complete, retained refs are no longer needed for recovery, and terminal cleanup evidence is fsynced. Closing-ineligible terminalization may instead move retained-ref authority to the exact non-capacity diagnostic/quarantine pointer before clearing `A` and releasing `Q`. A crash after `K` but before the first claim therefore resumes the same cohort rather than sealing duplicate work. Any other combination, missing required artifact, unexpected ref OID, next credential without matching prepared evidence, pointer/record/credential mismatch, or generation mismatch fails closed without deletion.

    Takeover of a committed cohort uses a separate append-only `rotation-prepared → next credential → rename over current → active-owner-CAS → rotation-committed` protocol. `rotation-prepared` contains the exact old `A` digest/generation/current-credential digest and the complete proposed next `A` bytes, successor PID/start/boot, generation, and next-credential digest. Allowed intermediate states are old `A`/old current plus prepared; old `A`/old current plus prepared plus matching next; old `A`/new current plus prepared and no next; or next `A`/new current plus prepared without committed. Recovery completes the unique next step. A dead intended successor before credential rename aborts the rotation while retaining old `A`/current; after rename recovery must CAS `A` to the recorded next bytes and append committed before any liveness or further takeover decision. Every subsequent transition folds the unique committed rotation chain and requires fresh `A` to equal its head. An unrecognized current digest, conflicting generation, or `A`/rotation mismatch blocks. A racing adopter returns `cohort_busy`.

    Repository drain accepts generic issues, unnumbered task files, and equal task numbers from different specs. Because members are one ready antichain, their total-order key is numeric Beads priority ascending, parsed `created_at` instant ascending, canonical spec identity from an exact `spec-task:specs/<slug>/tasks/<filename>.md` match where `<slug>` is lower-case ASCII `[a-z0-9][a-z0-9-]{0,127}`; otherwise bounded external ref; otherwise `~generic`; then a base-10 task number parsed only from filename prefix `^[0-9]{2,9}-` or the `2147483647` sentinel; then bounded external ref or empty string; then bd issue ID. `created_at` must be a valid RFC3339 instant and compares by Unix nanoseconds; invalid/missing priority or creation time fails seal. Strings compare by unsigned UTF-8 bytes. Duplicate numbers across or within specs remain deterministic through later fields. The ready-set digest is SHA-256 over the compact UTF-8 JSON array of ordered IDs with no whitespace or trailing LF. Each member also records a canonical scheduling fingerprint over status, assignee, priority, acceptance, definition provenance, dependency IDs/types, supersession state, and provider-visible metadata from the same snapshot. The revision-bound manifest is the durable checkpoint; restart resumes its membership, base, target, order, capacity, and ownership generation instead of recomputing readiness.

    Fresh R9-authorized reads compare that scheduling fingerprint immediately before claim, before a worker result becomes `landed`, before final gate partitioning, in one last barrier after the gate and immediately before publication-prepared evidence, immediately after the target-ref CAS/receipt, and before each close. A new issue outside the cohort is simply visible to the next fresh scheduler scan. A member that is no longer ready or whose fingerprint changed before claim is not claimed and is recorded `rescheduled`. A change after claim but before the final publication barrier is accepted only while the cohort still has exact ownership: it records the before/after fingerprints and uses R17's multi-issue conditional transaction to return the affected issue or inseparable landing group to open with empty assignees; markers are removed only after post-mutation proof. A concurrent state/owner change instead follows `contended`.

    Excluding a landed group is a prepared/committed `agentic.integration-group-disposition/v1` transition. Prepared evidence names the complete pre-partition, whole group expansion, expected authority cursor and ownership tuple for every member, exact conditional batch bytes, intended per-member tracker/marker disposition, and complete post-partition. After that evidence is durable, one R17 authority transaction applies all tracker dispositions atomically; recovery observes only the exact all-before state, where it retries, or exact all-after state, where it commits the transition. No partial member success is valid. The committed record atomically supersedes the pre-partition for gate/publication readers, after which marker cleanup is individually idempotent and proven. Thus a composite group is excluded as one unit, its final candidate is rebuilt and gated from the remaining committed partition, and every embedded member is rescheduled by the same evidence.

    Publication-prepared evidence binds the last barrier's complete fingerprint set and authority cursors. Because raw Beads and Git cannot share one transaction, a change first observed after the target CAS is explicitly `published_contended`: the publication receipt is marked permanently non-closing; no issue is reopened, rescheduled, or closed and external tracker authority is never overwritten. The coordinator stops or proves dead every owned process, removes only proven-clean worktrees and non-authoritative markers, preserves all immutable evidence and integration refs, and writes a mode-0600 `quarantine.json` pointer naming target, published OID, issue/cursor deltas, retained refs, and required human/follow-up disposition. Under account-global-capacity/repository/target locks it CAS-clears `A` and releases `Q`; `quarantine.json` consumes no writer permit but blocks a new ordinary cohort for that target until a separate registered reconciliation issue conditionally records the disposition and clears it. A crash at each quarantine/`A`/`Q` boundary resumes the same terminalization. Thus a change known before CAS never publishes, while a race after the last barrier may remain visibly published but cannot authorize tracker closure or permanently exhaust writer capacity. Barrier tests cover two sealers, cross-runtime/repository/target capacity races, killed permit holders, exact-dead adoption, unknown credentialed resume, prepared/committed credential recovery, duplicate resume/adoption, capacity truncation, fairness within priority, multiple waves, a new dependent issue before final readout, and dependency/acceptance changes before claim, after landing, during the gate, on both sides of publication-prepared, target CAS, receipt, every close, and quarantine permit release.

    Quarantine has one executable escape hatch, not a self-blocking ordinary cohort. `quarantine.json` contains a complete closed immutable reconciliation definition and hash. The coordinator guarded-creates one Bead with external ref `agentic-quarantine:<quarantine-sha256>`, that definition hash, and no free-form implementation scope. A direct attended `/work <id>` or dedicated non-drain dispatcher may claim it through ordinary Beads, but its closed preflight verifies the issue against `quarantine.json`, forbids file edits or an edit-capable child, and immediately invokes `agentic cohort reconcile-quarantine --quarantine <digest> --issue <id> --confirmed`; drain and ordinary cohort admission reject that issue. The command acquires the account-global/repository/target locks and atomically reserves one normal Q bound to the quarantine digest, reconciliation issue, runtime profile, and repository before creating a worktree or launching the writer. It waits or fails when either filtered cap is zero and releases Q through the same crash protocol; the sole exception is bypass of the target's quarantine prohibition, never capacity.

    After verifying the issue's exact assignee plus quarantine/evidence/ref/target state, the command creates one dedicated worktree from the retained ref. Its closed decisions are `revalidate_current`, `publish_reconciliation`, or `abandon`. `revalidate_current` re-reads every affected issue fingerprint/cursor, independently reviews the exact sealed-base-to-current-target diff, runs affected tests and the full canonical gate, repeats the post-gate/pre-receipt barriers, and emits a new `quarantine-resolution-publication/v1` closing-eligible receipt bound to current target, complete workset, exact cursors, review, and gate; only then may ordinary receipt-bound closes run. Any ABA/workset/target change before or during those closes re-quarantines. `publish_reconciliation` applies the same review/tests/gate/barriers and emits the same new receipt after target-ref CAS. `abandon` may only conditionally block/reschedule still-owned issues and never close them. The command records prepared/committed evidence and exact crash recovery for Q, worktree, review/gate, target CAS, tracker batch, new receipt, close, and quarantine-pointer CAS. Only a terminal receipt may clear that exact quarantine; contention keeps it. This path cannot launch unrelated work or exceed any writer cap.

    Seal preflight admits a closed tested Git version/capability and ref-backend set plus repository object format (`sha1` or `sha256`); all OIDs must be canonical lowercase 40- or 64-hex values matching that format. It rejects replacement objects, grafts, shallow history, or a `.gitattributes` merge driver other than the tested built-in text, binary, and union behaviors. That attribute check is repeated against the exact input and branch trees immediately before every member merge-tree, and against every input tree before a diagnostic rebuild, conflict reconciliation, gate-isolation reconstruction, or target reconciliation. A worker-added/change-to custom driver, macro, unsupported attribute, or tree-to-tree attribute drift blocks before object construction; seal-time inspection alone is insufficient.

    Construction runs in an owned private bare integration repository of the same object format, but explicitly sets `GIT_OBJECT_DIRECTORY` to the canonical repository's resolved common object directory so every content-addressed output is visible to and retained by canonical integration refs. Every construction command uses one resolved absolute Git binary and `env -i` with owned empty `HOME` and `XDG_CONFIG_HOME`, `PATH` containing only the resolved binary's directory, the explicit private `GIT_DIR` and canonical `GIT_OBJECT_DIRECTORY`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_COUNT=0`, `GIT_NO_REPLACE_OBJECTS=1`, `LC_ALL=C`, and `TZ=UTC`; no other inherited `GIT_*` variable is admitted. Its closed local config disables signing and contains only the tested deterministic settings. Integration and diagnostic ref CAS commands instead name the canonical common Git directory explicitly, use the same empty environment/config suppression, and fail preflight on an unprofiled ref backend; they do not construct object bytes. The capability record binds Git version, command options, object and ref formats, binary digest, sanitized environments, private-config digest, and resolved common directories.

    Each verified branch records its immutable branch OID. For member landing, the current main-ref OID is `input_oid`; sanitized `git merge-tree --write-tree <input_oid> <branch_oid>` in the private repository supplies the candidate tree or a typed conflict. A clean tree becomes a deterministic unsigned two-parent commit with parents `input_oid` then `branch_oid`. The coordinator sets UTF-8 `GIT_AUTHOR_NAME=agentic`, `GIT_AUTHOR_EMAIL=agentic@local.invalid`, `GIT_COMMITTER_NAME=agentic`, and `GIT_COMMITTER_EMAIL=agentic@local.invalid`; `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` are both the exact ASCII value `@<seal-second-plus-member-index> +0000`; and the complete stdin is the exact UTF-8 byte sequence `agentic cohort <cohort-id> member <issue-id>\n`. It invokes sanitized `git -c commit.gpgSign=false -c i18n.commitEncoding=UTF-8 commit-tree <tree_oid> -p <input_oid> -p <branch_oid>` in that private repository. No signing, editor, hook, cleanup, user/system config, replacement object, or unprofiled merge driver participates. Tests parse the resulting object and require the exact ordered headers and one trailing LF in the message, and reproduce the same OID under conflicting global/local Git configuration, environment, and timezone.

    A prepared landing record names input, branch, tree, and output OIDs before sanitized `git update-ref <main-ref> <output_oid> <input_oid>` compare-and-swaps the durable ref; a committed landing record follows. Prepared evidence is sufficient for deterministic reconstruction: recovery first verifies `input_oid` and `branch_oid` remain retained, reruns the exact merge-tree/commit-tree recipe whenever the recorded tree or output object is missing, and requires reproduced OIDs to equal the record before retrying the CAS. Ref at output writes a missing committed record; any third OID or reproduction mismatch fails closed. Tests run aggressive prune between object construction, prepared evidence, ref CAS, and committed evidence. Diagnostic landings use the identical reconstruction rule.

    The current landing groups always form one ordered, disjoint, exact partition of the currently landed member IDs; no member is absent or duplicated and every group's member expansion follows sealed order. Each ordinary committed landing atomically appends one singleton group for that member. A conflict gets one designated integration worktree, never auto-selects ours/theirs, and must repeat independent review and affected tests against the reconciled branch OID. A successful reconciliation writes a prepared group-transition record that names the entire accepted-prefix group list plus the conflicted member, their exact member expansion, and one replacement composite group; after the branch/ref CAS it appends a committed transition that atomically supersedes every named input group. Recovery accepts only pre-transition partition plus input ref or post-transition partition plus output ref and completes the missing CAS/record; mixed partitions fail closed. Gate, isolation, publication, disposition, and recovery read only the latest committed partition. Thus the reconciled member and every accepted-prefix input embedded in its branch form one indivisible `landing_group`; subsequent gate isolation or workset-drift disposition may accept or reject only that whole group and can never retain the reconciliation while excluding an embedded member. A second conflict records `blocked`, preserves branch/worktree/ref/evidence, and lets only dependency-independent later groups proceed.

    Member dispositions are closed:

    | Disposition | Included in final candidate/published HEAD | Tracker/marker action | Cohort effect |
    | --- | --- | --- | --- |
    | `landed` | yes | stays in progress; markers retained | eligible for gate/publication/close |
    | `blocked` | no | issue becomes blocked; claim/inflight markers removed only after that mutation; branch/worktree retained | terminal-excluded; its dependents cannot release |
    | `deferred` | no | before-claim external deferral has no markers; a claimed worker returning `DEFERRED` records its durable question, then atomically sets status `deferred` with empty assignee and removes markers only after that succeeds | terminal-excluded; its dependents remain non-ready |
    | `rescheduled` | no | a live scheduling-fingerprint change prevents claim or returns an exactly owned claim to open with empty assignee; markers are removed only after post-mutation proof | terminal-excluded; a fresh Beads graph decides later readiness |
    | `skipped` | no | accepted only when already closed or superseded before claim; no markers exist | terminal-excluded; existing bd semantics govern dependents |
    | `contended` | no | claim loser makes no tracker or marker mutation; the winning external actor retains Beads authority | terminal-excluded; existing Beads state governs dependencies |

    Worker/review/test/reconciliation/gate exhaustion maps to `blocked`; no separate ambiguous failed state exists. The canonical gate starts exactly when every member is `landed` or terminal-excluded and at least one member landed. An all-excluded cohort becomes terminal without publication. A passing full-stack gate publishes normally. An explicitly infrastructure-class failure may retry the identical full stack once; functional failures do not receive a flaky retry.

    A repeated or functional failure enters deterministic ordered batch isolation instead of blocking every landed member. Starting from the sealed base and ordered immutable landing groups, `classify(known_good, candidates)` rebuilds and gates `known_good + candidates`; pass accepts the whole candidate suffix, failure of a singleton group changes every member of that group to `blocked` with `agentic.integration-gate-isolation/v1` evidence, and a larger failure splits candidates at `floor(n/2)`, classifies the left half, then classifies the right half in the context of the accepted left prefix. The already-failed full stack is not redundantly tested. A failure caused only by interaction is deterministically attributed to the later ordered group that first fails in its accepted-prefix context.

    Every candidate stack uses the same merge-tree and deterministic commit-tree rules, retaining each member's original sealed index rather than its subset position. It writes prepared/committed diagnostic landing records and compare-and-swaps only its exact private diagnostic `.../<uuidv7>/head` ref; it never rewrites the original failed-stack ref or moves the publication target. Gate-isolation evidence identifies exact failed groups, accepted groups and their member expansion, branch/input/tree/output OIDs, gate result, and the original landing it supersedes for final-publication eligibility. A final rebuilt accepted stack must pass the full canonical gate before its diagnostic HEAD becomes `gated_oid`; the publication receipt names both all sealed members and the exact accepted/blocked partition. If that confirmation fails, the cohort becomes `gate_inconclusive`, all still-landed members become blocked, and all refs/evidence remain. The hard gate-invocation budget is `2g+2` for `g` originally landed groups, including the initial run, optional infrastructure retry, classifications, and final confirmation; exhaustion fails closed. Only finally accepted landed members can close. Blocked/deferred members and their dependencies never release through cohort mechanics.

    After a passing gate, publication holds both the target seal lock and an exclusive launch-worktree lock. It re-verifies that the worktree's symbolic HEAD is the sealed target, no other worktree checks out that branch, its target ref and HEAD equal `expected_oid`, its index and tracked worktree equal the expected tree, and every exact tracked/staged/untracked/ignored/submodule cleanliness check above passes. It appends `agentic.integration-publication/v1` prepared evidence, runs sanitized `git read-tree --reset -u <gated_oid>` in the locked launch worktree without moving the symbolic target ref, then compare-and-swaps that ref from `expected_oid` to `gated_oid` and appends committed evidence. Success requires target ref and HEAD equal the gated OID, index and tracked worktree equal the gated tree, all exact cleanliness checks still pass, and the committed receipt names all original members and the accepted/blocked landing groups.

    Recovery under the same locks recognizes all four exact crash-boundary combinations: expected ref plus expected index/worktree resumes before `read-tree`; expected ref plus gated index/worktree performs the ref CAS; gated ref plus expected index/worktree performs `read-tree`; gated ref plus gated index/worktree appends the missing committed receipt. Any other tracked tree, index/worktree disagreement, failed untracked/ignored/submodule check, other checkout, or third ref OID blocks without reset or closure. If the target CAS loses to a third OID after the worktree reached the exact gated tree, recovery first restores index/worktree to the now-current target tree with sanitized `read-tree --reset -u` only while the exclusive lock and exact prepared evidence prove no user mutation, records the conflict, and enters target reconciliation; any ambiguity blocks.

    Target movement enters `publish_conflict` without creating a successor owner or cohort. Under the same seal lock, active-cohort pointer, credential, and owner generation, one bounded reconciliation generation writes prepared then committed `agentic.integration-reconciliation/v1` records for the same cohort ID. Generation 1 seals the now-clean moved launch checkout as `moved_oid`, links generation 0 and the original member IDs, and treats predecessor `gated_oid` as one immutable aggregate candidate without new claims. Its exact ref `refs/agentic/integration/<cohort-id>/reconcile/1/head` starts at `moved_oid`.

    The generation runs sanitized `git merge-tree --write-tree <moved_oid> <gated_oid>`. A clean tree becomes one deterministic unsigned two-parent commit with parents `moved_oid` then `gated_oid`, the same fixed agentic identities, author and committer date `@<seal-second-plus-original-member-count-plus-1> +0000`, and exact message `agentic cohort <cohort-id> reconcile 1\n`. Prepared evidence records moved, gated, tree, and output OIDs before the ref CAS; recovery deterministically reconstructs missing objects exactly as for member landings. The generation repeats full diff review, affected tests, and the canonical gate, then uses the same checked-out-worktree-aware publication and post-publication fingerprint barrier. Recovery derives authority only from fresh `A`, its committed rotation head, and current credential and resumes the unique prepared generation; it can neither mint another owner nor create another cohort. The final receipt links reconciliation generations 0 and 1 and authorizes closure of original landed members.

    A reconciliation merge conflict, second target movement, second generation, dirty/mixed target state, or reproduction mismatch cannot wait while consuming permits. It appends exact closing-ineligible `reconciliation_blocked` evidence, conditionally blocks only still-owned in-progress members in one R17 batch, stops/proves-dead processes, removes proven-clean worktrees and non-authoritative markers, and retains immutable evidence plus named refs for diagnosis. If tracker contention prevents the batch, it uses the same non-capacity target quarantine as `published_contended`; otherwise it writes a non-capacity diagnostic pointer that does not block an unrelated target. It then CAS-clears `A` and releases `Q` under the ordered locks. Crash tests cover conflict detection, member batch, pointer transition, `A`, and `Q`; no conflict path permits closure or leaks capacity.

    The orchestrator closes landed Beads in total order only after passing gate evidence and the final closing-eligible publication receipt name the exact published HEAD, fingerprint set, authority cursors, and original member set. Before each close it acquires the R17 Beads authorizer and canonical repository lock, obtains fresh `show` and `history` through that ticket, and requires `status:"in_progress"` plus the cohort's exact session-unique assignee/run identity, scheduling fingerprint, and authority cursor to equal the exact values bound in the publication receipt. It never adopts a newer "stable" cursor. The only mutation form is `<absolute-bd> close --if-revision <receipt-bound-cursor> --actor agentic:cohort:<cohort-id> --reason published:<receipt-sha256> --json -- <id>`, with the opaque ID as one argv element after `--`. Any pre-close mismatch enters quarantine before invoking close. A foreign field, metadata, dependency-endpoint, or supersession event, including change-and-restore ABA from an older client, advances the authority cursor and makes close conflict without mutation. Fresh post-close `show` and history must expose the next cursor and a suffix containing exactly the one close event by that actor/reason and no intervening event. An ambiguous connection is accepted only when that exact cursor transition/event exists. An already-closed issue is idempotent only when the same receipt-bound transition already exists.

    Any close conflict or owner change enters `published_contended` with a durable per-member ledger of already proven closes and the same quarantine/permit-release protocol; it retains authoritative markers for the contended member, never overwrites external authority, and does not attempt later cohort closes. Claim/inflight markers for successfully closed members are removed only after their proof. Every seal, landing record, main/diagnostic-ref CAS, gate record, target-ref CAS, publication receipt, conditional Bead close, marker removal, quarantine, and cleanup step is idempotent; crash-injection tests cover both sides of each boundary. On the ordinary path integration refs and `A` remain reachable until every landed member is authoritatively closed and every excluded member's tracker/marker action is complete; cleanup then clears `A` and releases the exact runtime/repository `Q` reservation last under the ordered admission locks. Closing-ineligible terminal paths instead preserve immutable refs/evidence through non-capacity diagnostic or quarantine pointers while still clearing `A` and releasing `Q`.

21. R21: Four session-sized Bootstrap Tasks 00A–00D own the missing Beads authority layer; no current behavior is assumed. Three ordered patch fragments are generated against Beads v1.1.0 commit `8e4e59d39f3459a43cf21a3236a13eca4dd874f7` and applied by the checked-in provider-fragment apply/build helper owned by 00A. This provider helper is distinct from the pre-registration control bundle defined below. Task 00A owns `beads-authority-core.patch`, the deterministic fragment apply/build helper, and its tests: no-migrate backend identity, core/full schema-install transactions, storage-enforced uniqueness of nonempty external refs, guarded complete issue+initial-edge create and guarded external-ref update, one narrow expected-state bootstrap finalize, base/core/full handshakes, and embedded/server migration serialization. The narrow finalize exists only to close, canonicalize, and attach 00A after its own reviewed core binary is published and its core schema is installed; it does not expose the general conditional authority owned by 00B. Task 00B owns `beads-authority-conditional.patch`: the authority revision advanced by every fingerprint-relevant field, metadata, and incident-dependency mutation plus revision-conditional single/multi-issue transactions and actor-bound history. Task 00C depends on 00B and owns `beads-authority-supersession.patch`: supersession/redirect cursor movement and history on B's authority substrate, transactional current-dependent redirection, and future older-client redirect/rejection. Task 00D depends on 00C and owns the toolkit authorizer/adapters plus completion and certification of the migration driver's real-provider inspection, per-primitive receipt, recovery-snapshot, and terminal-bootstrap-receipt boundary; it changes no Beads storage or patch tooling and does not own migration graph or release semantics. The helper proves the fragments apply in exact A/B/C order. These bootstrap tasks are intentionally serial because their provider schema/history contracts are coupled; the main implementation graph still admits same-file parallel workers wherever dependency/decision edges allow it.

    The patched binary has three bootstrap commands. `bd authority identity --no-migrate --json` performs no schema write, auto-upgrade, repository initialization, or history append and returns the bounded backend/database/project/repository identity plus current base/core/conditional/full schema fingerprints. `bd authority bootstrap-finalize --request <canonical-json-file> --json` accepts only schema `agentic.bd-bootstrap-finalize/v1`; the request binds repository identity, issue ID, exact bootstrap definition/metadata hash, intent/run IDs, controller actor/reason, expected `status:"in_progress"`, exact assignee, and `external_ref:null`, plus the exact after-state `status:"closed"`, canonical external ref, and nonblocking container relation. After core installation it compares and writes that complete transition plus actor-bound history atomically, consumes one unique finalize receipt, and is idempotent only for that receipt; any foreign field, assignee, status, ref, relation, or history movement rejects without mutation. It cannot update another issue or express a general transaction. `bd authority install --profile core|conditional|full --migration-id <digest> --migration-host <digest> --if-schema <digest> --actor <actor> --json` acquires backend-native migration serialization and applies or verifies the named pinned schema in one storage transaction. Core installation, available after 00A, installs only identity, external-ref uniqueness, guarded create/ref update, the one-shot bootstrap-finalize transaction, and the install receipt needed to register 00B–00D safely; it does not advertise the R17 conditional or supersession profiles. Conditional installation, available only after A+B publish, adds 00B's general revision/history transactions but not supersession. Full installation, available after A+B+C publish, upgrades conditional to all three R17 profiles.

    Embedded mode combines the canonical OS migration lock with the database transaction. Server mode additionally acquires a database-scoped advisory migration lock keyed by database/project/migration ID, so clients on hosts with different R8 roots serialize in storage. Each transaction first scans the fields relevant to its profile; a duplicate external ref, inconsistent redirect, unsupported schema, or non-representable history rolls back with a typed incompatibility instead of repairing data. A committed install records profile/schema digest, migration ID/host, actor, prior fingerprint, exact before/after counts, and fragment digests in one unique storage receipt. For this registration migration, later operations require the same host identity; another host fails before mutation and v1 has no transfer. Crash before commit leaves the prior schema; crash after commit is recognized only by the exact receipt and post-schema verification. Ordinary patched commands never auto-migrate and fail with `authority_core_missing` or `authority_schema_missing` as applicable. At full profile, older supported clients remain usable, but storage constraints/triggers advance endpoint authority revisions and enforce uniqueness/redirect behavior for their writes. The patch adds no task/lease store and does not change ordinary readiness semantics.

    For ordinary production repositories, Task 00D exposes only `agentic bd-authority install --repo <physical-repo> --confirmed --json`. It performs the no-migrate identity read, shows the exact trusted binary/database/prior/full-schema identities before confirmation, takes the R8 and backend-native locks, calls the full install with a repository-scoped migration ID, and re-verifies the unique receipt/profiles. It never repairs incompatible data and has exact ambiguous-connection recovery. `agentic live --check` is read-only and reports `authority_schema_missing` until this explicit command succeeds.

    Task-local acceptance is nonempty and independently runnable with the 00A-owned helper. `test_beads_authority_core.sh` applies only A and tests no-migrate identity, core install/recovery, uniqueness, guarded creation/ref update, server locking, and the raw-client barrier. `test_beads_authority_conditional.sh` applies A+B and tests authority cursors, conditional single/batch operations, history, ambiguity, and older-client edge/metadata ABA. `test_beads_authority_supersession.sh` applies A+B+C and tests redirect cursor/history and older-client races. `test_beads_authority_provider.sh` applies A+B+C, runs the complete R17 matrix and full upstream gate, and emits the absolute binary, SHA-256, schema/fragment digests, and receipt consumed by 00D and migration. In that checkout the full gate separately runs `go build ./...`, `go vet ./...`, `go test -race ./...`, `golangci-lint run ./...`, and `go mod tidy` followed by `git diff --exit-code -- go.mod go.sum`.

    Migration accepts only the exact final helper output through Task 00D's authorizer or a released artifact matching `trusted-beads-releases-v1.json`; it never uses ambient `bd`. The allowlist binds version, 40-hex build commit, OS, architecture, artifact SHA-256, schema/profile majors, and upstream checksum-manifest provenance. Production live, cohort closure, and cutover remain disabled for an unlisted binary even if it self-reports a handshake. The upstream PR/release is external state; development and registration repair use the pinned fragments without fabricating a release.

## Ownership boundaries

| Surface | Owns | Must not own |
| --- | --- | --- |
| Mardi Gras | Bead browsing/detail, explicit launch intent, confirmation, activity rendering, PTY/tmux, ephemeral pane handles | Claims, worktrees, retries, verification, closure, recovery |
| `agentic launch/supervise` | Target validation, pointer-only runtime argv, immutable dispatch and process lifecycle | Claiming, issue prose interpretation, worker orchestration, tracker lifecycle |
| `agentic claim` | Short canonical-repository ready/status check, Beads claim, existing claim marker | Persistent ownership, scheduling, repair, requeue, worker launch |
| `agentic event` | Existing append-only run/process correlation records | Authorization, claims, workflow gating |
| `agentic activity` | Read-only evidence join and bounded state projection | Mutation, repair, requeue, liveness guessing, an independent trace protocol |
| Skills | Screening, atomic claims, worktree isolation, implementation, verification, closure, discoveries, recovery | TUI presentation |
| Beads | Canonical task, dependency, readiness, claim, and status state | Runtime process truth |
| Legacy Workboard | Read-only cross-repository inventory, session, and cost view after production cutover | A second launch, mutation, recovery, or repository-scoped control UI |

## Out of scope

- Reimplementing Mardi Gras's Beads browser, dependency graph, or detail view in this repository.
- A permanent Mardi Gras fork or vendored copy. If upstream declines the provider, ship a toolkit-owned companion using the same protocols.
- A second admission/lease database, UI-owned claims, queue scheduling, worktrees, verification, closure, orphan repair, or automatic retry.
- Generic kill, automatic recovery, remote-host agents, deployment, PR creation, or publishing.
- Projecting agents into normal or infrastructure Beads.

## Acceptance criteria

| Journey | Runnable evidence |
| --- | --- |
| Targeting and prompt safety | `python3 -m pytest tests/test_agentic_launch.py -q -k 'TargetResolution or PromptContract'` proves physical containment, authored-file shapes, exact refs, pointer-only prompts, argv execution, and malicious tracker/path rejection, including imported or forced issue IDs outside R2's launch grammar (R2, R3, R6, R12). |
| Supervisor and immutable package | `python3 -m pytest tests/test_agentic_launch.py -q -k 'SupervisorTopology or PackageLifecycle or RuntimeSupply or LoaderClosure or ProcessIdentity'` proves fast fresh prepares, the atomic one-shot prepared→starting transition, retry rejection before spawn, inherited PTY FDs, tmux/foreground plans, signal forwarding, reaping, dashboard independence, exact shared process-start/boot fixtures, crash evidence, boot/clock handling, plugin-cache pruning, resolver upgrade, retained package use, and atomic records. It verifies the closed supplier/checksum allowlist, hostile archive rejection, complete normalized runtime inventory, Linux native-file closure, Darwin standalone/shared-cache identity, and drift failure. Two independent builds from the same committed inventory yield identical manifest bytes/hash despite shuffled traversal; byte, mode, inventory, supplier artifact, version, or source changes alter identity; member tampering and a same-version identity collision fail closed at package-current, prepare, supervise, canary merge, and cutover (R4–R8). |
| Beads race boundary | `python3 -m pytest tests/test_agentic_claim_races.py -q` races UI work/build, direct work, drain, and a barrier-controlled raw human claim from separate linked worktrees; proves session-unique actors make exactly one verified claimant proceed, every loser stops before edit/prompt dispatch, and the path performs no Git/JSONL operation. It covers exact same-run repair, open+fresh-ready atomic claim, every losing state, and the opaque-ID drain envelope. Embedded/server and two-`bd` PATH fixtures prove one resolved fingerprinted executable/ticket, no lease/heartbeat/reclaim, end-of-options safety, and correct ambiguous-success/error post-reads. Behavior fixtures also certify monotonic authority/history cursors, conditional single/multi-issue update/close/dependency success and conflict, actor/reason atomicity, incident-edge and metadata ABA rejection including raw older-client writes, ambiguous-connection recovery, and before/during/after supersession dependency redirect/rejection. Missing conditional/supersession capability, binary drift, foreign cursor movement, and unknown schemas fail closed. Crash cases cover claim-before-marker, requeue-before-marker-removal, and dead-runtime/CLI-absent fallback with empty assignee before a distinct run (R1, R4, R9, R17). |
| Activity correctness and safety | `python3 -m pytest tests/test_agentic_activity.py tests/test_agentic_events_v2.py tests/test_agentic_child_activity.py -q` covers exact/possible/unknown correlations, the shared process-start/boot fixtures, reboot/PID reuse, malformed/future/stale markers, closed-versus-live records, branch-prefix rejection, public-data bounds, hung-source deadlines, sequence echo, and read-only operation. Claude Workflow, Codex collaboration, and Antigravity fixtures emit queued/started/terminal toolkit-child lifecycles; normalized label/kind/status/elapsed/worktree/summary rows cover running, queued, completed, and failed children, while a crashed indeterminate child becomes `unknown`. No transcript or arbitrary output tail is read. Tests also prove ad-hoc and cross-repository native agents remain fleet-owned and are not falsely projected into repository activity. Old strict packages never open v2; new readers merge v1/v2; a UI-losing/direct-winning race cannot inherit the direct run; and a UI winner joins only on exact dispatch/run/PID/start/current-boot evidence (R8, R10–R12, R16, R17). |
| Native façade parity | `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/run-native-facade-matrix.sh` resolves and verifies the installed package, fingerprints each exact runtime executable, runs Claude Code and Codex with `work,build,drain`, runs Antigravity with `work,build`, proves unsupported Antigravity drain/resume fail before spawn, and atomically writes the complete package/runtime-bound façade report. Cross-package and same-runtime cross-fingerprint merges fail, while a changed fingerprint atomically resets that runtime's matrix (R9, R11, R15, R17). |
| Live runtime activation | `MANUAL_PENDING=1 bash specs/mardi-gras-agentic-integration/tests/run-runtime-canary-matrix.sh` runs `runtime-canary.sh claude work build drain`, `runtime-canary.sh codex work build drain`, and `runtime-canary.sh antigravity work build`, then asserts separate Antigravity drain and resume invocations return the documented unsupported-mode code before spawn. Prepare accepts only the canaried fingerprint and records its absolute executable; supervise invokes that path and a path/byte/version swap fails before spawn (R1, R3, R6, R15). |
| Install and protocol lifecycle | `bash specs/mardi-gras-agentic-integration/tests/install-lifecycle.sh` uses isolated account/state/PATH fixtures for canonical package, self-contained runtime, loader-closure, inventory, and manifest construction; stable resolver ownership; full member verification; package/plugin identity; valid handshake; `/usr/bin/mg`; dependency/version mismatch; stdlib, extension-module, and loaded shared-library swaps; OS/loader drift; trusted and untrusted release digests; patch-only rejection; plugin-cache pruning; atomic upgrade; same-version collision; referenced-package retention; uninstall with state retained; explicit purge; and CLI-absent direct fallback (R1, R7, R8, R14, R18, R19). |
| Documentation contract | `python3 -m pytest tests/test_agentic_live_docs.py -q && vale docs/guides/agentic-live.md README.md && bash tests/test_doc_links.sh` validates the complete R16 topic map and revision-bound `agentic.documentation-review/v1` artifact, requires the guide/README bytes to match the reviewed revision, and runs deterministic style/link checks (R16). Depth ceiling: the topic map is L1; the independent prose-review and README reader-test verdicts are the judgment complement. |
| Public JSON safety | `python3 -m pytest tests/test_agentic_public_json_contract.py -q` discovers every emitted schema and named JSON report/manifest/evidence artifact, requires the closed inventory to register every envelope, property, dynamic-key family, and string/numeric leaf, and rejects unregistered outputs or unexercised leaves. Exact-byte fixtures cover BOM, surrounding whitespace/trailing LF, member order, duplicate names, `\/`, `\u`, unnecessary escapes, aggregate/depth/cardinality caps, non-NFC and forbidden Unicode, plus signs, leading/negative zero, fractions, exponents, lossless uint64 boundaries, and every numeric class's inclusive bounds (R12). |
| Beads authority provider | `bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_core.sh && bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_conditional.sh && bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_supersession.sh && bash specs/mardi-gras-agentic-integration/tests/test_beads_authority_provider.sh` verifies the three ordered fragments against exact Beads commit `8e4e59d39f3459a43cf21a3236a13eca4dd874f7`; runs the task-local core, conditional/history, supersession/legacy, embedded/server, install/recovery, raw-race, and complete R17 matrices; proves no implicit preflight migration, storage-enforced uniqueness/future redirect/endpoint-cursor movement against older clients, different-host server rejection, and crash recovery; passes the full Go build/vet/race/lint/tidy-diff gate; and emits the pinned final binary/digests used by 00D and migration. A self-reported or untrusted production binary fails (R1, R9, R17, R21). |
| Mardi Gras provider | `bash specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh` verifies/applies the checked-in patch against exact commit `70e36ff5f180073864163e39739324c9fbec989e`, then runs `go test ./internal/agent ./internal/app ./cmd/mg -run Agentic -count=1`. The tests prove exact canonical handshake/control bytes and argv schemas, confirmations, issue/drain separation, every legacy launch entrypoint entering the provider, direct prompt/kill/recover suppression, single-flight polling, sequence rejection, last-good retention, selection preservation, pane switching, and terminal cleanup (R10, R13, R14, R18). |
| End-to-end terminal flow | `bash specs/mardi-gras-agentic-integration/tests/e2e-provider-pty.sh` obtains the patched pinned `mg` through the R18 helper, then exercises drill-down, issue launch, a UI/direct/drain/raw claim race, drain cancellation/confirmation, direct run-event appearance, source slowdown, state transitions, tmux switching, foreground suspension, runtime crash, dashboard quit/restore, and alternate-screen refresh with no scrollback growth (R1–R18). |
| Legacy cutover | `bash specs/mardi-gras-agentic-integration/tests/workboard-cutover.sh` proves absent, malformed, patch-only, stale-package, stale-build, and runtime path/digest/version/OS/architecture drift preserve existing Workboard controls. An exact released-build/package/canary/terminal receipt removes only Workboard mutation/dispatch actions; both browser routes retain cross-repo inventory/session/cost content, each repo card names `agentic live`, the independent fleet skill/entrypoint and plugin/marketplace promises remain byte-present and route session-local agent requests as before, and agent-console/package-entrypoint checks remain green (R16, R19). |
| Worktree integration | `python3 -m pytest tests/test_drain_worktree_integration.py -q` varies completion order among overlapping workers in one dependency-ready antichain; atomically enforces one account-global ledger with per-runtime and per-repository filtered caps across different runtimes/repositories/targets, including cross-runtime crash-after-Q, Q-only unknown-token recovery, killed holders on both sides of `Q/A`, and capacity scans after A rotation; proves a dependent starts only in a later published-and-closed wave and newly required work emits a typed authored-path/hash/downstream-edge action whose guarded complete create-plus-initial-edge transaction exposes one immutable dependent definition only to a later fresh wave, never by mutating the registered definition or sealed cohort; orders generic issues, unnumbered tasks, and duplicate numbers deterministically; races worktree administration while existing workers run; races two sealers and crashes after every `Q/A/P/N/R/C/K` boundary, including `K` before first claim; exercises current-owner rotation, dynamic issue/dependency/field changes through gate/publication/close barriers, atomic composite-group disposition, published contention quarantine/capacity release, capacity-bound direct quarantine reconciliation, and current-target revalidation/gate/new receipt; injects conflict/group-transition, target-reconciliation conflict, and gate-isolation failures; varies Git/object/ref formats, inherited configuration, replacement objects, worker-added/custom/drifting attributes, tracked/staged/untracked/ignored/submodule dirt, and multiply checked-out targets; prunes unreferenced prepared and diagnostic objects before recovery; exercises noncolliding exact refs, all four publication crash states, deterministic same-cohort reconciliation, exact receipt-cursor close ABA/connection races, and crash recovery through marker/ref/worktree/active/quarantine/permit cleanup (R20). |
| Immutable repair migration | The pre-00A source gate runs `python3 -m pytest tests/test_mardi_gras_registration_migration.py -q -k "not provider_integration"` against the strict fake authority to prove closed manifests, exact low-level action plans, per-primitive crash recovery, canonical terminal-bootstrap receipt consumption, distinct bootstrap/final commit identities, and closed authority snapshots/storage receipts without pretending the future provider exists. After 00D, the final source gate runs `MARDI_AUTHORITY_BINARY=<exact-reviewed-A+B+C-binary> python3 -m pytest tests/test_mardi_gras_registration_migration.py -q -k provider_integration` against isolated embedded and single-attested-host server-backed bd fixtures plus concurrent ready/claim/dependency/update probes at every mutation boundary. The latter proves owner-bound crash recovery for no-ref 00A intent/create/claim-dispatch/finalize, prepared/committed profile installs, storage-guarded serial creation and progressive finalization of 00B–00D, and full-schema upgrade; a barrier-controlled raw canonical-ref race cannot duplicate or mutate a foreign issue and enters exact human-conflict state without inventing a Bead or terminal receipt; original definitions are never replayed; replacements have pending guard state before complete; Task 01's authored definition, live acceptance, and notes remain byte-identical while a conditional batch adds only its 00D dependency/relation conversion; every ordinary graph mutation is cursor-conditional; the mandatory and arbitrary consumers added before/during/after supersession receive replacement blockers plus old historical relations through the redirect rule; divergent environments, same-host lock convergence, and different-host server rejection hold; crash/rerun validates both content-addressed evidence chains after every primitive and every event/head/schema/tracker boundary; receipt substitution and partial/shallow snapshots fail closed; foreign Task 01 updates lose no authority to release while a legitimate immediate claim is recovered; attestation/date/HUMAN digests and unique READY review are mandatory; Tasks 26/27 remain blocked; and terminal state has canonical refs for 00A–00D, one replacement per ref, one supersession/redirect per historical issue, one exact release cursor/event, and one released receipt (R17, R19–R21). |
| Project gates | `bash specs/mardi-gras-agentic-integration/tests/project-gates.sh` runs `bash scripts/check.sh` in the toolkit; obtains and patches exact Mardi Gras commit `70e36ff5f180073864163e39739324c9fbec989e` and exact Beads commit `8e4e59d39f3459a43cf21a3236a13eca4dd874f7`; and in each applicable checkout separately runs `go build ./...`, `go vet ./...`, `go test -race ./...`, `golangci-lint run ./...`, plus `go mod tidy` followed by `git diff --exit-code -- go.mod go.sum`. |

`tests/mardi-integration-task-tests-v1.json` is a staged ownership manifest
with integer `complete_through` and boolean `final`. Tasks 28–36 advance
`complete_through` monotonically from 28 through 36 with `final:false`.
At each such stage, `python3 -m pytest
tests/test_mardi_integration_task_partition.py -q` requires equality between
the collected integration node IDs and the manifest union; exact one-task and
one-family ownership for every collected node; no duplicate, unowned, extra,
substring-only, or drifting match; and the exact nonempty task/family sets
only for Tasks 28 through `complete_through`. Any marker or manifest entry for
a future task/family fails, so placeholder tests cannot satisfy an
intermediate stage. Task 37 alone sets `complete_through:37` and `final:true`;
that state additionally requires the exact complete Task 28–37/family table
below, every task and family nonempty, and no missing or additional family.
Each task runs the partition check plus every one of its following commands
separately:

- Task 28: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task28 -k seal_admission`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task28 -k active_pointer`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task28 -k capacity_admission`.
- Task 29: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task29 -k credential_ownership`.
- Task 30: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task30 -k git_capability`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task30 -k deterministic_objects`.
- Task 31: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task31 -k landing_journal`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task31 -k prune_reconstruction`.
- Task 32: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task32 -k workset_change`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task32 -k conflict_group`.
- Task 33: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task33 -k gate_isolation`.
- Task 34: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task34 -k target_publication`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task34 -k publication_drift`.
- Task 35: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task35 -k target_reconciliation`.
- Task 36: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task36 -k authority_close`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task36 -k marker_cleanup`.
- Task 37: `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task37 -k workset_extension`; `python3 -m pytest tests/test_drain_worktree_integration.py -q -m mardi_task37 -k terminal_cleanup`, followed by the unfiltered Worktree integration command.

## Design alternatives

Chosen: a narrow Mardi Gras provider with toolkit launch and observation protocols. Launch starts the existing skill; Beads arbitrates work.

Rejected after adversarial review: an `agentic admission` lease/provenance broker. Reserving work before runtime startup creates capability custody, heartbeat transfer, and unrecoverable cross-store windows around the Beads claim and marker files. Strengthening the existing claim-time lock compensates for Beads' same-assignee idempotence without becoming durable ownership; after the lock exits, only Beads matters. A losing runtime exiting before edits is simpler and safer.

Chosen for conditional close and migration: a narrow upstream Beads storage
patch rather than a toolkit shadow database or advisory-only lock. Revision
compare-and-swap, actor-bound history, and supersession redirects remain one
transaction in the canonical tracker, including against older clients. The
pinned patch makes development and the one-time repair reproducible; production
waits for an allowlisted upstream artifact.

Runner-up: unmodified Mardi Gras beside a separate tmux activity pane. It cannot route launch actions through the toolkit skills and splits one developer task across two interfaces.

Research supports a programmatic coordinator rather than a peer-message
free-for-all. The [OpenAI Agents SDK orchestration
guide](https://openai.github.io/openai-agents-python/multi_agent/) recommends
code-driven orchestration when predictability, speed, and cost control matter,
while retaining parallel fan-out for independent work. Anthropic's
[production multi-agent research
write-up](https://www.anthropic.com/engineering/multi-agent-research-system)
uses an orchestrator-worker pattern with explicit delegation and evaluation
and notes that software tasks expose less safe parallelism than broad research.
R20 follows that boundary: the graph and coordinator choose independent
workers; agents may research or review in parallel but do not negotiate
ownership or merge authority through chat.

Gas Town's fielded Refinery validates capacity-bounded worktree fan-out, sequential integration, merge-slot serialization, and batch failure isolation. Those mechanisms informed R20's capacity cap, short worktree-administration critical section, and deterministic batch classifier. Gas Town is not a runtime dependency: its documented merge paths are not one revision-bound correctness contract, and this feature additionally requires deterministic commit bytes, per-ref compare-and-swap, publication-before-close, and checked-out-target recovery.

MCP Agent Mail is an optional communication/audit layer, not an ownership or merge primitive. Its file reservations are advisory and intentionally discourage overlapping edits, while this design permits same-file execution in isolated worktrees and resolves compatibility at integration. Runtime-native messages or Bead-ID-keyed comments may carry bounded contract-change, blocker, review, or recovery notices; a notice must be reflected in Beads or cohort evidence before it changes scheduling. Beads formulas/molecules remain candidates for later reusable workflow templates, but they do not replace the live integration state machine or duplicate its tracker state.

Beads itself remains the durable ledger, not the workspace scheduler. Its
[multi-agent coordination
guide](https://github.com/gastownhall/beads/blob/e2dd121f4ffce8a47c105b99708287a9c071de87a/docs/multi-agent/coordination.md#L100-L125)
and [worktree
reference](https://github.com/gastownhall/beads/blob/e2dd121f4ffce8a47c105b99708287a9c071de87a/docs/reference/worktrees.md#L6-L28)
support shared tracker state across isolated workers. A real [worktree setup
discussion](https://github.com/gastownhall/beads/discussions/2798) also shows
that discovery and redirect behavior has caused operator confusion. The
coordinator therefore owns and verifies worktree administration explicitly
instead of asking workers to infer it.

The independent `fleet` skill remains the session-local native inventory.
R10/R11 deliberately cover a narrower population—toolkit-orchestrated
children in the selected repository—with stronger durable correlation.
Ad-hoc and cross-repository agents may be visible only through native harness
metadata, so this feature must not remove fleet, its generated entrypoint,
routing claims, or marketplace copy.

Flip condition: if upstream Mardi Gras declines a generic provider interface, retain `agentic launch/activity` and ship a toolkit-owned companion; do not maintain a long-lived fork.

## Parallelization

Dependency and decision coupling—not file overlap alone—control execution
admission. Every dependency-ready writer receives its own branch and Git
worktree. Two tasks may execute concurrently even when their `Touch:` sets
overlap, provided the spec has already fixed any shared schema, name, package
identity, or interface decision. The process-start/boot grammars and shared
fixture above remove the former launch/event decision race. Worktree isolation
makes overlapping execution safe from overwrite; it does not make the results
automatically mergeable. Only short shared-repository administration is
serialized; creating/removing/repairing/pruning worktrees cannot race, while
all work inside already-created worktrees remains parallel.

Each cohort contains exactly one dependency-ready antichain from one fresh
ready scan and selects only the deterministic prefix allowed by native,
profile, and hard capacity caps. Its completed branches enter one deterministic
integration queue ordered by canonical spec identity, optional authored task
number, external ref, and bd issue ID. Generic issues, unnumbered tasks, and
the same number in different specs remain valid repository-drain members. A
dependent is eligible only after the predecessor cohort publishes and closes
and a new ready scan seals the next wave. Before each landing, the integrator
runs the exact R20 `merge-tree`/deterministic-`commit-tree` construction and
compare-and-swap advances the durable integration ref. A conflict stops
automatic landing: one designated integration worktree reconciles the branch
without auto-selecting ours/theirs, then repeats review and tests. Remaining
completed branches are re-evaluated against the new integration HEAD. The
repository canonical gate runs once on the full integrated set in the normal
case, not inside every parallel worker. On failure, bounded ordered bisection
rebuilds candidate stacks from immutable branches, blocks only isolated
culprits when possible, and requires one final full gate on the accepted
subset. The gated HEAD is published through the locked,
checked-out-worktree-aware fast-forward protocol before any Bead closes;
target movement enters one bounded, evidence-linked reconciliation generation
under the same cohort ownership instead of overwriting or minting a successor.

The default coordinator remains programmatic: bd owns dependencies, verified
atomic claims, and recovery; code owns capacity, fan-out, join, ordered
integration, retry bounds, and gates. Peer messaging is reserved for bounded
research/review panels and typed exception notices such as a discovered
contract change, blocker, or recovery handoff. It does not replace the task
ledger, carry merge authority, or coordinate routine writers; any notice that
changes execution becomes durable Beads or cohort evidence first. LangGraph,
the OpenAI Agents SDK, Gas Town, and Agent Mail add no missing
workspace-merge primitive here and would duplicate orchestration, durable task
state, or both.

The repaired breakdown begins with the narrow serial 00A core, 00B
conditional/history, 00C supersession, and 00D toolkit-authorizer bootstrap.
After the guarded
registration migration releases retained Task 01, it continues with two parallel foundations:
worktree-administration/profile-capacity primitives and
runtime/package/process identity. Ten
session-sized integration tasks then add seal admission, credential ownership,
deterministic object construction, landing journals, dynamic-workset and
conflict-group handling, gate isolation, publication, same-cohort
reconciliation, authority closure, and terminal cleanup in dependency order.
Strict claim and event
evolution may afterward run concurrently in worktrees. Claim/requeue façade
migration precedes the separate native child-lifecycle/canary task. Reproducible
package/runtime/resolver installation may proceed independently of activity,
while live activation/canaries wait for the installed package, activity
surface, and pinned provider/allowlist. Launch/supervisor, receipt, terminal, documentation, and
Workboard stages follow only their explicit interface dependencies. All
packaged skill, profile, and manifest changes land before installed-package
canaries. Released-provider certification remains manual-pending and gates no
implementation task.

## Pre-registration control bundle

The explicitly user-authorized repair/breakdown session owns one deliberately
out-of-band source deliverable because that deliverable creates the first
Bootstrap Bead and therefore cannot depend on a Bead that does not yet exist.
This exception is source-scoped and ends at source attestation; it grants no
untracked tracker authority and cannot implement provider or product behavior.
Its exact owned paths are:

- `specs/mardi-gras-agentic-integration/bootstrap-registration.py`
- `specs/mardi-gras-agentic-integration/bootstrap-registration-v1.json`
- `specs/mardi-gras-agentic-integration/bootstrap-00a-workflow.md`
- `specs/mardi-gras-agentic-integration/migrate-registration.py`
- `specs/mardi-gras-agentic-integration/registration-repair-v1.json`
- `specs/mardi-gras-agentic-integration/tests/project-gates.sh`
- `specs/toolkit-core-simplification/surface-inventory/mardi-gras-registration-control.json`
- `tests/inventory/mardi-gras-registration-control.json`
- `tests/test_mardi_gras_bootstrap_registration.py`
- `tests/test_mardi_gras_registration_migration.py`
- the exact two Mardi Gras manual-certification lines in `HUMAN.md`

The bundle may validate closed manifests, source containment and hashes,
construct the exact reviewed requests, manage the owner-bound bootstrap and
migration evidence state machines, and invoke only the authority operations
specified below. It must not emulate a missing Beads storage primitive, weaken
a provider handshake, use ordinary `agentic register-spec`, or mutate live
tracker state during its own authoring or critique. Before the source baseline
is eligible for attestation, all of these commands must pass:

This source owner supplies the fake-adapter control tests that can run before a
provider exists. Bootstrap Task 00D is the explicit later owner of the real
`provider_integration` additions to `migrate-registration.py` and
`tests/test_mardi_gras_registration_migration.py`; its immutable definition
requires those tests to use the exact A+B+C binary on embedded and server
fixtures before final migration attestation. That planned sequential ownership
is not a live acceptance rewrite.

```text
python3 specs/mardi-gras-agentic-integration/bootstrap-registration.py validate --config specs/mardi-gras-agentic-integration/bootstrap-registration-v1.json
python3 specs/mardi-gras-agentic-integration/migrate-registration.py validate --manifest specs/mardi-gras-agentic-integration/registration-repair-v1.json
python3 -m pytest tests/test_mardi_gras_bootstrap_registration.py -q
python3 -m pytest tests/test_mardi_gras_registration_migration.py -q -k "not provider_integration"
```

Bootstrap source attestation is separate from the later registration-migration
attestation. The bootstrap source commit contains the complete control bundle,
SPEC, and immutable task definitions with an empty `attestation` object in
`bootstrap-registration-v1.json`. Its direct child changes only that file to
bind the source commit, exact source-config bytes, SPEC, controller, workflow,
and four task hashes plus one bounded independent READY review record. A second
independent whole-bundle READY critique reviews that child. At command start,
`run-00a --reviewed-commit <40-hex>` requires a clean checkout at that exact
child, its parent equal to the bound source commit, and the parent-to-child diff
to contain only the bootstrap configuration. The operator's `--confirmed`
asserts that the second READY critique was received. These bootstrap identities
remain immutable evidence after 00A publishes a newer implementation commit;
they are not reused as the final migration attestation.

Only that reviewed bootstrap child may authorize the human-attended bootstrap
command below. No live Beads mutation occurs merely because these files exist
or their validation gate passes.

## Registration migration

The first registration already created all twelve original child issues,
added the package-bound native-canary issue as a blocker of
`agentic-868.9`, and superseded `agentic-868.8` with the original façade
replacement. Those writes are history and are not repeated.

`specs/mardi-gras-agentic-integration/registration-repair-v1.json` is the
authoritative migration manifest. Its closed schema records the exact
old-to-replacement pairs and graph below; the two known mandatory external
downstream rewires plus the dynamic supersession-redirect policy;
the Bootstrap Task 00A–00D IDs and envelopes, requiring 00A's attested
pre-core `external_ref:null` transition to its exact canonical ref and exact
canonical refs for 00B–00D; feature-container ID `agentic-j01`; the exact P0
creation envelope for all 27 replacement Tasks 13–39. To avoid a second prose
authority, each manifest entry stores the source path and exact dependency
tokens; the closed validator expands the attested task bytes into title,
goal-derived description, task type, external ref, nonblocking related
container, priority, budget, rigor, source, sorted Touch, canonical definition
hash, and pending registration state and rejects any mismatch. It also records a 40-hex
`source_commit`; an exact `source_date_utc`; the
SHA-256 of `SPEC.md`; the SHA-256 of each committed HUMAN entry; and canonical
registrar `definition_hash` values for Bootstrap Tasks 00A–00D, Task 01, every historical Task 02–12
file, and every one of the 27 replacement Task 13–39 files. Unknown keys, missing entries,
duplicate refs, container/priority/metadata drift, or any hash mismatch fails
closed. The exact old-to-replacement pairs
are:

| Existing external reference | Replacement external reference |
| --- | --- |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/02-build-launch-supervisor.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/15-build-launch-supervisor-v2.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/03-evolve-run-events-v2.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/16-evolve-run-events-v2-repair.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/04-instrument-native-facades.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/38-instrument-child-lifecycle-canaries.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/05-project-live-activity.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/18-project-live-activity-repair.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/06-package-and-launch-live.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/39-activate-live-runtime-canaries.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/07-prove-installed-native-facades.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/26-prove-final-installed-native-facades.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/08-implement-cutover-receipt.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/20-implement-cutover-receipt-repair.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/09-add-mardi-gras-provider.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/21-add-mardi-gras-provider-repair.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/10-prove-terminal-journeys.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/23-document-agentic-live-repair.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/11-make-workboard-read-only.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/24-make-workboard-read-only-repair.md` |
| `spec-task:specs/mardi-gras-agentic-integration/tasks/12-certify-production-cutover.md` | `spec-task:specs/mardi-gras-agentic-integration/tasks/27-certify-production-cutover-repair.md` |

Bootstrap Task 00A owns R21's core storage/install fragment and shared patch
helper. Bootstrap Task 00B depends on 00A and owns conditional/history; 00C
depends on 00B and owns supersession/legacy; 00D depends on 00C and owns the
toolkit authorizer, schema-install client, and conditional adapters. All close
before full migration.
Task 01's authored definition, registered hash, live acceptance, and notes
remain unchanged while its live Bead gains Task 00D as a blocking dependency.
New Tasks 13, 14, 23,
and 25 respectively own worktree-administration primitives and declared
profile-capacity parsing,
runtime/package/process identity,
documentation, and the final immutable package freeze. Tasks 28–37 are the
session-sized integration chain: Task 28 owns seal admission, the active
target pointer, capacity, and prepared membership; Task 29 owns credentials,
liveness, commit, resume, and takeover; Task 30 owns Git capability and the
private deterministic object-construction environment; Task 31 owns member
landing journals, commits, integration-ref compare-and-swap, and recovery;
Task 32 owns typed workset-extension construction, conflict reconciliation,
atomic landing groups, and final member dispositions; Task 33 owns canonical gates and
ordered failure isolation; Task 34 owns checked-out-target publication and
its four crash states; Task 35 owns target-movement reconciliation; Task 36
owns revision-conditional closure and marker cleanup; and Task 37 owns
guarded workset-extension consumption, quarantine reconciliation, terminal
ref/worktree cleanup, active-pointer/permit release, and the full integration
gate.
Replacement Task 17 owns claim/requeue façade migration; Task 38 owns native
run/child lifecycle instrumentation and the hermetic façade-canary merger.
Task 18 owns normalized repository child-agent activity. Replacement Task 19
owns reproducible package/runtime/resolver construction and isolated
installation; Task 39 owns live activation and runtime canaries. Task 24 owns
receipt-gated Workboard read-only cutover while preserving fleet; Task 25
freezes the resulting package/manifests. The manifest records this exact
replacement graph:

- Bootstrap Task 00B depends on closed 00A, 00C depends on 00B, and 00D
  depends on 00C through their storage-guarded creation transactions.
- Retained Task 01 depends on closed Bootstrap Task 00D in live Beads state;
  its authored `Depends on: none` line remains immutable provenance.
- Task 13 depends on Task 01.
- Task 14 depends on Task 01 and may run concurrently with Task 13.
- Task 28 depends on Tasks 01, 13, and 14.
- Task 29 depends on Tasks 01 and 28.
- Task 30 depends on Tasks 01 and 29.
- Task 31 depends on Tasks 01 and 30.
- Task 32 depends on Tasks 01 and 31.
- Task 33 depends on Tasks 01 and 32.
- Task 34 depends on Tasks 01 and 33.
- Task 35 depends on Tasks 01 and 34.
- Task 36 depends on Tasks 01 and 35.
- Task 37 depends on Tasks 01 and 36.
- Tasks 15 and 16 each depend on Tasks 01, 14, and 37.
- Task 17 depends on Tasks 01, 14, 16, and 37 plus toolkit-core Tasks 03, 04,
  and 07.
- Task 38 depends on Tasks 01, 14, 16, 17, and 37.
- Task 18 depends on Tasks 01, 15, 38, and 37.
- Task 19 depends on Tasks 01, 14, and 37.
- Task 39 depends on Tasks 01, 14, 18, 19, 21, and 37.
- Task 20 depends on Tasks 01, 39, and 37.
- Task 21 depends on Tasks 01, 18, and 37.
- Task 22 depends on Tasks 01, 21, 39, and 37.
- Task 23 depends on Tasks 01, 22, 39, and 37.
- Task 24 depends on Tasks 01, 20, 22, 23, and 37.
- Task 25 depends on Tasks 01, 24, and 37.
- Task 26 depends on Tasks 01, 17, 25, 38, and 37.
- Task 27 depends on Tasks 01, 21, 22, 24, 25, 26, and 37.
- In one conditional transaction before old Task 06 is superseded,
  `agentic-2nj.5` gains Task 19 as its package-only blocker and its old Task
  06 blocker becomes a nonblocking historical relation. It is therefore not
  enumerated into the general old Task 06→Task 39 redirect.
- `agentic-868.9` depends on Task 26 before the old Task 07 is superseded.

Because registered definition hashes are immutable, this repair never edits
an existing task definition in place. The already blocked, unchanged Task 01
issue is the migration guard: all original descendants already depend on it,
and every replacement definition names it as a prerequisite.

One explicit human-attended additive bootstrap precedes the full migration.
After final SPEC critique/breakdown, the operator runs the checked-in
`specs/mardi-gras-agentic-integration/bootstrap-registration.py` against closed
`bootstrap-registration-v1.json`. That definition document contains exactly
four P0 task envelopes: title, complete description/acceptance, task type,
definition hash, metadata, container, and dependency refs. 00A's task path is
`tasks/00-add-beads-authority-core.md`; its bootstrap issue deliberately has no
external ref before uniqueness exists and instead carries the exact task path
and definition hash in closed bootstrap metadata. The guarded post-core refs
are `tasks/00-add-beads-conditional-authority.md`,
`tasks/00-add-beads-supersession-authority.md`, and
`tasks/00-install-beads-authorizer-bootstrap.md` under the normal
`spec-task:specs/mardi-gras-agentic-integration/` prefix. The latter three
are registered after core: 00B depends on 00A, 00C depends on 00B, and 00D
depends on 00C. Unknown keys, task-byte/hash
mismatch, another dependency, or preexisting 00A explicit ID stops before
create. The configuration also closes every provider response used by this
controller—identity, profile install, bootstrap finalize, guarded create, and
conditional transaction—so missing or additional response members fail before
a receipt can authorize the next mutation.

Before mutation the helper acquires the R8 canonical repository lock and
uses the exact owner-bound content-addressed evidence protocol defined below
under `<R8-root>/bootstraps/<identity-hash>/mardi-gras-agentic-integration-v1/`:
mode-0700 `owners/` and `events/`, immutable mode-0600 owner records, event
files `<sequence>-<sha256>.json`, canonical `head.json`, owner UUID in every
event/temp filename, file/directory fsync, temp/rename/head order, exactly-one
unreferenced-next recovery, and exact-dead-only temp removal. The first durable
`intent_prepared` event binds one UUIDv7, physical pre-core `bd` path/digest,
repository/database identity, all four envelopes, the one deterministic 00A
ID `<current-prefix>-<12-lowercase-hex>` whose suffix is the first twelve
hexadecimal characters of the canonical bootstrap identity digest over
repository/database identity, reviewed bootstrap source commit, source-config
digest, and 00A definition hash, exact argv/request bytes, task/config
hashes, and actor `agentic:registration-bootstrap:<intent-uuid>`. A crash
before its head commit recovers only that same event; no state permits a new
ID. The operator-supplied `--issue` must equal that derived ID. Therefore a
second local or server-connected host can only race the same storage primary
key and must post-read the same envelope; another intent cannot mint a second
no-ref 00A. Every resume rebinds the original physical `bd` path and digest,
runtime executable, repository/database identity, configuration, source
attestation, and task bytes before doing work. Malformed/torn/forked intent,
live or unknown foreign owner/temp state, cross-intent temp state, or an
unclassified event fails closed; only an exactly dead owner permits removal
of its validated temporary files, and recovery advances only one fully valid
next content-addressed event.

The pre-core command is exactly one argv-array invocation of
`bd create --id <id> --title <title> --description <description> --acceptance
<acceptance> --type task --priority 0 --metadata @<canonical-file> --actor
<actor> --json`; it creates only 00A, with no external ref and no dependency
edge. Afterward the helper re-reads ID, fields, bootstrap
metadata, creator actor, exact creation history, and complete absence of
unauthorized edges and appends an
`issue00a_committed` receipt. Thus a raw client has no canonical bootstrap ref
to duplicate.

The checked-in pre-bootstrap command
`python3 bootstrap-registration.py run-00a --intent <uuidv7> --issue <id>
--task specs/mardi-gras-agentic-integration/tasks/00-add-beads-authority-core.md
--runtime claude|codex --reviewed-commit <40-hex> --confirmed` is the only
executable binding for the bootstrap. Its name identifies the single 00A
intent; every rerun resumes that intent and continues through terminal 00D
rather than creating another controller or issue.
Under the repository lock it requires intent ID, contained regular task
realpath/bytes/hash, issue ID/bootstrap metadata, open+fresh-ready state, and
empty assignee; atomically claims as `agentic:bootstrap-build:<run-id>`,
post-verifies that exact assignee, writes an owner-bound envelope, and launches
the selected native runtime without a shell with a pointer-only prompt to the
checked-in bootstrap workflow and task file. The workflow revalidates the
envelope before edits, applies normal build/review semantics, and returns a
typed result. The parent independently runs the task's exact acceptance,
requires a separate diff review, and publishes the reviewed worker commit to
the exact clean launch target only when the recorded target OID is unchanged.
It records the prepared and committed target-ref transition and re-verifies the
published bytes before using that published core binary. Claim loss, task-byte
drift, target movement, crash before/after claim/envelope/child/result/review/
publication, or ambiguous publication has the same post-read and
orphan-recovery rules as R9 and never detaches code work from the Bead.
Bootstrap tests race another claim and inject every boundary.

After `test_beads_authority_core.sh` passes and publication is committed, the
helper prepares, invokes, and commits the exact 00A core-schema install under
backend serialization. Immediately after the unique core receipt verifies,
one prepared/committed `bootstrap-finalize` transaction atomically changes
that same 00A issue from its exact in-progress assignee and
`external_ref:null` state to closed with its canonical `spec-task:` ref,
nonblocking container relation, and actor-bound history. Terminal bootstrap
state never leaves a closed 00A detached. Only then does the helper use
storage-guarded create to register 00B/00C/00D with canonical refs, complete
envelopes, related container, and their serial dependencies atomically.
The same resumable bootstrap controller then uses the identical
claim/worktree/runtime/result/review/publication protocol for the serial
registered 00B–00D Beads. After publishing 00B it installs and verifies the
A+B conditional profile, then closes 00B through that revision-conditional
authority. After publishing 00C it installs and verifies the A+B+C full
profile, then closes 00C through the already installed conditional authority.
After publishing 00D it verifies the toolkit authorizer against that exact
full provider and revision-conditionally closes 00D. Every stage has its own
prepared/committed receipt and rerun resumes the same issue, worktree, target,
profile install, or close rather than creating a successor. Ordinary work or
drain may observe these issues but cannot claim or close a bootstrap issue
whose controller owner/evidence is live. The registration migration cannot
begin until fresh reads prove all four bootstrap issues closed and their exact
provider/authorizer receipts present.

Every bootstrap create/install/edge has prepared and committed evidence and
exact all-before/all-after ambiguous recovery. A raw create raced at any
post-core ref is serialized by storage uniqueness: either the helper wins, or
it records one non-duplicated `bootstrap_ref_conflict` and stops before
creating any later task or terminal receipt; it never adopts, overwrites, or
deletes the foreign issue. The conflict record binds the foreign issue/ref and
exact intended envelope and requires a human to resolve the external authority
through ordinary Beads before rerunning the same intent. It creates no
unauthored issue and cannot mutate 00D. Barrier tests cover helper/raw wins,
00A finalization, every B/C/D ref, and resume after human resolution. Every
provider action response is validated against its closed schema and captured
in evidence; every committed stage is freshly re-observed before the next
mutation. The canonical no-LF mode-0600 terminal receipt remains under R8
`receipts/<sha256>.json` rather than in Git. Its closed
`agentic.registration-bootstrap-terminal-receipt/v1` body binds the earlier
bootstrap source commit and its direct child attestation commit, intent ID and
digest, exact 00A–00D issue IDs, published head, terminal event and predecessor
digests, and the final provider's physical path, executable SHA-256, backend,
database/project/repository identity, and core/full schema fingerprints. The
controller returns its absolute path and digest. Full migration requires that
exact canonical R8 path; a byte-identical owned copy outside its
`bootstraps/<identity>/mardi-gras-agentic-integration-v1/receipts/<digest>.json`
location is rejected. Full migration also requires fresh proof that the
receipt's exact 00A–00D IDs are closed with canonical refs, serial
dependencies, container relations, revisions, actor-bound terminal history,
and provider receipts, plus the exact final provider and authorizer artifacts,
so retained Task 01 authorizes none of its own prerequisites.

The normal `agentic register-spec` command is forbidden for this one repair
because its create-then-edge sequence exposes a transient ready window.
`specs/mardi-gras-agentic-integration/migrate-registration.py` is the sole
live migration entry point. Before attestation or any migration-state
read-modify-write, it obtains the exact R21 patched binary/digest from the
final A+B+C helper through Task 00D (or a trusted released equivalent), invokes
its exact `authority identity --no-migrate` form directly to obtain the core
identity without requiring the full authority schema, and performs no other
tracker read.
Ambient `PATH` and the existing unprofiled `bd` are ignored. Its lock root is
exactly
`<R8-environment-independent-state-root>/locks`; `HOME`, `XDG_STATE_HOME`,
`AGENTIC_STATE_DIR`, and `AGENTIC_DISPATCH_DIR` cannot change it.

The no-migrate identity reply supplies the exact bounded strings
`backend_mode`, `database_identity`, `project_identity`,
`repository_identity`, `core_schema_fingerprint`, and
`full_schema_fingerprint`. The driver serializes the object with exactly those
six keys using R12 canonical JSON, no BOM, surrounding
whitespace, or trailing LF, and computes SHA-256 over those exact bytes. It
opens
`<state-root>/locks/<that-64-lowercase-hex>/registration-migration.mardi-gras-agentic-integration-v1.lock`.
Canonical and linked worktrees for the same repository/database/project must
produce byte-identical identity documents and therefore the same lock;
distinct repository or database identities must differ. Tests race identical
tickets under divergent process environments and require the same lock.
The driver opens the symlink-safe parent at mode 0700 and the mode-0600 lock
with `O_NOFOLLOW|O_CLOEXEC`, acquires one exclusive nonblocking OS lock, and
retains it through the terminal `released` record. A contender returns typed
`migration_busy` before any Beads mutation or evidence append. Process death
releases the lock, after which the next driver reruns the reconciler. The lock
serializes migration drivers on the attested host. For server mode, the
authority-schema install receipt additionally binds one stable
`migration_host_identity`: SHA-256 of canonical OS machine identity, effective
UID, and the physical R8 state-root identity. Another host or state root is
rejected for this migration ID even after schema installation; v1 migration
has no host-transfer path. The storage advisory lock serializes the install,
and that persistent host binding plus this OS lock serializes the remaining
full migration. The guarded creation protocol continues to protect raw
`bd ready` and claim clients.

Immediately after the OS lock, the driver exclusively creates and fsyncs
`owners/<uuidv7>.json` with schema `agentic.registration-migration-owner/v1`,
owner UUID, PID/start/boot identity, machine/host identity, reviewed commit,
binary digest, identity-document digest, and lock-path digest. Every evidence
event records that owner UUID. Temporary event/head files are named
`.tmp-<owner-uuid>-<20-digit-sequence>-<sha256>` and contain the same owner
UUID. On recovery, a current owner may classify only its own temporary files;
an earlier owner's file may be removed only when its immutable owner record
and PID/start/boot observation prove `exact_dead`. Exact-live, unknown,
unbound, malformed, or cross-owner temporary state fails closed.

Migration evidence lives only at
`<R8-state-root>/migrations/<identity-hash>/mardi-gras-agentic-integration-v1/`.
Its mode-0700 `events/` directory contains immutable mode-0600 files named
`<20-digit-zero-padded-sequence>-<sha256>.json`; canonical
`agentic.registration-migration/v1` bytes contain sequence, previous-event
digest or null at zero, phase, idempotency key, manifest/review identities,
and complete before/after payload digests. The filename digest is SHA-256 over
the exact no-LF bytes. A canonical mode-0600 `head.json` names the current
sequence and digest.

Every phase is decomposed into an ordered closed `primitive_requests` array.
For each primitive, and never merely around a group of writes, the driver uses
one deterministic idempotency key and two event kinds:
`operation_prepared` contains the exact primitive, complete before snapshot,
complete intended snapshot, storage receipt, and manifest digest;
`operation_committed` names its prepared digest plus the freshly observed
complete after snapshot and matching storage receipt. A final phase commit
binds the request-array digest and final phase snapshot. Under the migration
lock, append writes and fsyncs a nofollow owner-bound temporary event,
atomically renames it to its final content-addressed name, fsyncs `events/`,
then temp-write/rename/fsyncs `head.json` and its parent. Recovery validates
the complete hash chain from sequence zero. Head at the last valid event
resumes normally; exactly one valid unreferenced next event advances head;
multiple next children, a gap, digest/sequence mismatch, malformed/torn final
file, head outside the chain, or an unknown temporary file fails closed.
Only a temporary file proven to belong to an exact-dead prior migration owner
may be removed after its bytes are classified. Idempotency keys suppress a
duplicate logical append; conflicting payloads for one key fail. The unique
committed `released` operation is the terminal receipt. For a prepared
primitive without its committed pair, recovery reads fresh state: exact
before-state retries the same conditional mutation, exact intended after-state
appends the missing committed event, and any other or partial state fails.
Thus a crash after any prefix resumes at the first uncommitted primitive
without replaying its predecessors. No tracker mutation occurs unless that
primitive's prepared event is durable at head.

Task 00D's real provider implements the closed `inspect_phase`,
`inspect_primitive`, `plan_primitive`, and `apply_primitive` protocol used by
this controller. Inspections and plans bind phase, primitive index and digest,
complete issue fields/metadata/revisions/history cursors, sorted edges,
actor-bound history and comments, scoped-ready proof, and the set of storage
transaction receipts in one canonical domain digest. Each receipt binds its
transaction ID, phase, primitive index/digest, exact before/after domain
digests, and history cursor. Unknown keys, shallow summaries, self-hashed
opaque plans, missing receipts, or a receipt absent from the intended and
observed snapshots fail closed.

The first prepared/committed mutation is `authority_schema_install`. Its
prepared event binds the no-migrate identity, exact core/full-schema fingerprints,
preexisting-data compatibility scan digest, migration ID, migration-host
identity, Tasks 00A–00C binary/fragment/helper receipt, and Task 00D authorizer
package digest. The driver then calls Task 00D's adapter for the exact R21
`authority install --profile full` transaction. A typed core mismatch, incompatible data,
server-lock contention, or foreign host binding performs no schema/history
write. Recovery accepts only the exact prior core schema with no full receipt, where it
retries, or the exact authority schema plus unique matching storage receipt,
where it appends committed evidence; any implicit/partial upgrade or different
receipt fails closed. Only after this committed phase does Task 00D's
authorizer issue the R17 ticket used for every subsequent read or mutation.

For each absent replacement the locked driver invokes one
capability-certified `bd create --if-external-ref-absent` with plain
`--deps <resolved-Task-01-id>` in the same guarded transaction—not
`blocks:<id>`, whose direction is reversed—plus `--priority 0`, exact
task/external-ref/description fields, and canonical registrar metadata with
`registration_state:"pending"` and `feature_container:"agentic-j01"`. It does
not use `--parent`: this toolkit's frontier treats `parent-child` as blocking,
so executable tasks use an explicit nonblocking `related` edge to the feature
container instead. The replacement therefore depends on the blocked guard in
its creation transaction without depending on the blocked feature. The driver
re-resolves it by exact external ref and verifies container metadata, related
edge, priority, registrar metadata, and guard direction before adding
remaining manifest edges. Every later edge/metadata change uses an R17
multi-issue authority transaction naming the fresh expected revisions of all
incident issues. One such transaction adds retained Task 01's dependency on
closed Task 00D and converts Task 01's existing `parent-child` edge to
`agentic-j01` into the same related edge; historical superseded tasks retain
their original history. Only after every edge exists does a conditional batch
set each new issue's registration state to `complete`. Before
every write and after every write except the final guard release it asserts
that the scoped ready set is empty.

The manifest contains the exact pre-migration digest of retained Task 01's
complete live fields and requires those bytes to remain unchanged through
release. The newly required authorizer/provider contract exists only in the
immutable Task 00A–00D definitions and dependency graph. Migration does not
edit Task 01's acceptance or notes and cannot pretend a live prose amendment
will reach a pointer-only worker. Any concurrent Task 01 live-field edit
advances its authority revision, conflicts with the dependency transaction or
release, and is never overwritten.

A `live external dependent` is an issue
outside the retained/historical/replacement sets whose status is neither
`closed` nor `superseded` and which has a blocking dependency on a historical
Task 02–12 issue. The manifest's mandatory known subset is
the package-only exception `agentic-2nj.5`→old Task 06 (`agentic-njk`) and
`agentic-868.9`→old Task 07 (`agentic-tg1`); either missing or already
redirected contrary to the attested starting state fails closed, while
additional live dependents are discovered work, not manifest drift.

Before any supersession transaction, the driver adds every remaining
replacement-graph edge through prepared/committed R17 multi-issue authority
transactions, resolving both sides by exact external ref and binding both
fresh endpoint revisions. A separate manifest-bound transaction handles the
package-only exception first: it adds the Task 19 blocker to
`agentic-2nj.5`, retypes that issue's old Task 06 blocker to `related`, and
binds fresh authority revisions for all three endpoints. Recovery accepts
only exact all-before or all-after state. The subsequent old Task 06
supersession therefore does not enumerate that consumer; future and other
old Task 06 consumers use the durable Task 39 redirect. Migration then
requires a behavior-certified
`agentic.bd-supersession-capabilities/v1` primitive for both supported
backends. In one transaction per old/replacement pair it enumerates every
then-live blocking consumer, adds the corresponding replacement blocking edge,
converts the old blocking edge to a nonblocking `related` historical edge,
marks the old issue superseded by the replacement, and installs a durable
redirect rule. A later raw attempt to add a blocking edge to that superseded
issue must either atomically create the replacement blocking edge plus old
historical relation or reject with typed `superseded_target`; it can never
create an old-only blocker. The certified authority/history cursor orders a racing
dependency addition wholly before the transaction, where it is included, or
afterward, where the redirect/rejection rule applies.

The driver therefore additively covers both mandatory known consumers and
every concurrently discovered consumer. Terminal state requires the
package-only exception to have exactly its Task 19 blocker and old Task 06
historical relation; every other live consumer has exactly the mapped
replacement blocker and old nonblocking historical relation; no live
consumer retains an old blocking edge; and every superseded Task 02–12 issue
has its redirect rule. The migration receipt records the sorted complete
consumer mapping and the explicit exception but does not freeze future
workset cardinality. Before guard
release it verifies `agentic-j01`'s nonblocking related execution set contains
closed Bootstrap Tasks 00A–00D, retained Task 01, and exactly the 27
replacement Tasks 13–39,
and that historical Tasks 02–12 are classified by their supersession
transactions; it does not rewrite container acceptance prose. Immediately after
the migration actor opens retained Task 01 with an empty assignee, that issue
is the sole newly eligible scoped issue; every historical or downstream
replacement issue remains non-ready until ordinary post-release work advances
the graph. Old task files remain immutable history; no registrar rerun may
reinterpret them.

The driver is an idempotent state reconciler, not a forward-only script. Its
closed domain phases are `source_attested`, `bootstrap_verified`,
`authority_schema_installed`, `review_recorded`, `tracker_attested`, `created`,
`wired`, `registered`, `task01_wired`, `redirected`, `manual_blocked`,
`container_verified`, `prepared`, and `released`; each mutating phase uses the
per-primitive prepared/committed sequence and final phase commit above.
`bootstrap_verified` binds the exact canonical terminal receipt bytes and
SHA-256 to the later migration evidence before any tracker write and performs
the fresh four-issue terminal-state proof above. It cannot be a zero-primitive
phase that accepts only a provider-supplied `complete:true` flag.
`review_recorded` validates the external
canonical READY artifact against the explicit reviewed-child commit and
conditionally appends it once to unchanged Task 01 through the new authority;
the following phase verifies exactly that tracker record. On every invocation
it reads actual bd state and the validated head
`agentic.registration-migration/v1` evidence record, accepts only the exact
before/after state for the next phase, completes a partially applied phase, or
fails closed on drift. Every create, related/guard edge, remaining edge,
metadata transition, external rewire, supersession, Task 26/27 block,
and phase-evidence append is individually idempotent and revision-conditional;
no ordinary dependency or metadata mutation is an unguarded "idempotent add."
The complete `prepared` evidence—including all issue IDs, edge and
metadata snapshots, blocked states, hashes, empty-ready proof, and the unique
revision-bound migration actor `agentic:migration:<reviewed-commit>`, where
`<reviewed-commit>` is the manifest's exact 40-lowercase-hex attestation
commit, plus Task 01's fresh stable authority revision/history cursor—is persisted
before the one-way Task 01 release. Release is exactly one
capability-certified Beads transaction:
`<absolute-bd> update --if-revision <prepared-cursor> --status open --assignee "" --actor agentic:migration:<reviewed-commit> --json -- <Task-01-id>`.
The transaction applies only if the exact prepared revision still has the
expected `blocked`/empty-assignee state and live-field digests. It changes that
state
to `open`/empty-assignee and atomically creates its ordinary actor-bound Beads
history event; the driver performs no separate comment or history append.
Fresh post-transaction `show` and history reads through the same R9 ticket
must prove the next cursor, new state, and exactly one matching transition
event with no intervening event. A conditional conflict records no migration
mutation and preserves external authority. An ambiguous connection counts as
released only when the exact cursor transition/event proves it. A crash after release
but before `released` evidence accepts Task 01 still open/ready or any
ordinary forward state (`in_progress`, `closed`, `blocked`, or `deferred`)
only when history proves the exact migration release event preceded every
later mutation, the attested replacement graph/hashes remain unchanged,
any later external dependency is explained by the certified redirect history
and folded into the terminal consumer mapping, and no migration
write made another scoped issue eligible. Rerun then writes the terminal
receipt without repeating or reversing a mutation. A missing/ambiguous actor
event, a prior state other than the prepared exact blocked state,
open-but-not-ready Task 01 without a later authorized mutation, graph
drift, or a second migration-caused eligible issue fails closed. The isolated
test injects a crash and reruns on both sides of every phase/write boundary,
including a concurrent Task 01 claim immediately post-release, while
ready/claim probes prove no earlier exposure. It also launches drivers
simultaneously from the canonical checkout and a linked worktree: both resolve
the same lock, exactly one mutates, the loser returns `migration_busy` with
zero mutation/evidence, killing the winner releases the lock for a clean
resume, and the terminal state contains exactly one issue per replacement
ref, one supersession per historical issue, one Task 01 release event, and
one terminal receipt. A server fixture also starts a second host identity with
a distinct R8 root; the authority receipt rejects it before mutation while the
attested host may resume. Different repositories do not share the lock or host
binding.

Final registration attestation occurs only after Bootstrap Tasks 00A–00D have
landed and closed; it is distinct from the earlier bootstrap-source
attestation. It is deliberately two-phase because a tracked manifest cannot
contain the hash of its own commit. The final `source_commit` contains the
reviewed SPEC bytes, Bootstrap Tasks 00A–00D, their bootstrap
definition/helper, every historical and replacement task file, the migration
driver and acceptance tests, all three completed pinned
Beads fragments and helpers, the completed toolkit authorizer and trusted
Beads allowlist, and the complete manifest with an empty attestation object.
The canonical terminal-bootstrap receipt remains in R8; Git contains only the
contract that creates and consumes it.
It does not contain outputs owned by unrun replacement Tasks 13–39, including
the Mardi Gras provider patch or trusted Mardi Gras release allowlist. Before
that source commit, both the control-unit migration gate and the exact
post-00D `provider_integration` gate above must pass. A direct
child attestation commit changes only the manifest, filling `source_commit`,
the distinct earlier `bootstrap_source_commit` and
`bootstrap_attestation_commit`, exact `bootstrap_receipt_sha256`,
`spec_sha256`, HUMAN-entry digests, every definition hash, and the complete
canonical starting tracker snapshot for retained Task 01, historical Tasks
02–12, their incident edges/revisions/metadata, and both known external
consumers. Neither earlier bootstrap commit may be substituted by the final
source or reviewed-child commit. The manifest cannot contain the hash of its
own reviewed child; the
explicit CLI argument and READY artifact bind that child externally. A final
critic reviews the child revision and returns one canonical external JSON
artifact with closed schema
`agentic.registration-review/v1`, `verdict:"READY"`, reviewed child commit,
source commit, SPEC SHA-256, reviewer run ID, and bounded evidence summary;
after schema installation, `review_recorded` conditionally appends those exact
bytes once as a Task 01 comment and `tracker_attested` rejects zero or multiple
matching READY records. The live command is
`migrate-registration.py run --manifest <path> --authority <absolute-path>
--reviewed-commit <40-hex> --review-artifact <path> --bootstrap-receipt
<absolute-mode-0600-R8-path> --confirmed`. Before any authority mutation, the
driver loads those exact receipt bytes, verifies their SHA-256, closed schema,
bootstrap commits, intent, issue IDs, event chain, provider path/digest, and
complete provider identity, rejects an otherwise valid copy outside the
canonical R8 receipt path, and requires the same physical provider, fresh
no-migrate identity, and fresh exact terminal state of those four issue IDs.
The
pre-full-schema
`source_attested` phase requires the exact
tracked/staged/untracked/ignored/submodule-clean predicate from R20; an
explicit `--reviewed-commit <40-hex>`
equal to current HEAD; `HEAD^` equal to manifest `source_commit`; the diff
from `source_commit` to HEAD to contain only the manifest; every listed file
to be tracked; every listed SPEC/task source to be byte-identical to
`source_commit`; current SPEC/task/HUMAN-entry hashes to match the manifest;
and exact bootstrap intent/receipt hashes. It does not read tracker state.
After `authority_schema_installed`, the `tracker_attested` phase uses the new
R17 ticket to require exactly that Task 01 review record and the manifest's
complete starting issue/edge/revision snapshot. Migration evidence records
both commit IDs and all hashes.

The source commit already contains two unchecked entries under `HUMAN.md`'s
machine-owned section. Before creating that commit, the author chooses one
manifest `source_date_utc` matching exact ASCII `YYYY-MM-DD` and creates or
amends the source commit so its committer timestamp, converted to UTC, has
exactly that date; the driver derives the date from the committed object and
requires equality. The attestation commit may fill hashes and `source_commit`
but may not change `source_date_utc`.

The source `HUMAN.md` bytes must contain exactly one
`## Agent-filed blockers\n` section header. Each required blocker is exactly
one LF-terminated checkbox line in that section selected by the byte substring
` · <exact-replacement-task-path> · run — `; a missing line, duplicate match,
CRLF line, line outside the section, checked entry, or second entry for the
same path fails. The Task 26 line uses its exact replacement task path and
instructs the human to run the complete native façade matrix against the final
immutable package; its `Blocks:` clause names native certification and Task
27. The Task 27 line uses its exact replacement path and instructs the human
to install trusted released Beads and Mardi Gras artifacts, run terminal
parity, and record the cutover receipt; its `Blocks:` clause names production control
cutover. Both have `source_date_utc` as their date token and `run` as their
type. Each manifest HUMAN digest is SHA-256 over that exact line's UTF-8 bytes
including its one final LF and excluding every surrounding byte. The migration
driver only verifies exact committed presence, section membership, date, and
digests; it never writes the tracked file. Task 26's and Task 27's
certification completion procedures each remove only their own exact entry in
the same commit that resolves the human action.

Before Task 01 opens, Task 26 is set blocked with an authenticated-runtime
`Unblock: run:` note and Task 27 is set blocked with a trusted-release
`Unblock: run:` note. Closing every implementation dependency must not make
either certification task ready. Only after the full graph, container contract,
revision attestation, committed manual blockers, and read-only assertions pass
does the driver remove Task 01's pre-publication blocker.
