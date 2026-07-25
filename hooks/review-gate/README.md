# review-gate hook

A `PreToolUse` hook that denies a Bash `git commit` until a review has been
recorded against the exact diff that commit would contain. The recording tool
is `bin/review-gate`; this hook is the thing that makes forgetting to use it
cost you a round trip instead of nothing.

## What it does

- Parses the Bash command about to run, finds a `git commit` in it, and works
  out what the commit would contain — `--all` widens the diff to tracked
  unstaged changes, `--amend` measures against the commit being replaced,
  `git -C <dir>` moves the decision into `<dir>`.
- Asks `review-gate check` whether a review is on file for that diff's key. If
  it is, the hook stays silent and the commit proceeds.
- If it is not, the hook emits a `deny` naming the key, the diff command to
  review, and the exact `review-gate record` line to run afterwards.
- Denies a pathspec commit (`git commit -m x file.txt`) outright. That form
  takes content from the worktree rather than the index, so there is no diff
  for the gate to key on.
- Denies when it cannot compute the key at all — no `shasum` or `sha256sum` on
  `PATH`, or a `git diff` that failed. A gate that cannot see the diff would
  otherwise switch itself off silently.

## What it does NOT guarantee

That a review happened. `review-gate record` accepts any non-blank text on
stdin and the marker is an ordinary file under `.git/`, so any agent with shell
access can satisfy the gate — or forge it — without reviewing anything. This
is a speed bump: it converts an oversight into a deliberate act. It is not
proof of review and must not be reported as one. Real proof would require the
gate to run the review itself, outside the committing agent's control.

## The bypass

`REVIEW_GATE=0` in the command's environment turns the gate off for that
command — both the hook and `review-gate check` honor it, including for the
pathspec deny. Use it when you have decided a commit should not be gated. It is
named in every deny message, so nobody has to go looking for it.

## Known gaps

The hook reads one command string. These evade it, and no amount of parsing
will fix them, because the commit text is not visible until a shell expands it:

- `bash -c 'git commit -m x'` and `sh -c '...'` — the commit lives inside a
  quoted argument, which the parser deliberately treats as data.
- `xargs git commit` — the command word comes from stdin.
- `eval "$cmd"` and `$(...)` command substitution — the commit text is
  produced at runtime.
- Committing through a tool other than Bash, or a `git` alias that wraps
  `commit` under another name.
- Heredoc bodies are skipped wholesale, so a heredoc that is executed rather
  than written to a file hides its commits.

Treat every gap above as open.

In the other direction, the pathspec deny fires on an unexpanded variable
(`git commit -m x $FILE`), because the hook sees the literal text and a
positional argument there really would be a pathspec. Expand it yourself, or
use the bypass.

## Requirements

- `jq` on `PATH` (the hook is silent and allows without it).
- `bin/review-gate` next to the hook (`../../bin/review-gate`) or on `PATH`.

## Install

The hook is not auto-installed. Wire it in your user settings at
`~/.claude/settings.json` to cover every repo (replace `<TOOLKIT>` with the
toolkit checkout root):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "<TOOLKIT>/hooks/review-gate/pretool-review.sh"
          }
        ]
      }
    ]
  }
}
```

If `~/.claude/settings.json` already has a `hooks` block, append this entry to
the existing `PreToolUse` array rather than replacing the block. Restart or
reload sessions for the setting to take effect.

## Uninstall

Remove that entry from `~/.claude/settings.json` and reload. Nothing else is
left behind outside `.git/agentic-review/` in repos where a review was
recorded; delete those directories to clean up:

```sh
rm -rf "$(git rev-parse --git-common-dir)/agentic-review"
```

To disable it for a single command instead, use `REVIEW_GATE=0` (above).

## Fail-open boundaries

Every unexpected condition allows the commit and says why on stderr: no `jq`,
malformed hook JSON, empty stdin, not a git repository, `review-gate` not
found, a `git -C` target that is not a directory, or a marker location that
cannot be written (a read-only `.git` must not wedge the repository). The one
deliberate exception is the uncomputable-key deny above, where allowing would
mean the gate is off with no signal.

## Tests

```sh
bash tests/test_review_gate.sh
```

The tests drive both the hook and `bin/review-gate` against throwaway fixture
repositories in a temp dir, covering the deny and allow paths, the `-a` /
`--amend` / `-C` variants, pathspec commits, heredoc bodies, every fail-open
boundary, and the `REVIEW_GATE=0` bypass. They never touch this toolkit's own
`.git`.
