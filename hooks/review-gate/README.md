# review-gate hook

A git `pre-commit` hook that refuses a commit until a review has been recorded
against the content that commit will contain. The recording tool is
`bin/review-gate`; this hook is the thing that makes forgetting to use it cost
you a round trip instead of nothing.

It is a git hook rather than a Claude Code `PreToolUse` hook because the
content is only unambiguous once git has staged it. A `PreToolUse` hook sees a
command string and has to guess: `git commit -am`, pathspec commits, heredocs,
`bash -c`, and aliases each defeated a different version of that parser. Inside
a `pre-commit` hook, `git diff --cached` is the commit, whatever form the
command took, and there is nothing left to parse.

## What it does

- Asks `review-gate check` whether a review is on file for the key of
  `git diff --cached`. If it is, the hook stays silent and the commit proceeds.
- If it is not, the hook prints the key, the exact `review-gate record` command
  to run once you have reviewed, and both bypasses; then it exits 1 and the
  commit does not happen.
- Runs after the repository's own `pre-commit` checks, never instead of them,
  and exits with their status if they fail (see [Install](#install)).
- Refuses when it cannot compute the key at all — no `shasum` or `sha256sum` on
  `PATH`. A gate that cannot see the diff would otherwise switch itself off
  silently.

## What it does NOT guarantee

That a review happened. `review-gate record` accepts any non-blank text on
stdin and the marker is an ordinary file under `.git/`, so any agent with shell
access can satisfy the gate — or forge it — without reviewing anything. This
is a speed bump: it converts an oversight into a deliberate act. It is not
proof of review and must not be reported as one. Real proof would require the
gate to run the review itself, outside the committing agent's control.

## What the review itself should block on

The gate fires on *whether a review happened*, never on what it found. Deciding
which findings are worth stopping for stays with the reviewer, and the bar there
isn't "clean." Published practice converges on approving work that improves the
codebase even when imperfect, and on reserving a block for defects rather than
taste:

- Hard-block on correctness bugs, security vulnerabilities, and defects that
  would break production.
- Report but allow style, naming, structure, nits, missing non-critical tests,
  and pre-existing issues the change didn't introduce.

Google's standard is to "favor approving a CL once it is in a state where it
definitely improves the overall code health of the system being worked on, even
if the CL isn't perfect," and to never "block CLs from being submitted based
only on personal style preferences"
(<https://google.github.io/eng-practices/review/reviewer/standard.html>).
Anthropic's own Code Review tags findings Important / Nit / Pre-existing and
never blocks a merge on them
(<https://code.claude.com/docs/en/code-review>).

That bar applies to this gate too. Google's Tricorder turns off any analyzer
that produces 10% or more effective false positives
(<https://abseil.io/resources/swe-book/html/ch20.html>). A wrong refusal here
blocks real work in every repository on the machine, so a false refusal is a
more serious defect than a missed commit. If this gate starts refusing
legitimate commits, turn it off rather than working around it.

## The bypasses

There are two, and every refusal names both:

- `REVIEW_GATE=0 git commit ...` turns the gate off for that command. Use it
  for a commit you have decided not to gate.
- `git commit --no-verify` skips every `pre-commit` hook, this one included —
  the standard git escape hatch.

Neither is narrower than the other in practice: the gate returns on
`REVIEW_GATE=0` before it chains, so both bypasses also skip whatever
staged-file format and lint checks the repository's own `pre-commit` hook runs.
Re-run those by hand, or don't bypass.

## Recording a review for `-a` and pathspec commits

`review-gate record` reads `git diff --cached` from your shell, where
`git commit -a` and `git commit -m x <path>` have not staged anything yet. The
index has to hold exactly what the commit will contain, or the key you record is
not the key the hook computes and the commit is refused.

For `git commit -a`, that is `git add -u` — tracked changes only, which is what
`-a` writes. Not `git add -A`: it also stages untracked files, which a `-a`
commit does not contain.

```sh
git add -u
printf '%s' 'VERDICT: READY — no blocking findings' | review-gate record
git commit -am 'the reviewed change'
```

For a pathspec commit, git builds the commit from `HEAD` plus the paths you
name, ignoring everything else in the index — so anything else staged has to
come out of the index first, or it lands in the key and not in the commit:

```sh
git reset                     # unrelated staged work goes back to the worktree
git add -- src/thing.go
printf '%s' 'VERDICT: READY — no blocking findings' | review-gate record
git commit -m 'the reviewed change' src/thing.go
```

## Install

Installation is per repository. Name the repositories, or omit them for the
current one:

```sh
bin/install-review-gate install            # the current repository
bin/install-review-gate install ~/hub ~/fooszone
bin/install-review-gate status ~/hub
```

The hook lands in the repository's *effective* hooks directory — what
`git rev-parse --git-path hooks` answers, which already honors a
repository-local `core.hooksPath` (bd sets one, pointing at `.beads/hooks`).
That is exactly where git will look in that repository, and nothing else in it
changes.

If no `pre-commit` hook is there, the installer symlinks ours in. If one is
already there, it stays and the installer appends a marked block that runs the
gate after it:

```sh
# --- BEGIN AGENTIC REVIEW-GATE ---
REVIEW_GATE_CHAINED=1 '/path/to/hooks/review-gate/pre-commit' "$@" || exit $?
# --- END AGENTIC REVIEW-GATE ---
```

The repository's own checks run first and decide first; the gate runs only once
they pass. Re-running `install` replaces the block in place, so it never
appears twice.

In a bd-managed repository the block goes strictly after
`# --- END BEADS INTEGRATION vN ---`. Everything between bd's markers belongs
to bd, and the installer never writes inside them; if that block is not the end
of the file, it refuses rather than guessing where its own belongs.

It also refuses when the target is not a git repository, when the hooks
directory cannot be created or written, when the existing hook is not a shell
script, and when the existing hook's last line is an unconditional `exit` —
a block appended after that would never run, and reporting success while gating
nothing is the failure this installer exists to avoid.

## Uninstall

```sh
bin/install-review-gate uninstall          # the current repository
bin/install-review-gate uninstall ~/hub
```

That removes the marked block and leaves the rest of the file byte-for-byte as
it was, or removes the file outright when it holds nothing but our hook. A
beads block is never touched. Markers are left behind in repositories where a
review was recorded; delete those per repository:

```sh
rm -rf "$(git rev-parse --git-common-dir)/agentic-review"
```

## Why not a global `core.hooksPath`

The installer deliberately does not set `core.hooksPath`, globally or locally.
It is the wrong mechanism here twice over:

- **Inert where it matters.** A local `core.hooksPath` overrides the global
  one, and every bd-managed repository sets one — on this machine that is every
  repository in daily use (`~/claude`, `~/hub`, `~/fooszone`,
  `~/ynab-mcp-new`), each pointing at its own `.beads/hooks`. A global install
  would report success and gate none of them.
- **Harmful everywhere else.** Where no local setting exists,
  `core.hooksPath` **replaces** `.git/hooks` rather than adding to it, so every
  hook type the new directory does not itself provide stops running.
  `post-commit`, `pre-push`, `post-merge`, `post-checkout` and a `review-audit`
  hook are all live in repositories on this machine and would have gone silent,
  along with anything husky installed.

Installing into the effective hooks directory avoids both.

The hook still chains to a repository's own `pre-commit` when it is installed
as the whole file, resolving it from the git common dir and passing along its
arguments and stdin; a non-zero exit from that hook is the commit's exit
status, and the gate adds nothing to its output. It runs that hook exactly once
even when the hook is this same file, by symlink or by copy. An appended
install needs none of that — the repository's checks sit above the block in the
same file — so the block sets `REVIEW_GATE_CHAINED=1` and they do not run
twice.

`REVIEW_GATE=0` returns before the chain and therefore runs neither the review
check nor the repository's own hook; `git commit --no-verify` skips both by
skipping the hook entirely.

## Requirements

- `bin/review-gate` next to the hook (`../../bin/review-gate`, following the
  installed symlink) or on `PATH`.
- `shasum` or `sha256sum` on `PATH`.

## Known gaps

A `pre-commit` hook covers `git commit`. These write history without running
it, and are not gated:

- `git merge` — runs `pre-merge-commit` instead, which this does not install.
  A merge that stops for a manual `git commit` is gated, as an ordinary commit.
- `git rebase` — replayed commits do not run `pre-commit`. Neither does
  `git cherry-pick`, `git revert`, or `git commit --amend` under a rebase.
- `git am` and `git apply --index` followed by a rebase-style commit.
- Any tool writing objects directly: `git commit-tree`, `git fast-import`,
  `git update-ref` on a hand-built tree, or a library like libgit2 or
  Dulwich that never shells out to the hook.
- `git commit --amend` IS gated, but on what is staged against `HEAD` rather
  than on the whole commit the amend produces. A reword with nothing staged has
  an empty diff and passes.
- Every repository the hook has not been installed into. Installation is per
  repository, so a fresh clone commits ungated until you run the installer
  there.

Treat every gap above as open.

## Tests

```sh
bash tests/test_review_gate.sh
```

The tests drive real `git commit` invocations against throwaway fixture
repositories in a temp dir — plain, `-a`, pathspec, and `bash -c` commits, both
bypasses, the chaining and recursion cases, and every fail-open boundary. The
installer assertions run against a sandboxed `HOME` and `GIT_CONFIG_GLOBAL`,
and skip themselves if git does not honor the latter. Nothing here touches this
toolkit's own `.git` or the machine's real git configuration.
