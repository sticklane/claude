#!/usr/bin/env python3
"""Shared parser for runtime profiles' ``## Headless`` sections.

Single source of truth for two related jobs, so no consumer
(``.claude/skills/workboard/workboard.py``, ``.claude/skills/drain/reference.md``,
``evals/run.sh``) hand-rolls its own copy:

1. Resolve a runtime name to its ``## Headless`` command template — the first
   fenced shell block in ``runtimes/<name>.md``, with backslash continuation
   lines collapsed into one command and placeholders (``<prompt>`` etc.) left
   intact for the caller to substitute — or the sentinel string ``NONE`` when
   the section has no fenced block (no scriptable relaunch exists).

2. Derive a *match-shape* regex from that template for parsing an existing
   relaunch command back out of arbitrary text: the invocation prefix up to
   and including the quoted ``<prompt>`` argument, with literal-whitespace
   runs collapsed to ``\\s+`` (preserving today's ``BATON_CMD_RE`` tolerance
   for ``claude  -p`` / tab variants) and the prompt argument turned into
   ``"[^"]*"``.

Profiles are always resolved relative to this module's own directory, so a
consumer that scans many repos (workboard.py) still reads profiles from the
toolkit installation it ships from — never from a scanned target repo's tree.

The Headless-section contract itself is documented for profile authors in
``runtimes/README.md``.
"""

import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

#: Sentinel returned when a runtime has no scriptable headless relaunch.
NONE = "NONE"

#: Placeholder token a conforming ``## Headless`` block uses for the prompt.
PROMPT_TOKEN = "<prompt>"

#: The runtime resolved to when a requested one is missing.
DEFAULT_RUNTIME = "claude-code"

_MODULE_DIR = Path(__file__).resolve().parent


def _profile_path(name: str) -> Path:
    """Path to ``runtimes/<name>.md`` relative to this module's directory."""
    return _MODULE_DIR / f"{name}.md"


def _resolve_profile_path(name: str) -> Path:
    """Resolve a runtime name to a profile file.

    A missing profile is not an error: it falls back to the default runtime
    (``claude-code``) and logs a warning, so a workboard scan or a drain baton
    pass over a bad/missing runtime name degrades instead of crashing.
    """
    path = _profile_path(name)
    if path.exists():
        return path
    logger.warning(
        "runtime profile %r not found under %s; falling back to %r",
        name,
        _MODULE_DIR,
        DEFAULT_RUNTIME,
    )
    return _profile_path(DEFAULT_RUNTIME)


def _extract_section(text: str, heading: str) -> str:
    """Return the body of the ``## <heading>`` section (up to the next ``## ``)."""
    lines = text.splitlines()
    body: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line[3:].strip() == heading
            continue
        if in_section:
            body.append(line)
    return "\n".join(body)


def _first_fenced_block(section_text: str) -> list[str] | None:
    """Return the lines inside the first ```` ``` ```` fenced block, or None."""
    block: list[str] = []
    in_block = False
    for line in section_text.splitlines():
        if line.lstrip().startswith("```"):
            if in_block:
                return block
            in_block = True
            continue
        if in_block:
            block.append(line)
    return None


def _join_template(block_lines: list[str]) -> str:
    """Collapse backslash-continuation lines into one command string."""
    parts: list[str] = []
    for line in block_lines:
        token = line.strip()
        if not token:
            continue
        if token.endswith("\\"):
            token = token[:-1].rstrip()
        parts.append(token)
    return " ".join(parts)


def headless_template(name: str) -> str:
    """Return the joined ``## Headless`` template for ``name``, or ``NONE``.

    Placeholders (``<prompt>``, ``<allowlist>``, …) are preserved verbatim for
    the caller to substitute. Returns the sentinel ``NONE`` when the profile's
    ``## Headless`` section contains no fenced block (no scriptable relaunch).
    An unresolvable ``name`` falls back to ``claude-code`` with a logged
    warning; it never raises.
    """
    path = _resolve_profile_path(name)
    section = _extract_section(path.read_text(encoding="utf-8"), "Headless")
    block = _first_fenced_block(section)
    if block is None:
        return NONE
    return _join_template(block)


def derive_match_regex(template: str) -> "re.Pattern[str] | None":
    """Derive a match-shape regex from a joined Headless template.

    Takes the invocation prefix up to and including the quoted ``<prompt>``
    argument, collapses each run of literal whitespace to ``\\s+``, escapes
    every other literal chunk, and turns the quoted prompt argument into
    ``"[^"]*"``. Returns ``None`` when ``template`` is the ``NONE`` sentinel
    (or has no ``<prompt>`` placeholder) — there is nothing to match against.
    """
    if not template or template == NONE:
        return None

    first_line = template.splitlines()[0]
    quoted = f'"{PROMPT_TOKEN}"'
    sentinel = "\x00PROMPT\x00"

    if quoted in first_line:
        end = first_line.index(quoted) + len(quoted)
        prefix = first_line[:end].replace(quoted, sentinel)
    elif PROMPT_TOKEN in first_line:
        end = first_line.index(PROMPT_TOKEN) + len(PROMPT_TOKEN)
        prefix = first_line[:end].replace(PROMPT_TOKEN, sentinel)
    else:
        return None

    out: list[str] = []
    for chunk in re.split(r"(\s+)", prefix):
        if not chunk:
            continue
        if chunk.isspace():
            out.append(r"\s+")
        else:
            out.append(
                r'"[^"]*"'.join(re.escape(piece) for piece in chunk.split(sentinel))
            )
    return re.compile("".join(out))


def match_regex(name: str) -> "re.Pattern[str] | None":
    """Convenience: resolve ``name`` and derive its match-shape regex."""
    return derive_match_regex(headless_template(name))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: parse_headless.py <runtime-name>", file=sys.stderr)
        return 2
    print(headless_template(argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
