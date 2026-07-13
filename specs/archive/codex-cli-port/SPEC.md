# Codex CLI port of the toolkit

Status: open
Priority: P2
Breakdown-ready: true

## Problem

The toolkit already ships two runtimes: `.claude/` (source of truth) and
`antigravity/` (mirrored port for Google's Antigravity CLI). OpenAI's Codex
CLI (v0.144.1, confirmed live via `codex doctor` this session) is a third
plausible target, and live testing this session showed the picture is
mixed rather than "just works" or "needs a full new mirror":

- Codex natively reads the exact `.agents/skills/<name>/SKILL.md`
  (YAML frontmatter `name`/`description`) + `AGENTS.md` shape that
  `antigravity/.agents/` already uses. Confirmed live: copying
  `antigravity/.agents/` + `antigravity/AGENTS.md` unmodified into a scratch
  git repo root and running `codex exec --cd <scratch> --skip-git-repo-check
  "list the specs in this project and their status"` correctly
  auto-triggered the mirrored `list-specs` skill by description match, read
  its `SKILL.md`, ran the bundled `list_specs.py`, and returned the correct
  scoped result — zero file changes needed for the skills tier's content.
- Codex has no structural discovery mechanism for
  `antigravity/.agents/workflows/*.md` at all. Confirmed live: asking Codex
  "what does this project's drain workflow do?" only produced a correct
  answer because Codex's own `scout` skill happened to `rg -n "drain"` across
  `.agents/workflows` and `.agents/skills` and found the file by luck of
  grep, not through any workflow-invocation mechanism — there is no
  slash-command or workflow-discovery equivalent to Antigravity's Agent
  Manager. This leaves the entire `disable-model-invocation: true` /
  human-only execution tier ported as antigravity workflows — `drain`,
  `build`, `autopilot`, `evals` — effectively unreachable on Codex except by
  a user pasting an exact file path.
- Research this session (developers.openai.com/codex, redirects to
  learn.chatgpt.com/docs/*) found a real Codex-native analogue of
  `disable-model-invocation`: an optional `agents/openai.yaml` beside a
  `SKILL.md` with `policy: { allow_implicit_invocation: false }` disables
  auto-trigger-by-description-match while explicit invocation still works
  via `$skill-name` in the TUI/`codex exec`, or the `/skills` command
  (https://developers.openai.com/codex/skills). This means the four
  workflow-only stages COULD become real, explicitly-invocable Codex
  skills instead of unreachable files — but three open upstream issues
  (openai/codex #19695, #10585, #23454) report explicit-invocation-only
  skills are not yet reliably discoverable, so this is an early mechanism,
  not a settled guarantee, and needs to be verified live before being
  trusted as the primary path.
- Codex Subagents (developers.openai.com/codex/subagents) are a
  delegation/parallelism primitive (custom TOML files in `.codex/agents/`
  or `~/.codex/agents/`, triggered by natural language like "spawn two
  agents", or `/agent` for switching threads) — analogous to this toolkit's
  Agent-tool dispatch, not to Antigravity's Agent Manager. They do not
  offer a "human-launched command" stand-in and are out of scope for
  solving the workflow-invocation gap.
- Codex does not support user-defined custom slash commands; a "custom
  prompts" file mechanism existed but OpenAI's docs now mark it deprecated
  in favor of skills.
- Codex hooks (developers.openai.com/codex/hooks) are richer than
  Antigravity's `hooks.json`: lifecycle events include `SessionStart`,
  `SubagentStart`/`Stop`, `Stop`, `PreToolUse`, `PermissionRequest`,
  `PostToolUse`, `UserPromptSubmit`, `PreCompact`, `PostCompact`, configured
  via `hooks.json` or inline `[hooks]` in `config.toml`, with block/deny,
  rewrite, and context-injection actions comparable in scope to Claude
  Code's own hook system. A future `gate` skill port could target this
  directly, but that is out of scope for this spec.

Without a decision, the toolkit either gets no Codex support, or someone
builds a naive full duplicate `codex/` mirror that doubles the maintenance
burden CLAUDE.md already tracks for the antigravity mirror ("mirror the
change there in the same commit" — CLAUDE.md:73-80) without first checking
whether the skills tier even needs duplicating.

Resolved research finding (see
`specs/codex-port-launch-authorization-parity/SPEC.md` for the full
quote chain, not duplicated here): Codex's own documentation
(learn.chatgpt.com/docs/build-skills) describes exactly two invocation
pathways — agent-autonomous description-match selection (which
`allow_implicit_invocation: false` blocks) and human-typed explicit
invocation (`$skill-name` / `/skills`, which the flag leaves untouched).
No third "the model self-invokes explicitly" pathway is documented
anywhere. Because those two pathways are exhaustive, the single flag
already gives all four workflow-only stages a sufficient and uniform
launch guarantee: nothing the model can do reaches a stage the human did
not type. This is why R3 adapts one live-authorization-contract paragraph
to Codex's mechanism rather than inventing per-skill gating differences.

## Solution

Reuse, don't duplicate — but reuse through ONE unified discovery root, not
two competing trees. Codex discovers project skills from a single
`.agents/skills` directory relative to the directory it's invoked in
(confirmed live: the scratch-repo test put `.agents/` at the invoked root).
A design that leaves the 15 already-working skills under
`antigravity/.agents/skills/` while placing the four new workflow-only
skills under a separate `codex/.agents/skills/` does not work: whichever
tree Codex is pointed at, the other tree's skills stay invisible, which
recreates the exact "unreachable except by exact file path" problem this
spec exists to fix. (This was the critic's top finding on the first draft;
this section resolves it by design rather than punting to a live A/B test.)

Caveat carried into R5: the scratch-repo live test happened to have its
invoked `--cd` directory *equal to* the git repo root, so it cannot by
itself distinguish "discovery is relative to the `--cd`/cwd directory" from
"discovery is relative to the git repository root" — and this spec's
`codex/` design puts `.agents/` at a subdirectory of the git root, not at
the root itself, which only the cwd-relative reading supports. R5 is the
step that resolves this ambiguity for real, before the design is trusted;
if it turns out discovery is git-root-relative instead, the documented
fallback is a root-level `.agents -> codex/.agents` symlink (the repo root
has no existing `.agents/` directory today to conflict with) instead of
relying on `--cd codex`, with `codex/README.md` updated to say which one
this repo actually needs.

Concretely:

1. `codex/` becomes a small, self-contained Codex-facing project root:
   - `codex/.agents/skills/` is populated with (a) one relative symlink per
     already-working entry under `antigravity/.agents/skills/` — the 15
     skill directories AND the `_shared/` support directory (16 entries
     total: `_shared/` holds `spec_readiness.py`/`viz.py`, used by
     `list-specs` and `workboard`. Those scripts self-locate via
     `Path(__file__).resolve()`, which chases the per-skill symlink back
     into the real `antigravity/` tree, so they would not actually break at
     runtime without a `_shared` symlink here — but `_shared` still must be
     symlinked so `codex/.agents/skills/` stays an exact listing match with
     `antigravity/.agents/skills/`, which R4's diff check requires), e.g.
     `codex/.agents/skills/list-specs -> ../../../antigravity/.agents/skills/list-specs`
     and `codex/.agents/skills/_shared -> ../../../antigravity/.agents/skills/_shared` —
     so all of it is reused with zero copies (a symlink is not a duplicate
     mirror), and (b) four real directories —
     `codex/.agents/skills/{drain,build,autopilot,evals}/` — each with its
     own `SKILL.md` and an `agents/openai.yaml` file nested beneath it (the
     exact path OpenAI's docs specify — https://developers.openai.com/codex/skills)
     setting `policy: { allow_implicit_invocation: false }`. Together this makes
     all 19 skills plus the shared support directory visible from the
     single discovery root Codex actually uses.
   - `codex/AGENTS.md` is a short, real (not symlinked) file: it points to
     `antigravity/AGENTS.md` for the shared pipeline orientation and adds
     the one Codex-specific fact `antigravity/AGENTS.md` doesn't know —
     that this project additionally exposes `drain`/`build`/`autopilot`/
     `evals` as explicit-invocation-only skills (`$drain`, etc.), with the
     experimental-reliability caveat below.
   - `codex/README.md`: a thin doc (same shape as `antigravity/README.md`'s
     "What degrades" section) stating the one invocation convention —
     `codex exec --cd codex "<prompt>"` (or an interactive `codex` session
     started with `codex/` as its working directory) — documenting what
     still degrades for Codex specifically (no custom slash commands;
     explicit-invocation-only skills are an early/unreliable mechanism per
     the open upstream issues #19695/#10585/#23454; Subagents are not a
     workflow-launcher stand-in), and stating the live verification command
     a maintainer re-runs after any Codex CLI upgrade.
   - No content copies of the other ~15 skills or the 13 workflow files —
     those stay authored once under `antigravity/.agents/`, reused via
     symlink from `codex/.agents/skills/`.
2. The invocation convention is fixed by design as `--cd codex` from the
   repo root (or equivalent: starting Codex with `codex/` as its cwd) — not
   left as a choice between mechanisms — because it is the only option that
   gives Codex one discovery root containing both the reused skills and the
   four new ones. R5's live test verifies this design actually resolves
   correctly (symlinks intact and traversable, both an old and a new skill
   discoverable from that one root) — it is a verification step, not a
   decision point.
3. Update CLAUDE.md's mirror-convention bullet (currently: "`.claude/` is
   the source of truth; `antigravity/` is a mirrored port... mirror the
   change there in the same commit") to describe the three-way
   relationship: `.claude/` → `antigravity/` (full mirrored port, real
   copies) → `codex/` (thin overlay: symlinks the ~15 already-working
   `antigravity/.agents/skills/*` directories, adds only the four
   explicit-invocation-only skill wrappers as real content). A task whose
   `Touch:` changes one of the four `.claude/skills/{drain,build,autopilot,
   evals}/SKILL.md` files must also carry the matching
   `codex/.agents/skills/<name>/SKILL.md` update in its `Touch:` — same
   discipline as the existing antigravity mirror rule. A task that renames
   or removes any of the ~15 already-working `antigravity/.agents/skills/*`
   directories must also update the matching symlink under
   `codex/.agents/skills/`, since a dangling symlink silently drops that
   skill from Codex's discovery root.
4. Bump `.claude-plugin/plugin.json` version in the same commit as any
   `codex/` addition, per existing convention.
5. Live-verify the explicit-invocation-only mechanism before trusting it:
   if it proves unreliable (matching the open upstream issues), document
   the four skills as best-effort/experimental in `codex/README.md` rather
   than claiming they reliably work, but still ship them (an
   unreliable-but-present explicit skill is strictly better than the
   current "unreachable except by exact file path" state). If no `codex`
   binary is available to run the live test at all (e.g. an unattended
   `/drain` or `/build` worker with no Codex CLI installed), the
   verification requirement (R5) and the end-to-end acceptance check both
   have an explicit manual-pending path: stop, mark the check
   manual-pending in the task's evidence, and do not fabricate output —
   per the "must not gate acceptance on a tool unattended workers lack"
   rule (docs/memory/unattended-worker-tool-limits.md).

## Requirements

- R1: `codex/README.md` exists, documents the reuse-not-copy approach for
  the skills tier, states the fixed invocation convention (`--cd codex` /
  `codex/` as cwd), and includes a "What degrades on Codex" section
  covering: no custom slash commands, Subagents ≠ workflow launcher, and
  the experimental status of explicit-invocation-only skills.
- R2: `codex/.agents/skills/drain/SKILL.md`,
  `codex/.agents/skills/build/SKILL.md`,
  `codex/.agents/skills/autopilot/SKILL.md`, and
  `codex/.agents/skills/evals/SKILL.md` each exist with valid YAML
  frontmatter (`name`, `description`) and, nested at `agents/openai.yaml`
  beneath each skill directory (per https://developers.openai.com/codex/skills —
  NOT a flat sibling of SKILL.md), a policy setting
  `allow_implicit_invocation: false`.
- R3: Each of the four SKILL.md bodies inline-covers the same execution
  steps as its `.claude/skills/<name>/SKILL.md` counterpart (a paraphrased
  adaptation per docs/memory/workboard-mirror-verbatim.md's prose-mirror
  convention — content-coverage checked, not byte-diffed) — not a stub that
  merely says "see antigravity" (Codex needs the procedure inline since it
  has no workflow-file fallback to read from). Additionally, for
  `drain`/`build`/`autopilot` specifically, the inlined SKILL.md content
  must include a live-authorization-contract paragraph — but adapted to
  name Codex's actual gating mechanism rather than quoting `.claude/`'s own
  tool names verbatim: `allow_implicit_invocation: false` blocks automatic
  description-match selection, so the agent cannot self-launch the stage; a
  human must type the invocation explicitly (`$drain`/`$build`/`$autopilot`
  in the TUI or `codex exec`, or via the `/skills` command). `evals`'s
  SKILL.md is explicitly unaffected here — its "human-only, paid headless
  sessions" framing already states an unconditional guarantee, so there is
  nothing to add to it.
- R4: `codex/.agents/skills/` contains exactly the four real directories
  (`drain`, `build`, `autopilot`, `evals`) plus one symlink per
  already-working `antigravity/.agents/skills/*` entry, INCLUDING
  `_shared/` (16 symlinks total) — no directory under `codex/` holds
  copied *content* for any of those 15 skills or `_shared/`.
- R5: A live test (scripted, re-runnable, with an explicit
  no-`codex`-binary manual-pending path per Solution item 5) proves, from
  this repo's actual root: (a) whether skill discovery is relative to the
  `--cd`/cwd directory or to the git repo root (per the Solution section's
  caveat), applying the documented fallback (root-level
  `.agents -> codex/.agents` symlink) if the cwd-relative reading is
  wrong; (b) using whichever mechanism R5(a) established works, `codex
  exec` auto-triggers at least one already-working symlinked skill (e.g.
  `list-specs`) with a natural-language prompt; and (c) for at least one of
  the four new skills (e.g. `drain`), a plain natural-language prompt
  matching its description does NOT trigger it, while explicit
  `$drain`-style invocation (or the closest working Codex syntax) DOES read
  its SKILL.md. Record the actual result of each of (a)/(b)/(c) (works /
  partially works / does not work / manual-pending — codex not installed)
  in `codex/README.md` — a negative result on (b) or (c) is an acceptable,
  documented outcome, not a spec failure; a negative result on (a) requires
  applying the fallback before scoring (b)/(c).
- R6: CLAUDE.md's mirror-convention section is updated to describe the
  three-way `.claude/` → `antigravity/` → `codex/` relationship (copies →
  copies → symlinks-plus-four-real-skills) and extends the
  `Touch:`-discipline sentence to cover the four codex skill wrappers and
  the symlink-maintenance obligation from Solution item 3.
- R7: `.claude-plugin/plugin.json` version is bumped in the same commit
  that adds `codex/`.

## Out of scope

- Building Codex-native equivalents for any of the ~15 skills that already
  work unmodified via symlink into `antigravity/.agents/skills/` (scout,
  critic, verifier, implementation-worker, idea, breakdown, distill, gate,
  onboard, design, handoff, factcheck, list-specs, prioritize, workboard).
- A Codex port of the `gate` skill targeting Codex's richer native hook
  system (`hooks.json` / `config.toml [hooks]`) — noted as a promising
  future direction in the Problem section, not this spec's job.
- Any change to Antigravity's own workflow-vs-skill split, or retrofitting
  Antigravity with an `allow_implicit_invocation`-style gating mechanism —
  Antigravity has no such mechanism today and none is proposed here.
- Filing or fixing the upstream Codex bugs (#19695, #10585, #23454) —
  this spec treats them as a documented risk to test around, not something
  this repo can fix.
- CI/automated re-verification of the live `codex exec` checks (R5) on
  every push — Codex CLI is an external, evolving binary; re-verification
  is a manual maintainer step noted in `codex/README.md`, not a gated CI
  job.
- Making symlinks work on Windows checkouts — this repo's tooling already
  assumes a POSIX dev environment (macOS/Linux) elsewhere; no new
  cross-platform guarantee is added here.

## Acceptance criteria

- [ ] `test -f codex/README.md` and it names the `--cd codex` invocation
  convention and contains a "What degrades" heading (covers R1)
- [ ] `test -f codex/.agents/skills/drain/SKILL.md && test -f codex/.agents/skills/drain/agents/openai.yaml`
  (and the same pair for build, autopilot, evals) — covers R2
- [ ] `grep -q "allow_implicit_invocation: false" codex/.agents/skills/drain/agents/openai.yaml`
  (and for build, autopilot, evals) — covers R2
- [ ] A `verifier`-agent judgment pass confirms each of the four SKILL.md
  bodies inline-covers its `.claude/skills/<name>/SKILL.md` counterpart's
  execution steps (not merely a pointer to another file) — covers R3; this
  is explicitly a content-judgment check, not a scripted metric (a prior
  word-count-based draft of this criterion was dropped as neither
  necessary nor sufficient)
- [ ] `diff <(ls antigravity/.agents/skills | grep -v -E '^drain$') <(ls codex/.agents/skills | grep -v -E '^(drain|build|autopilot|evals)$')`
  produces no output (this includes `_shared` on both sides; the left-side
  filter excludes `antigravity/.agents/skills/drain`, a non-skill script
  bundle with no `SKILL.md` that supports
  `antigravity/.agents/workflows/drain.md` — it is not one of the 15
  already-working skills and was never symlinked), AND
  `find codex/.agents/skills -maxdepth 1 -type l` lists exactly the 15
  already-working skill names plus `_shared` (16 symlinks; no entry for
  drain, build, autopilot, or evals, which are real directories not
  symlinks) — covers R4
- [ ] A runnable script (e.g. `codex/verify-live.sh`) exists; if a `codex`
  binary is on PATH its output is pasted into `codex/README.md`'s
  verification section, otherwise the script prints and the README states
  "manual-pending — codex not installed" — covers R5
- [ ] `grep -q "codex/" CLAUDE.md` and the mirror-convention paragraph
  mentions all three of `.claude/`, `antigravity/`, and `codex/` — covers R6
- [ ] `git show --stat HEAD -- .claude-plugin/plugin.json codex/` (on the
  commit that adds `codex/`) shows both paths touched together — covers R7
- End-to-end (skips to manual-pending if `codex` is not installed, per R5):
  from a clean checkout of this repo, running the exact invocation
  documented in `codex/README.md` (either `codex exec --cd codex "list the
  specs in this project and their status"`, or the root-cwd fallback
  command if R5(a) found discovery is git-root-relative and required the
  `.agents -> codex/.agents` symlink) returns a correct scoped result,
  demonstrating the reuse-via-symlink mechanism works from the real repo
  layout, not just a scratch copy.

## Open questions

(none)

## Parallelization

Tasks 01 (root scaffold: symlinks + `codex/AGENTS.md` + plugin.json bump),
02 (drain + build skill wrappers), and 03 (autopilot + evals skill
wrappers) touch fully disjoint paths under `codex/.agents/skills/` and
share no undecided design — the frontmatter shape, `agents/openai.yaml`
policy key, and per-skill launch-authorization wording are all fixed by
this spec's R2/R3 text, so no two tasks would make the same open choice.
They form the first parallel-safe group.

Tasks 04 (live verification script + `codex/README.md`) and 05 (CLAUDE.md
mirror-convention update) both depend on the full structure from 01-03
existing, but touch disjoint files (`codex/README.md` +
`codex/verify-live.sh` vs. `CLAUDE.md`) and share no undecided design —
05's description of the three-way relationship doesn't depend on 04's live
verdicts. They form the second parallel-safe group, run after the first.

- Group: 01, 02, 03
- Group: 04, 05
