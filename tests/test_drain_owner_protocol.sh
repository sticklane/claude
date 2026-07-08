#!/usr/bin/env bash
# Model-free test of the drain owner/CAS protocol's git mechanics (SPEC R9,
# specs/multi-session-coordination/SPEC.md — DRAIN-OWNER.md format pinned
# there: single-line Run-token:/Host:/Started:/Generation:/Spec: headers).
# Exercises five cases against throwaway repos in a temp dir. Never touches
# a real repo.
set -u

pass=0
fail=0
case_fail=0

note_pass() { pass=$((pass + 1)); }
note_fail() { # note_fail <description>
  fail=$((fail + 1))
  case_fail=1
  echo "FAIL: $1" >&2
}

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then note_pass; else note_fail "$desc"; fi
}

assert_not() { # assert_not <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then note_fail "$desc"; else note_pass; fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then note_pass; else note_fail "$desc (expected: '$expected', got: '$actual')"; fi
}

report_case() { # report_case <letter> <label>
  if [ "$case_fail" -eq 0 ]; then
    echo "PASS: ($1) $2"
  else
    echo "FAIL: ($1) $2"
  fi
  case_fail=0
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# The shipped skill text that case (e) cross-checks its local baton-adoption
# predicate against (SPEC R2). Resolved from this script's own location so the
# cross-check works regardless of the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFERENCE_MD="$SCRIPT_DIR/../.claude/skills/drain/reference.md"

mkrepo() { # mkrepo <dir>
  mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" config user.email test@example.com
  git -C "$1" config user.name "Test User"
}

# ---------------------------------------------------------------------------
# (a) CAS flip: after a simulated foreign flip, an exact-match replacement of
# "Status: pending" fails; grep confirms a single in-progress writer.
# ---------------------------------------------------------------------------
case_a() {
  case_fail=0
  local dir="$TMP/case-a"
  mkrepo "$dir"
  mkdir -p "$dir/specs/demo/tasks"
  local file="$dir/specs/demo/tasks/01-demo.md"
  cat > "$file" <<'EOF'
Status: pending
Depends on: none
Priority: P0
Budget: 10 turns

## Goal
demo
EOF
  git -C "$dir" add specs/demo/tasks/01-demo.md
  git -C "$dir" commit -qm "seed task"

  # Foreign flip: a different writer flips the task first and commits.
  sed -i '' 's/^Status: pending$/Status: in-progress/' "$file"
  git -C "$dir" add specs/demo/tasks/01-demo.md
  git -C "$dir" commit -qm "foreign: flip to in-progress"

  # Our worker re-reads HEAD immediately before flipping: the exact-match
  # CAS precondition on the literal "Status: pending" line must now fail.
  if grep -q '^Status: pending$' "$file"; then
    cas_would_proceed=1
  else
    cas_would_proceed=0
  fi
  assert_eq "(a) CAS flip: exact-match precondition rejects the stale flip" \
    0 "$cas_would_proceed"
  assert_eq "(a) CAS flip: exactly one in-progress writer" 1 \
    "$(grep -c '^Status: in-progress$' "$file")"
  report_case a "CAS flip"
}

# ---------------------------------------------------------------------------
# (b) owner lifecycle: claim commit, generation update, release commit leave
# the expected file states.
# ---------------------------------------------------------------------------
case_b() {
  case_fail=0
  local dir="$TMP/case-b"
  mkrepo "$dir"
  mkdir -p "$dir/specs/demo"
  local owner="$dir/specs/demo/DRAIN-OWNER.md"
  local token
  token="$(openssl rand -hex 8)"

  cat > "$owner" <<EOF
Run-token: $token
Host: test-host
Started: 2026-07-05T00:00:00Z
Generation: 1
Spec: specs/demo
EOF
  git -C "$dir" add specs/demo/DRAIN-OWNER.md
  git -C "$dir" commit -qm "drain: claim owner"
  assert "(b) owner lifecycle: claim commit leaves Generation: 1" \
    grep -q '^Generation: 1$' "$owner"

  # Baton pass updates Generation: in place, its own commit.
  sed -i '' 's/^Generation: 1$/Generation: 2/' "$owner"
  git -C "$dir" add specs/demo/DRAIN-OWNER.md
  git -C "$dir" commit -qm "drain: baton pass, generation 2"
  assert "(b) owner lifecycle: generation update recorded" \
    grep -q '^Generation: 2$' "$owner"

  # Release: terminal report deletes the owner file in a committed cleanup.
  git -C "$dir" rm -q specs/demo/DRAIN-OWNER.md
  git -C "$dir" commit -qm "drain: release owner"
  assert "(b) owner lifecycle: release commit removes owner file from disk" \
    test ! -e "$owner"
  assert_not "(b) owner lifecycle: owner file absent at HEAD" \
    git -C "$dir" show HEAD:specs/demo/DRAIN-OWNER.md
  report_case b "owner lifecycle"
}

# ---------------------------------------------------------------------------
# (c) path-scoped commit: a staged foreign file does not ride along with a
# path-scoped queue commit.
# ---------------------------------------------------------------------------
case_c() {
  case_fail=0
  local dir="$TMP/case-c"
  mkrepo "$dir"
  mkdir -p "$dir/specs/demo/tasks"
  printf 'Status: pending\n' > "$dir/specs/demo/tasks/01-demo.md"
  printf 'unrelated\n' > "$dir/other.txt"
  git -C "$dir" add -A
  git -C "$dir" commit -qm "seed"

  # A foreign file is staged in the working tree when we make our
  # path-scoped queue-state commit (R5: git add <explicit paths> + commit
  # limited to those paths, never -a or bare `git add .`).
  sed -i '' 's/^Status: pending$/Status: in-progress/' \
    "$dir/specs/demo/tasks/01-demo.md"
  printf 'foreign change\n' >> "$dir/other.txt"
  git -C "$dir" add other.txt

  git -C "$dir" commit -qm "drain: flip task 01" -- specs/demo/tasks/01-demo.md

  assert_eq "(c) path-scoped commit: commit touches only the task file" \
    "specs/demo/tasks/01-demo.md" \
    "$(git -C "$dir" show --name-only --pretty=format: HEAD | sed '/^$/d')"
  assert_not "(c) path-scoped commit: foreign file's staged change survives uncommitted" \
    git -C "$dir" diff --cached --quiet -- other.txt
  report_case c "path-scoped commit"
}

# ---------------------------------------------------------------------------
# (d) losing claim: two sequential claim commits with different Run-tokens;
# read-back at HEAD identifies exactly one winner, loser's token absent.
# ---------------------------------------------------------------------------
case_d() {
  case_fail=0
  local dir="$TMP/case-d"
  mkrepo "$dir"
  mkdir -p "$dir/specs/demo"
  local owner="$dir/specs/demo/DRAIN-OWNER.md"
  local token_a token_b
  token_a="$(openssl rand -hex 8)"
  token_b="$(openssl rand -hex 8)"

  cat > "$owner" <<EOF
Run-token: $token_a
Host: host-a
Started: 2026-07-05T00:00:00Z
Generation: 1
Spec: specs/demo
EOF
  git -C "$dir" add specs/demo/DRAIN-OWNER.md
  git -C "$dir" commit -qm "drain: claim owner (writer A)"

  cat > "$owner" <<EOF
Run-token: $token_b
Host: host-b
Started: 2026-07-05T00:00:01Z
Generation: 1
Spec: specs/demo
EOF
  git -C "$dir" add specs/demo/DRAIN-OWNER.md
  git -C "$dir" commit -qm "drain: claim owner (writer B)"

  assert_eq "(d) losing claim: HEAD identifies exactly one winner (writer B)" \
    "Run-token: $token_b" \
    "$(git -C "$dir" show HEAD:specs/demo/DRAIN-OWNER.md | grep '^Run-token:')"
  assert_not "(d) losing claim: loser's Run-token absent at HEAD" \
    grep -q "$token_a" "$owner"
  assert_eq "(d) losing claim: exactly one Run-token line at HEAD" 1 \
    "$(git -C "$dir" show HEAD:specs/demo/DRAIN-OWNER.md | grep -c '^Run-token:')"
  report_case d "losing claim"
}

# ---------------------------------------------------------------------------
# (e) baton adoption predicate: matching Run-token lines pass, mismatched
# fail, via the documented one-liner comparison.
# ---------------------------------------------------------------------------
case_e() {
  case_fail=0
  local dir="$TMP/case-e"
  mkdir -p "$dir"
  local token
  token="$(openssl rand -hex 8)"

  local owner="$dir/DRAIN-OWNER.md"
  local baton_match="$dir/baton-match.md"
  local baton_mismatch="$dir/baton-mismatch.md"

  cat > "$owner" <<EOF
Run-token: $token
Host: host-a
Started: 2026-07-05T00:00:00Z
Generation: 1
Spec: specs/demo
EOF
  cat > "$baton_match" <<EOF
Run-token: $token
Generation: 1
EOF
  cat > "$baton_mismatch" <<EOF
Run-token: $(openssl rand -hex 8)
Generation: 1
EOF

  # The documented one-liner (R2): a generation adopts the existing owner
  # iff the baton's Run-token: line matches DRAIN-OWNER.md's.
  adopt() { [ "$(grep '^Run-token:' "$1")" = "$(grep '^Run-token:' "$2")" ]; }

  assert "(e) baton adoption: matching Run-token adopts the existing owner" \
    adopt "$baton_match" "$owner"
  assert_not "(e) baton adoption: mismatched Run-token fails adoption" \
    adopt "$baton_mismatch" "$owner"

  # Cross-check the local adopt() predicate above against the SHIPPED skill
  # text so the two can't silently diverge. The R2 baton-lineage exception in
  # .claude/skills/drain/reference.md pins the grammar: a baton adopts the
  # existing owner iff its `Run-token:` line matches DRAIN-OWNER.md's — exactly
  # what adopt() compares. If that shipped prose ever changes the identity
  # field or the comparison target, this fails instead of the local
  # reimplementation passing on stale grammar. (Flattened to one line because
  # the pinned clause wraps across two lines in the reference.)
  assert "(e) baton adoption: shipped reference.md exists to cross-check against" \
    test -f "$REFERENCE_MD"
  local shipped
  shipped="$(tr '\n' ' ' < "$REFERENCE_MD")"
  assert "(e) baton adoption: shipped reference.md still pins the Run-token/DRAIN-OWNER.md predicate adopt() implements" \
    grep -Eq "baton.*Run-token:.*matches DRAIN-OWNER\.md" <<<"$shipped"
  report_case e "baton adoption predicate"
}

case_a
case_b
case_c
case_d
case_e

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
