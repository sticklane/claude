#!/usr/bin/env bash
# plugin-staleness: SessionStart hook that warns when the installed "agentic"
# Claude Code plugin is behind the source repo's current version.
#
# This repo distributes itself as the `agentic` plugin; Claude Code caches the
# plugin's content at install time and that cache goes stale once new content
# lands and the source `.claude-plugin/plugin.json` version bumps (the remedy
# is the manual `bin/refresh-plugins`). This hook is the missing proactive
# half: it compares the source manifest's version against the installed
# version and surfaces a WARNING — never a silent block, never a non-zero
# blocking exit, never an auto-refresh with side effects the user didn't ask
# for. It only points at `bin/refresh-plugins`; running it stays the user's
# call.
#
# Silent (empty stdout, exit 0) whenever it cannot make a confident
# behind-comparison: no source manifest, no determinable installed version, or
# an installed version equal to / ahead of source. A repo that isn't a plugin
# checkout, or an up-to-date install, sees zero behavior change.
#
# Antigravity and Codex are live-file runtimes with no install/cache step
# (see bin/refresh-plugins), so this cache-version skew is Claude-Code-only.
set -u

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
manifest="$root/.claude-plugin/plugin.json"
[ -f "$manifest" ] || exit 0

# --- source version: the manifest at the repo root ------------------------
source_version="$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]+"' "$manifest" \
  | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
[ -n "$source_version" ] || exit 0

# --- installed version: env stub wins (tests + explicit overrides), else the
#     live `claude plugin list` read, mirroring bin/refresh-plugins' parse ---
installed_version="${PLUGIN_STALENESS_INSTALLED_VERSION:-}"
if [ -z "$installed_version" ] && [ "${PLUGIN_STALENESS_SKIP_CLI:-0}" != "1" ] \
   && command -v claude >/dev/null 2>&1; then
  installed_version="$(claude plugin list 2>/dev/null \
    | grep -o 'agentic@agentic-toolkit.*[0-9]\+\.[0-9]\+\.[0-9]\+' \
    | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+$' | head -1 || true)"
fi
[ -n "$installed_version" ] || exit 0

# --- compare: warn only when installed is strictly BEHIND source ----------
[ "$installed_version" != "$source_version" ] || exit 0
lower="$(printf '%s\n%s\n' "$installed_version" "$source_version" | sort -V | head -1)"
[ "$lower" = "$installed_version" ] || exit 0

cat <<EOF
plugin-staleness: the installed "agentic" plugin is version $installed_version but the source repo is at $source_version. Doctrine or skills may have changed since your plugin cache was built. Run bin/refresh-plugins to update the installed copy (this is a warning only — nothing is blocked and nothing was auto-refreshed).
EOF
exit 0
