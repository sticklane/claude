<!-- install-gates:checks -->
## Checks

- `bash scripts/check.sh` — canonical check (format-check, lint, tests). Run it green
  before calling work done; the Stop hook enforces it.
- The pre-commit hook runs format-check on staged files only
  (`git commit --no-verify` is the escape hatch).
<!-- /install-gates:checks -->
