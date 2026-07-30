# File-sourced commands

A command parsed out of a repository file — an `Unblock: run:` line, an
acceptance criterion's backticked command — reaches `exec` inside an
unattended loop, where no human sees what the file actually said. One policy
decides whether such a command may execute, and it has exactly one
implementation: `bin/command-policy`. Consumers call it and record its
verdict; none of them re-implements the decision or adds a second allowlist.

`.claude/rules/human-blockers.md` is the model this policy follows — its
`Still-blocked:` probes already solve name resolution, no-shell execution,
POSIX lexing, argv execution, and a cwd at the git root. That probe contract
stays where it is: probe resolution is not folded in here.

## Accept conditions

A command is accepted only when all of these hold:

- **argv-0 resolves to a regular executable under an allowlisted root.** The
  roots are the repository's `bin/` and `scripts/`, plus a named tool list
  (`bash`, `echo`, `git`, `grep`, `make`, `node`, `npm`, `python3`) resolved
  under `/bin`, `/usr/bin`, `/usr/local/bin`, or `/opt/homebrew/bin`. A bare
  name is searched against those roots in that order and never against `$PATH`.
- **Execution is direct, never through a shell.** The words are handed to the
  operating system as argv. Nothing is interpreted by `sh -c`, so a
  metacharacter in an accepted argument is an inert byte — *provided* argv-0
  is not itself an interpreter that would read one of those arguments as
  code, which the next condition forbids. That carve-out is why the ban below
  is scoped to argv-0: a regex like `'unclassified\|drift'` or an apostrophe
  in `"don't"` is ordinary argument data, and refusing it would cost the two
  consumers their real commands for no gain.
- **argv-0 never reads a following argument as a code string.** When argv-0
  resolves to an interpreter in the named-tool list (`bash`, `node`,
  `python3`), a `-c`, `-e`, or `--eval` anywhere in its arguments is refused:
  `bash -c '…'` would hand the policy's own bytes back to a shell, undoing
  the direct-execution guarantee above.
- **argv-0 survives POSIX shell-word lexing** and carries no shell
  metacharacter (`;`, `|`, `&`, backtick, `$`, `(`, `)`, `<`, `>`, `\`,
  newline). Words arrive already split, or as one file-sourced string the
  policy lexes itself; an unbalanced quote in that string is refused as it is
  lexed.
- **No word carries an ASCII control character.** This bound holds on every
  word, argv-0 and arguments alike.
- **Bounds hold**: at most 64 words, each at most 4096 characters.
- **The cwd is the repository root**, resolved with `git rev-parse
  --show-toplevel`.
- **A bounded timeout applies** (120 seconds by default; `--timeout` or
  `COMMAND_POLICY_TIMEOUT` override it). On expiry the child's whole process
  group is killed.
- **No network grant.** The child inherits a scrubbed environment — `HOME`,
  `LANG`, `LC_ALL`, `PATH`, `SHELL`, `TMPDIR`, `TZ`, `USER` and nothing else —
  so no proxy configuration and no credential-bearing variable reaches it.
  This is a grant boundary, not kernel-level network isolation: a command that
  needs an enforced network boundary is out of scope for this policy.

## Reason codes

Each refusal carries one stable code, and a consumer records the code rather
than prose: `unresolved-argv0`, `not-executable`, `outside-allowlist`,
`shell-metacharacter`, `interpreter-code-string`, `control-character`,
`unbalanced-quote`, `too-many-arguments`, `argument-too-long`, and `timeout`.

`timeout` is the one code that follows an execution: the command was accepted
and then exceeded its bound. The other nine are decided before any process
starts.

## Demotion contract

A rejected command is **never executed**, and its consumer records the reason
code rather than dropping it:

- An `Unblock: run:` command that the policy rejects demotes to `ask:`,
  carrying the reason code into the question a human answers (EP18).
- An acceptance criterion the policy rejects records `skip` with its reason
  code in the spec's `acceptance-status.json`, and is not counted as a pass
  or a failure (EP12).

## Interface

```sh
bin/command-policy [--check-only] [--timeout SECONDS] <argv…>
bin/command-policy [--check-only] [--timeout SECONDS] --command '<one string>'
```

One JSON verdict object is emitted — `verdict` (`accept`, `reject`,
`timeout`), `reason`, `detail`, `executed`, and `exit_code` when a child ran.
It goes to stdout under `--check-only` — for a rejection as much as for an
acceptance, since the reason code is what a `--check-only` consumer exists to
capture — and to stderr otherwise, so an executed child owns stdout. Exit codes: the accepted command's own code, 78 for a
rejection, 124 for a timeout, 2 for a usage error.
