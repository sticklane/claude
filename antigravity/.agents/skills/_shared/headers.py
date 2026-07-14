"""Shared task-header parsing for the toolkit's own skill scripts.

One home for the `Key: value` task-header regexes and the importlib bootstrap
helper that `workboard.py`, `list_specs.py`, and `prioritize_scan.py` each
otherwise defined or duplicated locally. Consolidating them here means the
same header reads one way everywhere — the `Priority:` divergence this module
closes had `/workboard` and `/prioritize` parsing `Priority: [P1]` two ways.

Reached the same way workboard reaches `viz`/`spec_readiness`:
`sys.path.insert(0, <.../_shared>)` then `import headers` — a regular import,
never path-loading (`_load_module`-by-path) for `headers.py` itself, which
would need a loader to load the loader.

Stdlib only; no side effects on import beyond compiling the regexes.
"""

import importlib.util
import re

# `Status:` tolerates the bracketed `[value]` shape (`Status: [done]`).
STATUS_RE = re.compile(r"^Status:\s*\[?([A-Za-z_-]+)\]?", re.MULTILINE)
# `Depends on:` — the raw remainder of the line (parsed into entries by callers).
DEPENDS_RE = re.compile(r"^Depends on:\s*(.*)$", re.MULTILINE)
# `Priority:` — bracket-tolerant like `Status:`, but range-restricted to the
# toolkit's defined P0-P3 priorities. An out-of-range value (`P7`) does NOT
# match, so callers fall through to their own default (P2).
PRIORITY_RE = re.compile(r"^Priority:\s*\[?(P[0-3])\]?", re.MULTILINE)


def _load_module(name, path):
    """Load a Python file at `path` as a module named `name`, executing it.

    The importlib bootstrap `list_specs.py` and `prioritize_scan.py` each used
    to define byte-identically, now defined once here. Callers reach this via
    a regular `import headers` (see the module docstring), then call it to
    load `workboard.py` (which is not itself in `_shared/`)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
