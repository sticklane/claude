#!/usr/bin/env bash
# plugin-autorefresh: Stop hook that auto-refreshes the locally-installed
# "agentic" plugin once a version bump has landed on the marketplace source.
#
# The agentic-toolkit marketplace is sourced from GitHub (sticklane/claude),
# so a refresh only helps AFTER the bump commit is on the remote — a refresh
# against a merely-committed bump reinstalls the old version (the reason
# bin/submit exists instead of a pre-push git hook). This hook therefore
# compares the manifest as origin's default branch has it (the local
# remote-tracking ref, which the `git push` that shipped the bump updates)
# against the installed version, and runs bin/refresh-plugins only when the
# install is strictly behind. Firing at Stop means the refresh happens at the
# end of the very turn that pushed the bump.
#
# Companion to hooks/plugin-staleness (the warn-only SessionStart half):
# staleness detects at session start, autorefresh remedies at turn end.
# Auto-running the refresh here is deliberate and maintainer-requested
# (2026-07-16) — it does not change staleness-check's warn-only stance.
#
# Always exits 0 — a refresh failure must never block the session from
# stopping. Silent whenever there is nothing to do: no remote version, no
# determinable installed version, install equal to or ahead of the remote,
# or another refresh already in flight (single-flight lock; concurrent
# sessions' Stop hooks must not race the reinstall + cache prune).
#
# Antigravity and Codex are live-file runtimes with no install/cache step
# (see bin/refresh-plugins), so this skew — and this hook — is Claude-Code-only.
set -u

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"

parse_version() {
  grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]+"' \
    | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

# --- remote version: the manifest as origin's default branch has it -------
#     env stub wins (tests + explicit overrides), else the remote-tracking ref
remote_version="${PLUGIN_AUTOREFRESH_REMOTE_VERSION:-}"
if [ -z "$remote_version" ]; then
  ref="$(git -C "$root" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null)"
  [ -n "$ref" ] || ref="origin/main"
  remote_version="$(git -C "$root" show "$ref:.claude-plugin/plugin.json" 2>/dev/null \
    | parse_version)"
fi
[ -n "$remote_version" ] || exit 0

# --- installed version: env stub wins, else the shared live read ----------
installed_version="${PLUGIN_AUTOREFRESH_INSTALLED_VERSION:-}"
if [ -z "$installed_version" ] && [ "${PLUGIN_AUTOREFRESH_SKIP_CLI:-0}" != "1" ] \
   && [ -x "$root/bin/plugin-installed-version" ]; then
  installed_version="$("$root/bin/plugin-installed-version" 2>/dev/null || true)"
fi
[ -n "$installed_version" ] || exit 0

# --- refresh only when installed is strictly BEHIND the remote ------------
[ "$installed_version" != "$remote_version" ] || exit 0
lower="$(printf '%s\n%s\n' "$installed_version" "$remote_version" | sort -V | head -1)"
[ "$lower" = "$installed_version" ] || exit 0

# --- single-flight lock, with stale-takeover (a crashed run leaks the dir) -
lock="${PLUGIN_AUTOREFRESH_LOCK:-${TMPDIR:-/tmp}/plugin-autorefresh-$(id -u).lock}"
if ! mkdir "$lock" 2>/dev/null; then
  [ -n "$(find "$lock" -maxdepth 0 -mmin +10 2>/dev/null)" ] || exit 0
  rmdir "$lock" 2>/dev/null || true
  mkdir "$lock" 2>/dev/null || exit 0
fi
trap 'rmdir "$lock" 2>/dev/null' EXIT

refresh="${PLUGIN_AUTOREFRESH_CMD:-$root/bin/refresh-plugins}"
echo "plugin-autorefresh: installed agentic $installed_version is behind $remote_version on the marketplace source — running bin/refresh-plugins (a restart applies it)."
if ! "$refresh" >/dev/null 2>&1; then
  echo "plugin-autorefresh: bin/refresh-plugins FAILED — run it manually to update the installed plugin."
fi
exit 0
