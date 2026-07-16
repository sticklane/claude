#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny git repo whose existing source files source each other through a
# non-obvious chain, plus a two-requirement spec that extends that existing
# code WITHOUT spelling out which files each requirement touches. Because
# file-level dependencies are unclear from the spec text alone, /breakdown's
# step 2 must delegate to a `scout` agent to map them rather than reading the
# codebase into its own session.
set -eu

cd "$EVAL_DIR"
git init -q

mkdir -p lib bin specs/toolkit

# --- Existing code: a small CLI with a non-obvious sourcing chain ----------
# bin/cli.sh -> lib/args.sh -> lib/output.sh -> lib/colors.sh
# The chain is not described anywhere in the spec, so the dependency
# structure between the two requirements can only be learned from the code.

cat > lib/colors.sh <<'EOF'
#!/usr/bin/env bash
color_red() { printf '\033[31m%s\033[0m' "$1"; }
EOF

cat > lib/output.sh <<'EOF'
#!/usr/bin/env bash
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/colors.sh"
emit() { printf '%s\n' "$1"; }
EOF

cat > lib/args.sh <<'EOF'
#!/usr/bin/env bash
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/output.sh"
parse_args() { MODE="text"; for a in "$@"; do case "$a" in --mode=*) MODE="${a#--mode=}";; esac; done; }
EOF

cat > bin/cli.sh <<'EOF'
#!/usr/bin/env bash
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/../lib/args.sh"
parse_args "$@"
emit "mode=$MODE"
EOF
chmod +x bin/cli.sh

cat > specs/toolkit/SPEC.md <<'EOF'
# Toolkit CLI: output-mode and quiet extensions

## Problem

The CLI under `bin/cli.sh` supports only a single default text mode. Two
independent capabilities are wanted, but the existing sourcing chain
between `bin/`, `lib/args.sh`, and the output helpers is not documented —
which requirement touches which file must be determined from the code, not
assumed.

## Solution

Add a JSON output mode and a quiet flag. Each is a small, self-contained
capability; whether they can land in either order depends on which existing
library files each one has to modify, which the code — not this spec —
defines.

## Requirements

- R1: a `--json` flag makes the CLI emit its output as a JSON object
  instead of the plain `mode=<x>` line.
- R2: a `--quiet` flag suppresses all non-error output.

## Out of scope

- Any language other than bash; config files; new external dependencies.

## Acceptance criteria

- [ ] `bin/cli.sh --json` emits a JSON object (R1)
- [ ] `bin/cli.sh --quiet` prints nothing on success (R2)

## Open questions

(none)
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: toolkit CLI spec"
