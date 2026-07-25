#!/usr/bin/env bash
# Bring the session-refresh hook's own suite inside scripts/check.sh, whose
# glob is tests/test_*.sh — without this the hook is ungated.
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/hooks/session-refresh/test.sh"
