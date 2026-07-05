"""Shared spec-readiness helpers.

`open_questions_unresolved` implements the exact contract in
specs/list-specs/SPEC.md (R0, R0-note): a spec's `## Open questions`
section counts as *unresolved* only when its body is real, non-placeholder
prose. This module is intentionally standalone (no imports beyond `re`) so
both `specs/list-specs` and `specs/workboard-auto-triage` can depend on the
identical behavior without drift — see the R0-note coordination hazard.
"""

import re

_HEADING_RE = re.compile(r"^## Open questions[ \t]*$", re.MULTILINE)
_NEXT_HEADING_RE = re.compile(r"^## ", re.MULTILINE)
_RESOLVED_PLACEHOLDER_RE = re.compile(
    r"^\(none(?:\s*[—-].*)?\)$",
    re.IGNORECASE,
)


def open_questions_unresolved(spec_md_text: str) -> bool:
    """Return True iff spec_md_text has a non-empty, non-placeholder
    `## Open questions` body.

    Extracts the body between the `## Open questions` heading and the next
    `## ` heading (or EOF), collapses all internal whitespace (including
    newlines) to single spaces, and strips both ends. Returns False if the
    heading is absent, the collapsed body is empty, or the body is
    case-insensitively `none`, `(none)`, or `(none` followed by an
    em-dash/hyphen and any trailing text ending in `)`. Returns True for
    everything else.
    """
    heading_match = _HEADING_RE.search(spec_md_text)
    if heading_match is None:
        return False

    body_start = heading_match.end()
    next_heading_match = _NEXT_HEADING_RE.search(spec_md_text, body_start)
    body_end = next_heading_match.start() if next_heading_match else len(spec_md_text)
    raw_body = spec_md_text[body_start:body_end]

    collapsed = re.sub(r"\s+", " ", raw_body).strip()

    if not collapsed:
        return False
    if collapsed.lower() == "none":
        return False
    if _RESOLVED_PLACEHOLDER_RE.match(collapsed.lower()):
        return False

    return True
