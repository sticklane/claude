# ctx pre-commit hook (R16): write pending anchor updates whose re-anchored
# file is itself staged, and stage the touched note files. Best-effort — never
# blocks a commit.
"__CTX_BIN__" hooks pre-commit || true
