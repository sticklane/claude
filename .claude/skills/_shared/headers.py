"""Shared authored-header parsing for the toolkit's own skill scripts.

Task status and dependency state live in bd and are intentionally absent.
This module retains the authored `Priority:` parser and importlib bootstrap.

Reached the same way workboard reaches `viz`/`spec_readiness`:
`sys.path.insert(0, <.../_shared>)` then `import headers` — a regular import,
never path-loading (`_load_module`-by-path) for `headers.py` itself, which
would need a loader to load the loader.

Stdlib only; no side effects on import beyond compiling the regexes.
"""

import importlib.util
import re

# `Priority:` is bracket-tolerant but range-restricted to the
# toolkit's defined P0-P3 priorities. An out-of-range value (`P7`) does NOT
# match, so callers fall through to their own default (P2).
PRIORITY_RE = re.compile(r"^Priority:\s*\[?(P[0-3])\]?", re.MULTILINE)


def _load_module(name, path):
    """Load a Python file at `path` as a module named `name`, executing it.

    The importlib bootstrap the toolkit's scanner scripts each used
    to define byte-identically, now defined once here. Callers reach this via
    a regular `import headers` (see the module docstring), then call it to
    load `workboard.py` (which is not itself in `_shared/`)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
