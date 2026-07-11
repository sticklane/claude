# Task 03: autopilot + evals codex skill wrappers

Status: in-progress
Depends on: none
Priority: P1
Budget: 35 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: codex/.agents/skills/autopilot/**, codex/.agents/skills/evals/**

## Goal

`codex/.agents/skills/autopilot/SKILL.md` and
`codex/.agents/skills/evals/SKILL.md` exist as real files with valid YAML
frontmatter, each inline-covering its `.claude/skills/<name>/SKILL.md`
counterpart's execution steps (paraphrased, content-coverage checked). Each
has `agents/openai.yaml` nested beneath it setting
`policy: { allow_implicit_invocation: false }`. `autopilot`'s SKILL.md gets
the Codex-adapted live-authorization-contract paragraph; `evals`'s does NOT
(per spec R3's explicit carve-out — its existing "human-only, paid headless
sessions" framing already states an unconditional guarantee).

## Touch

Only `codex/.agents/skills/autopilot/**` and `codex/.agents/skills/evals/**`.
Do not touch `codex/.agents/skills/drain/` or `.../build/` (task 02 owns
those) or any symlinked skill directory (task 01 owns those).

## Steps

1. Read `.claude/skills/autopilot/SKILL.md` (100 lines) and
   `.claude/skills/evals/SKILL.md` (57 lines) in full.
2. Write `codex/.agents/skills/autopilot/SKILL.md`: valid frontmatter,
   inline-paraphrased procedure covering autopilot's classification/scoping/
   verification-gate behavior.
3. Insert the Codex-adapted live-authorization-contract paragraph into
   autopilot's SKILL.md, adapted from `.claude/skills/autopilot/SKILL.md`'s
   own launch-authorization paragraph (the "target task" variant, same
   shape as drain's but naming a target task rather than a target queue —
   see task 02 for the drain example if useful as a template). State that
   `allow_implicit_invocation: false` blocks automatic description-match
   selection, so the agent cannot self-launch autopilot; a human must type
   the invocation explicitly (`$autopilot` in the TUI or `codex exec`, or
   via the `/skills` command).
4. Write `codex/.agents/skills/evals/SKILL.md`: valid frontmatter,
   inline-paraphrased procedure covering evals' scaffold-and-run behavior,
   preserving its "human-only, paid headless sessions" framing
   (`.claude/skills/evals/SKILL.md`'s description: "Human-only because every
   run spawns paid headless sessions."). Do NOT add a launch-authorization
   paragraph to evals — this is an intentional asymmetry with the other
   three skills, not an oversight.
5. Create `codex/.agents/skills/autopilot/agents/openai.yaml` and
   `codex/.agents/skills/evals/agents/openai.yaml`, each setting
   `policy: { allow_implicit_invocation: false }`.
6. Commit.

## Acceptance

- [ ] `test -f codex/.agents/skills/autopilot/SKILL.md && test -f codex/.agents/skills/autopilot/agents/openai.yaml`
- [ ] `test -f codex/.agents/skills/evals/SKILL.md && test -f codex/.agents/skills/evals/agents/openai.yaml`
- [ ] `grep -q "allow_implicit_invocation: false" codex/.agents/skills/autopilot/agents/openai.yaml`
- [ ] `grep -q "allow_implicit_invocation: false" codex/.agents/skills/evals/agents/openai.yaml`
- [ ] A `verifier` agent judgment pass confirms both SKILL.md bodies
  inline-cover their `.claude` counterpart's execution steps, that
  autopilot's body contains an explicit Codex-adapted launch-authorization
  paragraph, and that evals' body does NOT need one (its existing framing
  already reads as an unconditional guarantee)
