# /evals reference: the breakdown scenario, verbatim

Contents: setup.sh · prompt.txt · assert.sh · allowed-tools.txt

The runner is [evals/run.sh](../../../evals/run.sh) — read it there
rather than duplicating it here. Runner and scenarios ship in the
toolkit repo, not with installs — not usable from plugin installs. Below are the four files of the
reference evalset `evals/breakdown/01-small-spec/`, verbatim, as the
template for scaffolding a new scenario. Its `assert.sh` keeps its failure
output under ~10 lines — one `ASSERT FAIL:` line per broken check, never a
transcript.

## setup.sh

```bash
#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo with a two-requirement spec and no open questions.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p src specs/demo

cat > src/greet.sh <<'EOF'
#!/usr/bin/env bash
echo "hello"
EOF
chmod +x src/greet.sh

cat > specs/demo/SPEC.md <<'EOF'
# Demo: greeting CLI pair

## Problem

`src/greet.sh` always prints a bare "hello" — it cannot greet a named
person — and the repo has no farewell counterpart at all.

## Solution

Two independent, dependency-free bash deliverables: extend the existing
greeting script in place, and add a sibling farewell script. They share
no files, so they can land in any order.

## Requirements

- R1: `src/greet.sh` accepts an optional name argument: `./src/greet.sh`
  prints `hello`, and `./src/greet.sh Ada` prints `hello Ada`.
- R2: a new executable `src/farewell.sh` prints `bye`, and
  `./src/farewell.sh Ada` prints `bye Ada`.

## Out of scope

- Any language other than bash; flags, help text, or i18n.

## Acceptance criteria

- [ ] `./src/greet.sh Ada` prints `hello Ada` (R1)
- [ ] `./src/greet.sh` still prints `hello` (R1)
- [ ] `test -x src/farewell.sh && ./src/farewell.sh Ada` prints `bye Ada` (R2)

## Open questions

(none)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: demo spec"
```

## prompt.txt

```
/breakdown specs/demo/SPEC.md
```

## assert.sh

```bash
#!/usr/bin/env bash
# Grades the /breakdown run. CWD is $EVAL_DIR; exit 0 = pass, non-zero
# with output explaining what failed.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

shopt -s nullglob
tasks=(specs/demo/tasks/[0-9][0-9]-*.md)
[ "${#tasks[@]}" -ge 2 ] || fail "expected >=2 specs/demo/tasks/NN-*.md files, found ${#tasks[@]}"

for t in "${tasks[@]}"; do
  grep -q "^Status:" "$t" || fail "$t has no Status: line"
  grep -q "^Depends on:" "$t" || fail "$t has no Depends on: line"
  grep -q "^## Acceptance" "$t" || fail "$t has no ## Acceptance section"
  awk '/^## Acceptance/{in_sec=1; next} /^## /{in_sec=0} in_sec' "$t" | grep -q '`' \
    || fail "$t Acceptance section has no backticked command"
done

grep -q "Parallelization" specs/demo/SPEC.md \
  || fail "specs/demo/SPEC.md gained no Parallelization section"

echo "assert: all checks passed (${#tasks[@]} task files)"
```

## allowed-tools.txt

```
Read,Edit,Write,Glob,Grep,Bash(git *),Task
```

`Task` is present because /breakdown fans out to `scout`/`critic`
agents, which the runner provisioned into the fixture's
`.claude/agents/`. Scenarios for non-fan-out skills omit this file and
inherit the runner's default allowlist.
