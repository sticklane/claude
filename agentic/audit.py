"""``agentic audit [--since DATE] [--dry-run]`` — measure tool use, file
regressions as tasks (SPEC statement 14; component "The audit job";
Migration step 7).

Reads Claude Code session transcripts (JSONL under ``~/.claude/projects`` by
default; overridable with ``AGENTIC_TRANSCRIPT_ROOT`` for testing and for
alternate runtimes) plus the bd tracker, and measures three tool-adoption
regression classes:

- ``code-exploration-bypass`` — raw Grep or grep-led shell search before any
                                Codebase-Memory query in that session. This is
                                an ordering signal, not a boundedness claim.
- ``verdict-schema-failure`` — verdict files that failed schema validation.
- ``spend-over-cap``       — dispatch spend over the configured cap
                             (best-effort: measured only where a spend signal
                             is available, else 0).

Each regression *class* with a non-zero count is filed as ONE tracker task
linked ``discovered-from`` a standing audit anchor issue. A second run files
nothing new: a class whose task is already open under the anchor is skipped
(dedup). ``--dry-run`` prints the measures and writes nothing.

agentprof owns the OTel/token-cost transcript pipeline (a separate Go tool),
so this module ships its own minimal JSONL reader rather than importing it.
Scheduling is out of band: run this by hand or from any scheduler (cron /
launchd / a Routine) — see the README's ``agentic audit`` note.
"""

import json
import os
import re
from pathlib import Path

from agentic import bd
from agentic.sync import sync_write

# The regression classes, in report order.
REGRESSION_CLASSES = (
    "code-exploration-bypass",
    "verdict-schema-failure",
    "spend-over-cap",
)

# The standing anchor every filed finding hangs off (discovered-from). Found
# by exact title; created on first file if absent.
ANCHOR_TITLE = "agentic audit: standing anchor for tool-adoption regressions"

_ENV_TRANSCRIPT_ROOT = "AGENTIC_TRANSCRIPT_ROOT"
# Optional best-effort spend signal (no metered ledger under the 2026-07-22
# pivot addendum — cost enforcement is advisory-plus-thin-guard). When both
# are set, a spend over the cap counts as one regression; otherwise 0.
_ENV_SPEND_USD = "AGENTIC_SPEND_USD"
_ENV_SPEND_CAP_USD = "AGENTIC_SPEND_CAP_USD"

# A "grep-led" Bash command: the first token (after optional leading
# VAR=val assignments) is grep/rg/ag — a raw structure search, as opposed to
# a pipeline that merely filters other output through grep.
_GREP_LED = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*(?:grep|rg|ag)\b")
_CBM_CLI = re.compile(
    r"(?:^|[\s;&|(])(?:\S*/)?(?:agentic-)?codebase-memory-mcp\s+cli\s+"
    r"(?:index_repository|list_projects|index_status|search_graph|trace_path|"
    r"detect_changes|query_graph|get_graph_schema|get_code_snippet|"
    r"get_architecture|search_code)\b"
)
_CBM_QUERY_TOOLS = {
    "index_repository",
    "list_projects",
    "index_status",
    "search_graph",
    "trace_path",
    "detect_changes",
    "query_graph",
    "get_graph_schema",
    "get_code_snippet",
    "get_architecture",
    "search_code",
}


def title_for(cls):
    """The tracker-task title filed for regression class ``cls``."""
    return f"audit regression: {cls}"


# --- transcript reading -----------------------------------------------------


def default_transcript_root():
    """Where Claude Code writes session transcripts, unless overridden."""
    override = os.environ.get(_ENV_TRANSCRIPT_ROOT)
    if override:
        return Path(override)
    return Path.home() / ".claude" / "projects"


def discover_transcripts(root):
    """Every ``*.jsonl`` transcript under ``root`` (recursively)."""
    root = Path(root)
    if not root.exists():
        return []
    return sorted(root.rglob("*.jsonl"))


def _records(path):
    """Parseable JSON records from one transcript file."""
    try:
        text = Path(path).read_text()
    except (OSError, UnicodeDecodeError):
        return []
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records


def _tool_uses(rec):
    """The ``tool_use`` blocks in an assistant record (empty otherwise)."""
    if not isinstance(rec, dict) or rec.get("type") != "assistant":
        return []
    content = (rec.get("message") or {}).get("content") or []
    return [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]


def _before(rec, since):
    """True iff ``rec``'s ISO timestamp is strictly before ``since`` (a
    ``YYYY-MM-DD`` day). A record with no timestamp is never filtered out —
    ISO timestamps sort lexically, so a prefix compare is exact."""
    if not since:
        return False
    ts = rec.get("timestamp") if isinstance(rec, dict) else None
    if not ts:
        return False
    return str(ts)[:10] < since


# --- detectors --------------------------------------------------------------


def is_raw_search(tool):
    """Whether a tool starts raw grep-like exploration."""
    name = tool.get("name")
    if name == "Grep":
        return True
    if name == "Bash":
        cmd = (tool.get("input") or {}).get("command", "") or ""
        return bool(_GREP_LED.match(cmd))
    return False


def is_codebase_memory_use(tool):
    """Whether a tool use invokes the Codebase-Memory skill, MCP, or CLI."""
    name = str(tool.get("name") or "")
    inp = tool.get("input") or {}
    if name == "Skill":
        skill = str(inp.get("skill") or inp.get("command") or "").strip()
        return skill.rsplit(":", 1)[-1] == "codebase-memory"
    if name == "Bash":
        return bool(_CBM_CLI.search(str(inp.get("command") or "")))
    normalized = name.lower().replace("-", "_")
    return (
        "codebase_memory" in normalized
        and any(normalized.endswith("_" + query) for query in _CBM_QUERY_TOOLS)
    )


def _is_verdict_schema_failure(rec):
    """A tool result recording a rejected (schema-invalid) verdict file.

    Matches the exact message ``agentic verdict`` emits on a bad file, scanned
    only within tool-result records so assistant prose can't false-positive.
    """
    if not isinstance(rec, dict) or rec.get("type") != "user":
        return False
    content = (rec.get("message") or {}).get("content")
    return "verdict file failed schema validation" in json.dumps(content)


def _measure_spend_over_cap():
    """Best-effort: 1 if a known spend signal exceeds the configured cap.

    No metered ledger exists under the pivot addendum, so this reads the
    optional ``AGENTIC_SPEND_USD`` / ``AGENTIC_SPEND_CAP_USD`` env pair when a
    scheduler supplies one, and reports 0 otherwise (never a fabricated
    number).
    """
    try:
        spend = float(os.environ[_ENV_SPEND_USD])
        cap = float(os.environ[_ENV_SPEND_CAP_USD])
    except (KeyError, ValueError):
        return 0
    return 1 if spend > cap else 0


# --- measurement ------------------------------------------------------------


def measure(transcript_paths, *, since=None, cwd=None):
    """Count each regression class across ``transcript_paths``.

    ``cwd`` is accepted for symmetry with tracker-aware callers and future
    tracker-sourced measures; the current measures are transcript- and
    env-sourced.
    """
    counts = {cls: 0 for cls in REGRESSION_CLASSES}
    for path in transcript_paths:
        used_codebase_memory = False
        for rec in _records(path):
            if _before(rec, since):
                if any(is_codebase_memory_use(tool) for tool in _tool_uses(rec)):
                    used_codebase_memory = True
                continue
            for tool in _tool_uses(rec):
                if is_codebase_memory_use(tool):
                    used_codebase_memory = True
                elif not used_codebase_memory and is_raw_search(tool):
                    counts["code-exploration-bypass"] += 1
            if _is_verdict_schema_failure(rec):
                counts["verdict-schema-failure"] += 1
    counts["spend-over-cap"] = _measure_spend_over_cap()
    return counts


# --- filing -----------------------------------------------------------------


def _anchor_ids(export):
    return {obj["id"] for obj in export if obj.get("title") == ANCHOR_TITLE}


def _export_objs(root):
    out = []
    for line in (bd.bd_export(cwd=str(root)) or "").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _ensure_anchor(root):
    """The anchor issue's id — reusing an existing one, else creating it."""
    existing = _anchor_ids(_export_objs(root))
    if existing:
        return sorted(existing)[0]
    return bd.bd_create(
        ANCHOR_TITLE,
        description=(
            "Standing anchor for the scheduled `agentic audit` job. Each "
            "measured tool-adoption regression class is filed as one task "
            "linked discovered-from this issue."
        ),
        priority=2,
        cwd=str(root),
    )


def _open_finding_titles(root, anchor_id):
    """Titles of still-open issues already filed discovered-from the anchor
    (dedup key — a closed prior finding does not suppress a re-file)."""
    titles = set()
    for obj in _export_objs(root):
        if obj.get("status") == "closed":
            continue
        for dep in obj.get("dependencies") or []:
            if dep.get("type") == "discovered-from" and (
                dep.get("depends_on_id") == anchor_id
            ):
                titles.add(obj.get("title", ""))
    return titles


def file_findings(cwd, counts):
    """File one task per non-zero regression class, deduped against open
    findings. Returns the list of titles newly filed (possibly empty)."""

    def _apply(root):
        anchor = _ensure_anchor(root)
        already = _open_finding_titles(root, anchor)
        filed = []
        for cls in REGRESSION_CLASSES:
            if counts.get(cls, 0) <= 0:
                continue
            title = title_for(cls)
            if title in already:
                continue  # dedup: an open finding for this class already exists
            bd.bd_create(
                title,
                deps=[f"discovered-from:{anchor}"],
                description=(
                    f"agentic audit measured {counts[cls]} {cls} occurrence(s). "
                    f"Investigate the regression and close the gap."
                ),
                priority=2,
                cwd=str(root),
            )
            already.add(title)
            filed.append(title)
        return filed

    return sync_write(cwd, _apply)


# --- report / entrypoint ----------------------------------------------------


def _print_report(counts, *, dry_run):
    print(f"== agentic audit ({'dry-run' if dry_run else 'filing'}) ==")
    for cls in REGRESSION_CLASSES:
        print(f"  {cls}: {counts[cls]}")


def run(args=None):
    since = getattr(args, "since", None)
    dry_run = bool(getattr(args, "dry_run", False))

    root = default_transcript_root()
    paths = discover_transcripts(root)
    counts = measure(paths, since=since, cwd=os.getcwd())

    _print_report(counts, dry_run=dry_run)

    if dry_run:
        return 0

    filed = file_findings(os.getcwd(), counts)
    if filed:
        print(f"filed {len(filed)} finding(s): {', '.join(filed)}")
    else:
        print("no new findings to file")
    return 0
