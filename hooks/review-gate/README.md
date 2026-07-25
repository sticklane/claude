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
- Runs the repository's own `pre-commit` hook first, and exits with that hook's
  status if it fails (see the `core.hooksPath` caveat below).
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

```sh
bin/install-review-gate install            # ~/.git-hooks, or pass a directory
bin/install-review-gate status
```

That symlinks the hook into the hooks directory and sets
`git config --global core.hooksPath` to point at it, which covers every
repository on the machine. If `core.hooksPath` is already set somewhere else,
the installer refuses and tells you rather than clobbering it.

## Uninstall

```sh
bin/install-review-gate uninstall
```

That removes the hook and unsets `core.hooksPath` when it still points at the
hook's directory. Markers are left behind in repositories where a review was
recorded; delete those per repository:

```sh
rm -rf "$(git rev-parse --git-common-dir)/agentic-review"
```

## The `core.hooksPath` caveat

`core.hooksPath` **replaces** a repository's `.git/hooks` rather than adding to
it. A global install would therefore silently disable every repository's own
`pre-commit` hook — on this machine, the staged-file format and lint checks
that gated repos run there.

So the hook chains: before checking for a review it runs the repository's own
`hooks/pre-commit` (resolved from the git common dir, since `git rev-parse
--git-path hooks/pre-commit` answers with `core.hooksPath`'s entry once that is
set), passing along its own arguments and stdin. A non-zero exit from that hook
is the commit's exit status, and the gate adds nothing to its output. It runs
the repository's hook exactly once even when that hook is this same file, by
symlink or by copy.

`REVIEW_GATE=0` returns before the chain and therefore runs neither the review
check nor the repository's own hook; `git commit --no-verify` skips both by
skipping the hook entirely.

Only `pre-commit` is chained. Every OTHER hook type a repository defines —
`commit-msg`, `prepare-commit-msg`, `pre-push`, `post-commit`, `pre-rebase`,
`post-merge`, and the rest, including anything husky installed — stops running
in every repository for as long as `core.hooksPath` is set, because git looks
for those names in the hooks directory too and finds nothing there. That is a
property of `core.hooksPath`, not of this hook. `bin/install-review-gate
install` says so at install time. If a repository on this machine depends on
one of those hooks, install per repository (symlink the hook into that
repository's `.git/hooks/pre-commit`) instead of globally.

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
- Every non-`pre-commit` hook in every repository, while a global install is
  in place — see the `core.hooksPath` caveat above.

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
