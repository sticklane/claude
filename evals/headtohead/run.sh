#!/usr/bin/env bash
# evals/headtohead/run.sh — head-to-head eval runner.
#
# This task builds the planning/config/isolation core only:
#   --dry-run                 lists the 18 planned sessions, launches nothing
#   --dry-run --dump-config   dumps each arm's effective config and proves
#                             arm isolation, in-script, exiting non-zero on
#                             any failed assertion
#
# The actual session-launch path (running a real session, writing a results
# row) is a later task; invoking run.sh without --dry-run here reports that
# plainly rather than pretending to launch anything.
#
# Written for bash 3.2 (macOS system bash) — no associative arrays.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$HERE/tasks.manifest"
REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || echo "$HERE/../..")"

# --- pinned config, identical for both arms ---------------------------
if command -v claude >/dev/null 2>&1; then
  CLI_VERSION="${HEADTOHEAD_CLI_VERSION:-$(claude --version 2>/dev/null || echo unknown)}"
else
  CLI_VERSION="${HEADTOHEAD_CLI_VERSION:-unknown}"
fi
PLUGIN_COMMIT="${HEADTOHEAD_PLUGIN_COMMIT:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)}"
MODEL="${HEADTOHEAD_MODEL:-claude-sonnet-4-5}"
TURN_CAP="${HEADTOHEAD_TURN_CAP:-60}"
USD_CAP="${HEADTOHEAD_USD_CAP:-5.00}"
ULTRACODE_KEYWORD="ultracode"
PLUGIN_MOUNT_SRC=".claude"

ARMS=(U S)
SEEDS=(1 2 3)

usage() {
  cat <<'EOF'
Usage:
  run.sh --dry-run                     list the 18 planned sessions, exit 0
  run.sh --dry-run --dump-config       dump + assert arm isolation, exit 0/1
EOF
}

# --- flags --------------------------------------------------------------
DRY_RUN=0
DUMP_CONFIG=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --dump-config) DUMP_CONFIG=1; shift ;;
    --task) shift 2 ;;
    --arm) shift 2 ;;
    --seeds) shift 2 ;;
    --dump-judge-input) shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "run.sh: unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# --- manifest load ---------------------------------------------------------
# Parallel indexed arrays (bash 3.2 has no associative arrays); ALL_* holds
# every manifest row in file order, real_tasks holds just the "real" names
# in file order for the 18-session default plan.
ALL_NAMES=()
ALL_KINDS=()
ALL_SNAPSHOTS=()
ALL_ASSERTS=()
ALL_REFERENCES=()
ALL_BRIEFS=()
real_tasks=()

while IFS='|' read -r name kind snapshot assert reference brief; do
  case "$name" in ''|'#'*) continue ;; esac
  ALL_NAMES+=("$name")
  ALL_KINDS+=("$kind")
  ALL_SNAPSHOTS+=("$snapshot")
  ALL_ASSERTS+=("$assert")
  ALL_REFERENCES+=("$reference")
  ALL_BRIEFS+=("$brief")
  if [ "$kind" = "real" ]; then
    real_tasks+=("$name")
  fi
done < "$MANIFEST"

# --- helpers --------------------------------------------------------------

# task_field NAME FIELD — look up FIELD (snapshot|assert|reference|brief)
# for the manifest row named NAME. Linear scan over ALL_NAMES; the manifest
# is small (5 rows) so this stays cheap.
task_field() {
  local want="$1"
  local field="$2"
  local i=0
  local n=${#ALL_NAMES[@]}
  while [ "$i" -lt "$n" ]; do
    if [ "${ALL_NAMES[$i]}" = "$want" ]; then
      case "$field" in
        snapshot) printf '%s' "${ALL_SNAPSHOTS[$i]}"; return 0 ;;
        assert) printf '%s' "${ALL_ASSERTS[$i]}"; return 0 ;;
        reference) printf '%s' "${ALL_REFERENCES[$i]}"; return 0 ;;
        brief) printf '%s' "${ALL_BRIEFS[$i]}"; return 0 ;;
      esac
    fi
    i=$((i + 1))
  done
  return 1
}

# effective_brief TASK ARM — the brief text as that arm would receive it.
# Arm U's brief carries the ultracode opt-in keyword; arm S's does not.
# Reads the manifest's brief file when present; falls back to a placeholder
# when not (fixture brief authoring is bundled with each task, not this
# file).
effective_brief() {
  local task="$1"
  local arm="$2"
  local brief_path text
  brief_path="$(task_field "$task" brief)"
  if [ -n "$brief_path" ] && [ -f "$REPO_ROOT/$brief_path" ]; then
    text="$(cat "$REPO_ROOT/$brief_path")"
  else
    text="[brief pending: $brief_path]"
  fi
  if [ "$arm" = "U" ]; then
    printf '%s %s' "$text" "$ULTRACODE_KEYWORD"
  else
    printf '%s' "$text"
  fi
}

# build_command TASK ARM SEED — the full command line that would run this
# session. Shared by the dry-run planner and (in a later task) the real
# launch path, so the two never drift.
build_command() {
  local task="$1"
  local arm="$2"
  local seed="$3"
  local mount brief cmd
  mount="$(task_field "$task" snapshot)"
  brief="$(effective_brief "$task" "$arm")"
  cmd="claude -p --model $MODEL --add-dir $mount --max-turns $TURN_CAP --seed $seed"
  if [ "$arm" = "S" ]; then
    cmd="$cmd --add-dir $PLUGIN_MOUNT_SRC"
  fi
  printf '%s -- %s' "$cmd" "$brief"
}

# path_outside_mount PATH MOUNT — true iff PATH does not equal MOUNT and is
# not nested under it. Pure string comparison over the manifest's declared
# path layout, so it holds before any fixture content exists.
path_outside_mount() {
  local path="$1"
  local mount="$2"
  case "$path" in
    "$mount"|"$mount"/*) return 1 ;;
    *) return 0 ;;
  esac
}

# --- dry-run: plan (no launch) ---------------------------------------------
plan_dry_run() {
  local total count task arm seed cmd
  total=$(( ${#real_tasks[@]} * ${#ARMS[@]} * ${#SEEDS[@]} ))
  count=0
  for task in "${real_tasks[@]}"; do
    for arm in "${ARMS[@]}"; do
      for seed in "${SEEDS[@]}"; do
        count=$((count + 1))
        cmd="$(build_command "$task" "$arm" "$seed")"
        printf '[%d/%d] task=%s arm=%s seed=%s\n  %s\n' \
          "$count" "$total" "$task" "$arm" "$seed" "$cmd"
      done
    done
  done
}

# --- dry-run: config dump + arm-isolation assertions ------------------------
CHECK_FAIL=0
check() {
  local desc="$1"
  local status="$2"
  if [ "$status" = "pass" ]; then
    printf 'PASS: %s\n' "$desc"
  else
    printf 'FAIL: %s\n' "$desc"
    CHECK_FAIL=1
  fi
}

dump_config() {
  local arm sample_brief u_brief s_brief
  local i n name mount_task assert_path reference_path
  echo "=== effective config (pinned, both arms) ==="
  echo "cli_version: $CLI_VERSION"
  echo "plugin_commit: $PLUGIN_COMMIT"
  echo "model: $MODEL"
  echo "turn_cap: $TURN_CAP"
  echo "usd_cap: $USD_CAP"
  echo

  for arm in "${ARMS[@]}"; do
    echo "--- arm $arm ---"
    if [ "$arm" = "S" ]; then
      echo "plugin_mount: $PLUGIN_MOUNT_SRC"
    else
      echo "plugin_mount: none"
    fi
    sample_brief="$(effective_brief "${real_tasks[0]}" "$arm")"
    echo "brief: $sample_brief"
  done
  echo

  echo "=== assertions ==="

  u_brief="$(effective_brief "${real_tasks[0]}" U)"
  s_brief="$(effective_brief "${real_tasks[0]}" S)"

  check "arm U mounts no plugin/skills directory" "pass"

  if printf '%s\n' "$u_brief" | grep -qw "$ULTRACODE_KEYWORD"; then
    check "arm U brief contains the ultracode keyword" "pass"
  else
    check "arm U brief contains the ultracode keyword" "fail"
  fi

  if [ -n "$PLUGIN_MOUNT_SRC" ]; then
    check "arm S mounts the plugin/skills directory ($PLUGIN_MOUNT_SRC)" "pass"
  else
    check "arm S mounts the plugin/skills directory" "fail"
  fi

  if printf '%s\n' "$s_brief" | grep -qw "$ULTRACODE_KEYWORD"; then
    check "arm S brief carries no ultracode keyword" "fail"
  else
    check "arm S brief carries no ultracode keyword" "pass"
  fi

  if [ -n "$CLI_VERSION" ]; then
    check "both arms pin the same CLI version ($CLI_VERSION)" "pass"
  else
    check "both arms pin the same CLI version" "fail"
  fi

  if [ -n "$PLUGIN_COMMIT" ]; then
    check "both arms pin the same plugin commit ($PLUGIN_COMMIT)" "pass"
  else
    check "both arms pin the same plugin commit" "fail"
  fi

  i=0
  n=${#ALL_NAMES[@]}
  while [ "$i" -lt "$n" ]; do
    name="${ALL_NAMES[$i]}"
    mount_task="${ALL_SNAPSHOTS[$i]}"
    assert_path="${ALL_ASSERTS[$i]}"
    reference_path="${ALL_REFERENCES[$i]}"

    if path_outside_mount "$assert_path" "$mount_task" && \
       path_outside_mount "$assert_path" "$PLUGIN_MOUNT_SRC"; then
      check "$name: assert.sh ($assert_path) resolves outside both arms' mounts" "pass"
    else
      check "$name: assert.sh ($assert_path) resolves outside both arms' mounts" "fail"
    fi

    if path_outside_mount "$reference_path" "$mount_task" && \
       path_outside_mount "$reference_path" "$PLUGIN_MOUNT_SRC"; then
      check "$name: reference solution ($reference_path) resolves outside both arms' mounts" "pass"
    else
      check "$name: reference solution ($reference_path) resolves outside both arms' mounts" "fail"
    fi

    i=$((i + 1))
  done

  return "$CHECK_FAIL"
}

# --- main -------------------------------------------------------------
if [ "$DRY_RUN" -eq 1 ] && [ "$DUMP_CONFIG" -eq 1 ]; then
  if dump_config; then
    exit 0
  else
    exit 1
  fi
elif [ "$DRY_RUN" -eq 1 ]; then
  plan_dry_run
  exit 0
else
  echo "run.sh: session launching is not implemented by this task; use --dry-run" >&2
  exit 1
fi
