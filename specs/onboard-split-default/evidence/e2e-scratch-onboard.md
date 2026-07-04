# E2E: /onboard writes the orientation split (scratch repo)

Task 01 acceptance evidence. A throwaway Node repo (package.json + one
`node:test` test) was scaffolded, the modified onboard skill + toolkit
agents provisioned into it, and /onboard run headlessly:

```
claude -p "Use the onboard skill to set this repository up ..." \
  --permission-mode dontAsk --max-turns 40 \
  --allowed-tools "Read Grep Glob Bash Write Edit Task"
```

Result: AGENTS.md (21 lines) with all three
sections and commands actually run; CLAUDE.md (20 lines) with the
`@AGENTS.md` bridge line in its first 10 lines. Both well under 200 lines.

## Produced AGENTS.md

```markdown
widget-lib is a tiny JavaScript utility library (npm package `widget-lib`) with no runtime dependencies, using Node's built-in test runner.

## Repo map

- `src/` — library source; `src/add.js` exports `{ add }`. New utilities go here.
- `test/` — tests using `node:test` + `node:assert`; one `*.test.js` per source file.
- `package.json` — package metadata and the `test` script. No build step.
- `README.md` — one-line human description.
- `.claude/` — agent config (agents, skills, permissions). Not shipped.

## Commands

- Install: `npm install` — no dependencies; creates `package-lock.json` only.
- Test: `npm test` — runs `node --test` (native runner, discovers `test/*.test.js`). Fast (<1s), exit 0 on pass.
- Build / lint / typecheck: none configured.

Requires Node with the stable `node --test` runner (verified on v26; `node:test` is stable since v18).

## State

No task tracking (`specs/`, `docs/TASKS.md`, none present). Open work is not recorded in-repo yet.
```

## Produced CLAUDE.md

```markdown
# widget-lib

@AGENTS.md

Orientation (repo map, commands, state) lives in AGENTS.md above. This file
holds conventions and gotchas only.

## Conventions

- TDD: write the failing test in `test/<name>.test.js` first, then the
  implementation in `src/<name>.js`. `npm test` is the only gate.
- Tests use `node:test` and `node:assert/strict` — no test framework is
  installed, and none should be added without reason.
- Keep the library dependency-free. Adding a runtime dependency is a
  deliberate decision, not a convenience.
- CommonJS modules (`module.exports` / `require`), matching `src/add.js`.

## Checks

- `npm test` — run green before considering any change done.
```

## Session closing summary

```
The `.claude/settings.json` write was blocked by a protected-file rule (Claude Code won't let me modify settings files unattended). That's the one piece I can't create for you — I'll hand you the content below to drop in.

Here's where things stand.

## Created

**`AGENTS.md`** — orientation (purpose line, `## Repo map`, `## Commands`, `## State`), 19 lines.
**`CLAUDE.md`** — conventions + gotchas with the `@AGENTS.md` bridge on line 3, 22 lines.

## Verification evidence

| Command | Result |
|---|---|
| `npm test` | **exit 0** — `✔ add sums two numbers`, 1 pass / 0 fail, ~42ms |
| `node --version` | v26.4.0 (native `node:test` runner, stable since v18) |
| build / lint / typecheck | none configured — recorded as absent, not invented |

Module style (`module.exports` / CommonJS) and the `node:test` + `node:assert` convention were both confirmed against `src/add.js` and the passing suite before writing.

## Needs your hand — permissions

Create `.claude/settings.json` with this (matches exactly the verified commands, denies `git push`):

```json
{
  "permissions": {
    "allow": [
      "Bash(npm install)",
      "Bash(npm test)",
      "Bash(npm test -- *)",
      "Bash(node --test*)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)"
    ],
    "deny": [
      "Bash(git push *)"
    ]
  }
}
```

Want me to write this once you lift the protection, or would you rather paste it yourself?

## Next layer (not installed — your call)

- **`/gate`** — Stop-hook that blocks "done" until `npm test` passes, plus auto-format/protected-files. Worth it even here since `npm test` is the sole gate.
- **`REVIEW.md`** — repo-specific code-review tuning. Low value for a library this small; skip unless you plan to grow it.

Say the word on either, or on the settings.json.

Next stage: /idea <first feature> (human-launched)
```
