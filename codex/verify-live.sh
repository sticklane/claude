#!/usr/bin/env bash
# codex/verify-live.sh — live verification (spec R5) of the Codex CLI port.
#
# Run from the REPO ROOT:  ./codex/verify-live.sh
# Re-run after any Codex CLI upgrade, then paste the SUMMARY block below into
# codex/README.md's "Live verification" section.
#
# It live-tests, against this repo's ACTUAL root (not a scratch copy):
#   (a) whether Codex skill discovery is cwd/`--cd`-relative or git-root-relative
#       — codex/.agents/ sits at a SUBDIRECTORY of the git root, so only the
#       cwd-relative reading finds the skills under `--cd codex` without a
#       root-level `.agents -> codex/.agents` fallback symlink;
#   (b) that an already-symlinked skill (list-specs) AUTO-triggers from a
#       plain natural-language prompt (proves the reuse-via-symlink mechanism);
#   (c) that a drain-shaped natural-language prompt does NOT auto-trigger the
#       drain skill (its agents/openai.yaml sets allow_implicit_invocation:
#       false), while an explicit `$drain` invocation is attempted.
#
# All model calls run under `--sandbox read-only` so that even if `drain` were
# to launch, it cannot claim leases, write, or spawn — the test observes
# whether the SKILL.md is READ, never lets a stage execute.
#
# No-codex-binary path (per docs/memory/unattended-worker-tool-limits.md): if
# `codex` is not on PATH, this prints a MANUAL-PENDING line and exits 0 rather
# than fabricating output.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 2

OUT_DIR="${VERIFY_OUT_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/codex-verify.XXXXXX")}"
mkdir -p "$OUT_DIR"

CODEX_TIMEOUT="${CODEX_TIMEOUT:-300}"
CODEX_FLAGS=(--cd codex --skip-git-repo-check --sandbox read-only --ephemeral --json)

section() { printf '\n=== %s ===\n' "$1"; }

# ---- no-binary manual-pending path ----------------------------------------
if ! command -v codex >/dev/null 2>&1; then
  echo "MANUAL-PENDING — codex not installed"
  echo "No 'codex' binary on PATH; the R5 live checks cannot run in this"
  echo "environment. Install the Codex CLI (https://developers.openai.com/codex)"
  echo "and re-run  ./codex/verify-live.sh  from the repo root."
  exit 0
fi

echo "codex binary:  $(command -v codex)"
echo "codex version: $(codex --version 2>&1)"
echo "results dir:   $OUT_DIR"

# run_codex NAME PROMPT -> prints codex exit code; JSONL to NAME_events.jsonl,
# final agent message to NAME_last.txt, both under $OUT_DIR.
run_codex() {
  local name="$1" prompt="$2"
  timeout "$CODEX_TIMEOUT" codex exec "${CODEX_FLAGS[@]}" \
    -o "$OUT_DIR/${name}_last.txt" "$prompt" \
    > "$OUT_DIR/${name}_events.jsonl" 2>&1
  echo "$?"
}

# A skill selected via Codex's own skill mechanism announces itself, e.g.
# `I'm using the `agentic:list-specs` skill because ...`. A model that instead
# grep-finds a file on disk emits no such announcement — that string is the
# discriminator between "skill mechanism fired" and "model read the file".
announced_skill() { # NAME SKILL
  grep -qiE "using the [^\"]*${2}[^\"]* skill" "$OUT_DIR/${1}_events.jsonl"
}

# ---- R5(a)+(b): discovery root + list-specs auto-trigger -------------------
section "R5(a)+(b): --cd codex discovery + list-specs auto-trigger"
ab_exit="$(run_codex ab "list the specs in this project and their status")"
echo "exit=$ab_exit   last message: $(tr '\n' ' ' < "$OUT_DIR/ab_last.txt")"
if grep -q "list_specs.py" "$OUT_DIR/ab_events.jsonl"; then
  a_verdict="WORKS — discovery is cwd/--cd-relative (skills found under codex/.agents via --cd codex; git root has no .agents, so no fallback symlink is needed)"
  b_verdict="WORKS — list-specs auto-triggered by description match, read its SKILL.md through the antigravity/ symlink, and ran the bundled list_specs.py"
else
  a_verdict="FAILED — no skill fired under --cd codex; discovery may be git-root-relative. Apply the fallback (ln -s codex/.agents .agents) and re-run. See $OUT_DIR/ab_events.jsonl"
  b_verdict="FAILED — list-specs did not run its bundled scanner (see $OUT_DIR/ab_events.jsonl)"
fi
echo "VERDICT (a): $a_verdict"
echo "VERDICT (b): $b_verdict"

# ---- R5(c-neg): drain-shaped NL prompt must NOT auto-trigger ---------------
section "R5(c-neg): drain-shaped natural-language prompt (expect NO auto-trigger)"
cneg_exit="$(run_codex cneg "Work through all the remaining unblocked tasks in this project's queue to completion without me restarting you at each step; dispatch a fresh worker per task in dependency order.")"
echo "exit=$cneg_exit"
if announced_skill cneg drain; then
  cneg_verdict="FAILED — drain was auto-selected as a skill despite allow_implicit_invocation: false (see $OUT_DIR/cneg_events.jsonl)"
else
  cneg_verdict="WORKS — drain did NOT auto-trigger; allow_implicit_invocation: false kept it out of the available-skill list (the model may still grep-find the file on disk, but that is not skill auto-selection)"
fi
echo "VERDICT (c-neg): $cneg_verdict"

# ---- R5(c-pos): explicit $drain -------------------------------------------
section "R5(c-pos): explicit \$drain invocation"
cpos_exit="$(run_codex cpos '$drain — before taking any action, load this skill and quote its Launch authorization rule back to me verbatim, then stop. Do not dispatch any workers.')"
echo "exit=$cpos_exit"
read_skill=no; via_mechanism=no
grep -q "allow_implicit_invocation" "$OUT_DIR/cpos_last.txt" 2>/dev/null && read_skill=yes
announced_skill cpos drain && via_mechanism=yes
if [ "$via_mechanism" = yes ]; then
  cpos_verdict="WORKS — \$drain invoked drain through the skill mechanism and its SKILL.md was read"
elif [ "$read_skill" = yes ]; then
  cpos_verdict="PARTIAL — the explicit-invocation skill mechanism is NOT exposed in 'codex exec' (matches upstream openai/codex #19695/#10585/#23454); \$drain was treated as literal text. The SKILL.md FILE was still reachable and read on disk, so its content surfaced, but not via \$-invocation"
else
  cpos_verdict="DOES NOT WORK — \$drain neither invoked the skill nor surfaced the SKILL.md content (see $OUT_DIR/cpos_events.jsonl)"
fi
echo "VERDICT (c-pos): $cpos_verdict"

# ---- SUMMARY (paste into codex/README.md) ---------------------------------
section "SUMMARY"
echo "(a) discovery root      : $a_verdict"
echo "(b) symlinked skill     : $b_verdict"
echo "(c-neg) no auto-trigger : $cneg_verdict"
echo "(c-pos) explicit invoke : $cpos_verdict"
echo ""
echo "Full JSONL event logs + last-message files: $OUT_DIR"
