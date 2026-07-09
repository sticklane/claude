#!/usr/bin/env bash
# Mechanical fleet CSS drift gate (spec fleet-viz-css-resync, R1/R2).
#
# /fleet's reference.md carries a copied timeline-CSS block that must stay
# byte-identical to `viz.py --emit-fleet-css`'s output (the premise of
# shared-viz-renderer/04-migrate-fleet-reference). This gate runs the same
# diff the spec's acceptance criteria use and fails loudly if the copy in
# fleet/reference.md's `viz:timeline-css BEGIN`/`END` block ever diverges
# from viz.py's live output again.
#
# Output (R2): on success, exit 0 with NO output. On failure, print the
# unified diff naming the mismatch and exit 1.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
viz="$repo_root/.claude/skills/_shared/viz.py"
reference="$repo_root/.claude/skills/fleet/reference.md"

emitted="$(python3 "$viz" --emit-fleet-css)"
copied="$(awk '/viz:timeline-css BEGIN/,/viz:timeline-css END/' "$reference")"

if ! d="$(diff <(printf '%s\n' "$emitted") <(printf '%s\n' "$copied"))"; then
  echo "fleet CSS drift: fleet/reference.md's viz:timeline-css block differs from viz.py --emit-fleet-css"
  echo "$d"
  exit 1
fi
exit 0
