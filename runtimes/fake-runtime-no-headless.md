# Runtime profile: fake-runtime-no-headless

A minimal, deliberately synthetic runtime profile with NO `## Headless`
fenced block. It exists purely as a fixture for `test_parse_headless.py`'s
NONE-sentinel path (a runtime with no scriptable relaunch) — a real
example was needed for this until 2026-07-12, when live-testing corrected
`antigravity.md` to show it DOES have one (`agy -p`), leaving no real
profile to exercise this path. It maps no real CLI; do not select it for a
production repo.

## Tiers

| Tier          | Model            | Notes                                          |
| ------------- | ---------------- | ----------------------------------------------- |
| scout-tier    | fake-small        | Cheap, fast reconnaissance.                     |
| session-tier  | the CLI's default | Whatever the interactive session runs.          |
| deep-tier     | fake-large        | Recommended pin value — opt-in, not a default.  |
| frontier-tier | fake-large        | No distinct rung above deep; opt-in pin value.  |

## Headless

None exists. This synthetic profile has no non-interactive command
template — it exists only to give `test_parse_headless.py` a fixture for
the "no scriptable relaunch" (`NONE` sentinel) path.

## Orchestration

- **Primitive**: none — synthetic fixture, not a real runtime.

## Notes

- This profile is synthetic: nothing here maps to a real binary. It is a
  fixture for `test_parse_headless.py` only.
