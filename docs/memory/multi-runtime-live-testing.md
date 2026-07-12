# Live-testing Antigravity CLI (`agy`) or Codex CLI (`codex`): gotchas found 2026-07-11

When to read: about to install, authenticate, or drive `agy` or `codex`
directly (not just edit their mirror files), or scoping a port to a new
coding-agent runtime.

## `agy`'s OAuth window can't survive a chat relay — do it in one sitting

`agy`'s manual-code login flow has a hard ~30-second server-side window
between printing the auth URL and giving up. Relaying the resulting code
through a conversation (user pastes it to the assistant, assistant writes
it to the waiting process) reliably loses the race — round-trip latency
alone exceeds the window, confirmed across several attempts. The fix is
NOT a clever pipe/background trick on the assistant's side; it's having
the human run the whole exchange themselves, in their own terminal, start
to finish, with no relay. If the account isn't already logged into Google
in a browser tab, budget for the consent screen alone possibly blowing the
window too.

## `agy` doesn't scope to the invoking directory by default

Running `agy --print "..."` from inside a target directory does **not**
scope the session to it — `agy` silently reuses a persisted "default
project" (`~/.gemini/config/projects/default-cli-project.json`) instead,
which can be a real, unrelated, sensitive project elsewhere on disk.
`--new-project --add-dir <dir>` doesn't replace the default project
either — it *adds* the new directory as a secondary workspace alongside
whatever was already default, so a "scoped" prompt can still return
results from both. There is no observed flag that gives full isolation
from a prior default project in one shot; treat any `agy` result as
possibly covering more than the directory you asked about until proven
otherwise (check the response for a "Primary Workspace" / "Workspace N"
breakdown).

`codex exec --cd <dir>` does not have this problem — directory scoping via
`--cd` worked cleanly with no bleed-through in testing.

## Antigravity and Codex converged on the same open Agent Skills standard

Both tools independently read `.agents/skills/<name>/SKILL.md` (YAML
frontmatter: `name`, `description`) and an `AGENTS.md` for always-on
project context. A skill mirror built for one often works **unmodified**
for the other — confirmed live: copying `antigravity/.agents/` verbatim
into a scratch repo and running it under `codex exec` correctly
auto-triggered the mirrored `list-specs` skill by description match, read
its `SKILL.md`, and ran its bundled script with the correct scoped
result — zero changes needed. When porting to a third runtime, check
whether it also implements this standard before assuming a from-scratch
mirror is required (see `codex/` overlay: reuses the antigravity mirror
via symlinks for everything that already works, only writing new files
for genuinely different behavior).

## Codex has no invocation mechanism for `.agents/workflows/*.md`

Only `.agents/skills/` gets auto-trigger-by-description or explicit
`$name`/`/skills` invocation. A `.agents/workflows/*.md` file (Antigravity's
equivalent of a human-launched "workflow") is just a plain repo file to
Codex — reachable only if something happens to grep for it (confirmed:
Codex's own `scout` skill found `drain.md` via `rg`, not via any
workflow-discovery path) or a human tells Codex the exact file path.
Anything ported as workflow-only (the disable-model-invocation tier:
`drain`/`build`/`autopilot`/`evals`) needs a REAL Codex skill written for
it, not just a symlink into the antigravity mirror.

## `allow_implicit_invocation: false`'s actual documented semantics

Codex's `agents/openai.yaml` policy flag is the closest analogue to
Claude Code's old `disable-model-invocation`. Per
learn.chatgpt.com/docs/build-skills (current redirect target for
developers.openai.com/codex/skills), Codex documents exactly two
invocation paths: **implicit** (the agent's own autonomous
description-match selection — what the flag disables) and **explicit**
(`$skill-name` or `/skills`, framed throughout the docs as something a
human types in the prompt/chat box). No third "the agent reasons its way
to an explicit invocation without a human typing it" path is documented
anywhere. So the flag gives the same practical guarantee for every skill
it's set on — don't assume a skill needs a stricter or looser variant of
it without a concrete documented mechanism to point to.

**Known upstream unreliability** (verified live, 2026-07-11): explicit
`$skill-name` invocation is not consistently exposed in `codex exec`
non-interactive mode — matches open issues openai/codex #19695, #10585,
#23454. Auto-trigger (implicit, by description match) worked reliably;
explicit invocation of an `allow_implicit_invocation: false` skill did
not, in one live test. Document this as an honest partial/experimental
result in any Codex-port README, not softened into a pass.

## Real session data locations (read-only inspection, don't touch)

- Antigravity: `~/.gemini/antigravity-cli/conversations/<cascade_id>.db`
  (SQLite; usage/model data lives in protobuf-encoded blob columns —
  `sqlite3 <db> "SELECT quote(data) FROM gen_metadata WHERE idx=0"`, strip
  the `X'...'` quoting, decode the hex, pipe through
  `protoc --decode_raw`). Conversation artifacts (transcripts, brain
  state) live in a matching `~/.gemini/antigravity-cli/brain/<cascade_id>/`
  directory.
- Codex: `~/.codex/` (`state_*.sqlite`, `logs_*.sqlite`, `config.toml`,
  `auth.json`). `codex doctor` prints a full health/auth report without
  needing to poke at these files directly.