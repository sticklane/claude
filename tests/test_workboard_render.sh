#!/usr/bin/env bash
# Hermetic render test for the workboard copy-buttons work
# (specs/workboard-copy-commands, R1/R2/R3/R5).
#
# Exports HOME + CLAUDE_CONFIG_DIR into a throwaway tree so the scan never
# touches Steven's real home, and passes the fixture repo as an EXPLICIT
# positional root (default_roots() would otherwise append Path.cwd()). The
# env vars are the ONLY test seam — no CLI flag is added for testability (R5).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
wb="$repo_root/.claude/skills/workboard/workboard.py"
fixtures_src="$here/fixtures/workboard"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

export HOME="$tmp/home"
export CLAUDE_CONFIG_DIR="$tmp/home/.claude"
mkdir -p "$CLAUDE_CONFIG_DIR"

# Copy the fixture tree and git-init the repo (find_repos only yields dirs
# with a .git, and git_info wants a real work tree).
mkdir -p "$tmp/tree"
cp -R "$fixtures_src/." "$tmp/tree/"
repo="$tmp/tree/demo-repo"
git init -q "$repo"

# A session record that lands in the 'stale' bucket: an old timestamp, cwd
# pointing at the fixture repo so it attaches to the repo card.
mkdir -p "$CLAUDE_CONFIG_DIR/projects/demo"
printf '%s\n' \
  "{\"type\":\"user\",\"message\":{\"content\":\"stale fixture session\"},\"cwd\":\"$repo\",\"gitBranch\":\"main\",\"timestamp\":\"2020-01-01T00:00:00Z\"}" \
  > "$CLAUDE_CONFIG_DIR/projects/demo/sess1.jsonl"

out="$tmp/wb.html"
python3 "$wb" "$repo" --out "$out" --actions-out "$tmp/a.sh" --quiet --stale-days 7

python3 - "$out" <<'PY'
import sys, re, html

out = open(sys.argv[1], encoding="utf-8").read()
fails = []
cwd_indep = re.compile(r"^(cd /|claude |python3 /|git -C /)")

# (a) every <code class="cmd"> is immediately followed by a copy button.
cmds = list(re.finditer(r'<code class="cmd">(.*?)</code>', out, re.S))
if not cmds:
    fails.append("no <code class=\"cmd\"> rendered at all")
for m in cmds:
    trailing = out[m.end():m.end() + 120]
    if 'class="copy-btn"' not in trailing:
        fails.append("code.cmd with no adjacent copy button: %r" % m.group(1)[:50])

# (b) every cmd, once entity-decoded, is executable from ~ (cwd-independent).
for m in cmds:
    dec = html.unescape(m.group(1))
    if not cwd_indep.match(dec):
        fails.append("cmd is not cwd-independent: %r" % dec[:70])

# (a, cont.) no BARE <code> (i.e. without class="cmd") whose decoded body is a
# command matching the same pattern — everything runnable got the treatment.
for m in re.finditer(r'<code(?!\s+class="cmd")[^>]*>(.*?)</code>', out, re.S):
    dec = html.unescape(m.group(1))
    if cwd_indep.match(dec):
        fails.append("bare <code> command left unconverted: %r" % dec[:70])

# (c) the repo-card handoff renders a runnable pickup command.
dec_out = html.unescape(out)
if not re.search(
    r'cd \S[^<]*&& claude "Read [^<]*and continue the work it describes"',
    dec_out,
):
    fails.append("handoff pickup command (cd ... && claude \"Read ...\") missing")

# (d) the copy handler is resilient and every branch ends in visible feedback.
for needle in ["navigator.clipboard &&", "writeText",
               "execCommand('copy')", "copied ✓", "press ⌘C"]:
    if needle not in out:
        fails.append("copy JS missing required fragment: %r" % needle)

if fails:
    print("FAIL: workboard render assertions")
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("PASS: workboard render (R1/R2/R3/R5) — %d cmd(s) checked" % len(cmds))
PY
