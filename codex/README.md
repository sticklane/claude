# Using this toolkit with OpenAI Codex CLI

OpenAI's Codex CLI (confirmed live on `codex-cli 0.144.1`) natively reads the
Agent Skills standard — `.agents/skills/<name>/SKILL.md` with YAML
`name`/`description` frontmatter, plus `AGENTS.md` — the exact shape the
`antigravity/` port already uses. So this port **reuses, it does not copy**.

## Reuse, don't copy

`codex/.agents/skills/` is a thin overlay, not a third mirror:

- The 15 already-working skills and the `_shared/` support directory are
  **relative symlinks** back into `antigravity/.agents/skills/*` — one entry
  each, zero content copies. Codex reads a symlinked `SKILL.md` transparently
  (it `cat`s the file the link points at) and runs the bundled scanners in
  place, so these skills stay in lockstep with the antigravity tree.
- Only the four launch-gated stages — `drain`, `build`, `autopilot`,
  `evals` — are **real directories** here, each with its own `SKILL.md` and a
  nested `agents/openai.yaml` setting
  `policy: { allow_implicit_invocation: false }`. That is Codex's native
  analogue of `.claude/`'s launch gates (a launch-authorization contract on
  drain/build/autopilot since 2026-07; the `disable-model-invocation` flag
  remains only on `/evals`): it blocks automatic description-match
  selection while leaving explicit invocation available.

See [`codex/AGENTS.md`](AGENTS.md) for orientation; the shared pipeline
doctrine lives in [`antigravity/AGENTS.md`](../antigravity/AGENTS.md).

## Invocation convention (fixed by design)

Codex discovers project skills from a single `.agents/skills` directory
**relative to the directory it is invoked in** (see the live result below).
Because this port keeps `.agents/` at `codex/.agents/` — a subdirectory of the
git root — always point Codex at `codex/`:

```bash
# non-interactive
codex exec --cd codex "list the specs in this project and their status"

# interactive: start Codex with codex/ as its working directory
cd codex && codex
```

`--cd codex` (or starting Codex with `codex/` as its cwd) is the one
convention that gives Codex a single discovery root holding **both** the
reused symlinked skills and the four new ones. No root-level
`.agents -> codex/.agents` fallback symlink is needed on this repo — discovery
proved cwd-relative (below), so the git root is left without an `.agents/`
directory.

## Live verification

[`codex/verify-live.sh`](verify-live.sh) is the runnable, re-runnable R5
check. Run it from the repo root after any Codex CLI upgrade; if no `codex`
binary is on PATH it prints `MANUAL-PENDING — codex not installed` and exits 0
rather than fabricating output.

```bash
./codex/verify-live.sh
```

### Recorded results — codex-cli 0.144.1, run from this repo's real root

| Check | Result | What was observed |
|---|---|---|
| **(a)** discovery root | **WORKS — cwd/`--cd`-relative** | With `--cd codex`, Codex found the skills under `codex/.agents/skills/`; the git root has no `.agents/`, so a git-root-relative reading would have found nothing. No fallback symlink was needed. |
| **(b)** symlinked skill auto-triggers | **WORKS** | A plain "list the specs in this project and their status" prompt auto-selected `list-specs` by description match, `cat`-ed its `SKILL.md` through the `antigravity/` symlink, and ran the bundled `list_specs.py`. It correctly returned `no specs/ directory found` — the correct scoped result, since `codex/` (the working root) has no `specs/` of its own. |
| **(c-neg)** drain must NOT auto-trigger | **WORKS as intended** | A drain-shaped natural-language prompt did **not** auto-select the `drain` skill; `allow_implicit_invocation: false` kept it out of the session's available-skill list (the model reported the `$drain` skill "isn't exposed in this session's available-skill list"). |
| **(c-pos)** explicit `$drain` | **PARTIAL — see below** | Typing `$drain` in `codex exec` did **not** invoke drain through the skill mechanism; `$drain` was treated as literal text. The model instead grep-found and read the `SKILL.md` file on disk, so its Launch-authorization content surfaced — but not via `$`-invocation. |

The (c-pos) partial is the expected outcome, not a spec failure: the
explicit-invocation-only skill mechanism is an **early, not-yet-reliable**
Codex feature per open upstream issues
[openai/codex #19695](https://github.com/openai/codex/issues/19695),
[#10585](https://github.com/openai/codex/issues/10585), and
[#23454](https://github.com/openai/codex/issues/23454). The four stages still
ship: an unreliable-but-present explicit skill, whose `SKILL.md` is at worst
readable from disk, is strictly better than the "unreachable except by exact
file path" state that preceded this port.

## What degrades on Codex (be aware)

- **No custom slash commands.** Codex has no user-defined `/command`
  mechanism (the old "custom prompts" file is deprecated in favor of skills),
  so there is no `/idea`, `/build`, … the way Claude Code and Antigravity
  expose them. Invoke a skill by natural-language description match (for the
  15 auto-trigger skills) or by typing its name.
- **Explicit-invocation-only skills are experimental.** The four
  human-launched stages (`drain`/`build`/`autopilot`/`evals`) rely on
  `allow_implicit_invocation: false` plus `$name` / `/skills` invocation.
  Live-tested here: the *guard* works (no auto-trigger — (c-neg) above), but
  the *explicit `$name` path is not yet exposed in `codex exec`* — (c-pos)
  above, matching upstream #19695/#10585/#23454. Treat these four as
  best-effort until those issues close; their procedures are inlined in each
  `SKILL.md` so the content is reachable even when `$`-invocation is not, and
  a human can always open the `SKILL.md` and follow it directly.
- **Subagents are not a workflow launcher.** Codex Subagents (`.codex/agents/`
  TOML, `/agent`, "spawn N agents") are a delegation/parallelism primitive —
  the analogue of this toolkit's Agent-tool dispatch, not of a human-launched
  command. They do not provide a launch-gate stand-in for the four stages.
- **The launch guard is real, but the file is still on disk.** Because
  `allow_implicit_invocation: false` only removes a skill from *auto-selection*
  (confirmed (c-neg)), a capable model can still `grep`/`cat` a `SKILL.md`
  directly and try to follow it — as (c-pos) showed. The human-authorization
  guarantee holds at the skill-mechanism layer; it is not a filesystem ACL.
  Run unattended Codex sessions under `--sandbox read-only` (as
  `verify-live.sh` does) so a stage that is merely *read* still cannot act.

## What's not ported

Checked by `tests/test_codex_parity.sh` (sibling to the antigravity parity
gate): every `.claude/skills/*` and `.claude/agents/*.md` must have either a
`codex/.agents/skills/<name>` entry (real directory or a resolving symlink)
or an anchored row here whose second cell contains "Not ported".

| Skill | Status |
|---|---|
| `fleet` | Not ported — inherited from `antigravity/README.md`: Antigravity's Agent Manager is this surface natively, and Codex has no equivalent to port from. |
| `workflow-author` | Not ported — inherited from `antigravity/README.md`: its entire job is authoring `.claude/workflows/*.js` for the Claude-Code-specific `Workflow` tool; neither Antigravity nor Codex has a scripted fan-out primitive to author against. |
| `critique` | Not ported — Antigravity itself only has `critique` as a workflow (`antigravity/.agents/workflows/critique.md`), not a skill; Codex has no workflow mechanism to reuse (no custom slash commands, per "What degrades on Codex" above), and there is no skill-shaped antigravity source to symlink. The procedure is reachable only by opening the file directly. |
| `qa-sweep` | Not ported — qa-sweep is a skill, not one of the four explicit-invocation-only skill wrappers (drain/build/autopilot/evals) Codex ships as real content, so per root CLAUDE.md's mirror-chain convention no `codex/.agents/skills/qa-sweep` entry is created. |

## Keeping the ports in sync

`.claude/` is the source of truth → `antigravity/` is the full mirrored port
(real copies) → `codex/` is this thin overlay (symlinks the ~15 already-working
`antigravity/.agents/skills/*` directories, adds only the four
explicit-invocation-only skill wrappers as real content). A change to one of
`.claude/skills/{drain,build,autopilot,evals}/SKILL.md` must also update the
matching `codex/.agents/skills/<name>/SKILL.md`; renaming or removing any of
the 15 already-working skills must update the matching symlink here, since a
dangling symlink silently drops that skill from Codex's discovery root.
