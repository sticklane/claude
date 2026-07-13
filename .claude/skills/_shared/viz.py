"""viz.py — shared status/timeline/DAG rendering primitives (pure stdlib).

Single source of truth for status colors, Gantt timelines, and dependency
DAGs so /workboard, agent-console, and /fleet render the same way instead of
each hand-rolling its own. See specs/shared-viz-renderer/SPEC.md.

Distribution: /workboard imports this module; agent-console vendors a
byte-identical copy (checked by its own conformance gate); /fleet's CSS
region is regenerated from --emit-fleet-css.
"""
# viz-sha256: 168aadae500cdb69f410fe06d30f98039cb2b26bb2f08a62c97409c521090dc5

import argparse
import hashlib
import html
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical status model
# ---------------------------------------------------------------------------

# Canonical token -> SVG/CSS-fallback hex. Seeded from agent-console's DAG
# palette (running/open/done); failed/stale/blocked are new.
STATUS_HEX: dict[str, str] = {
    "running": "#d98a63",
    "open": "#6ea3c0",
    "done": "#3a4150",
    "failed": "#c96262",
    "stale": "#5a6070",
    "blocked": "#d9b063",
}

# Every real status term in use across agent-console.py, workboard.py, and
# fleet/reference.md, mapped to one canonical token.
_STATUS_ALIASES: dict[str, str] = {
    "running": "running",
    "in-progress": "running",
    "in_progress": "running",
    "claimed": "running",
    "active": "running",
    "open": "open",
    "pending": "open",
    "todo": "open",
    "ready": "open",
    "queued": "open",
    "done": "done",
    "completed": "done",
    "closed": "done",
    "deferred": "done",
    "skipped": "done",
    "failed": "failed",
    "error": "failed",
    "recent": "stale",
    "stale": "stale",
    "idle": "stale",
    "blocked": "blocked",
}


def canonical_status(raw: str | None) -> str:
    """Map any known status term (case-insensitive) to one of the 6 canonical
    tokens; any unlisted term (including None/empty) maps to "open" rather
    than raising."""
    return _STATUS_ALIASES.get((raw or "").strip().lower(), "open")


# ---------------------------------------------------------------------------
# dag() — SVG dependency DAG
# ---------------------------------------------------------------------------

# Fill, edge stroke, and title-text colors stay fixed regardless of status;
# only the node stroke + number varies (by STATUS_HEX). Lifted from
# agent-console.py's _dep_graph_svg/_task_stroke (colors verbatim).
_DAG_NODE_FILL = "#161922"
_DAG_EDGE = "#2f3644"
_DAG_TEXT = "#c7ccd6"

_DAG_NODE_W, _DAG_NODE_H, _DAG_GAP_X, _DAG_GAP_Y, _DAG_PAD = 150, 30, 46, 12, 6


def dag(tasks: list[dict]) -> str:
    """Inline SVG dependency DAG, laid out left-to-right by dependency depth
    (longest-path layering, cycle-guarded Bezier edges). Layout lifted
    verbatim from agent-console.py:891-958. Node stroke + number text use
    STATUS_HEX[canonical_status(status)]; fill/edge/label stay the named
    constants above. Returns "" when there are no in-list edges."""
    by = {t["num"]: t for t in tasks}
    edges = [(d, t["num"]) for t in tasks for d in t["deps"] if d in by]
    # Edge-less specs normally get no graph, but a blocker must stay visible
    # even when its spec has no dependency edges.
    if not edges and not any(t.get("blocker") for t in tasks):
        return ""

    # longest-path layering (cycle-guarded)
    memo: dict[int, int] = {}
    stack: set[int] = set()

    def layer(num: int) -> int:
        if num in memo:
            return memo[num]
        t = by.get(num)
        if not t or num in stack:
            return 0
        stack.add(num)
        deps = [d for d in t["deps"] if d in by]
        v = 0 if not deps else 1 + max(layer(d) for d in deps)
        stack.discard(num)
        memo[num] = v
        return v

    cols: dict[int, list[int]] = {}
    for t in sorted(tasks, key=lambda t: t["num"]):
        cols.setdefault(layer(t["num"]), []).append(t["num"])

    W, H, GX, GY, PAD = _DAG_NODE_W, _DAG_NODE_H, _DAG_GAP_X, _DAG_GAP_Y, _DAG_PAD
    pos = {}
    for lx, nums in cols.items():
        for iy, num in enumerate(nums):
            pos[num] = (PAD + lx * (W + GX), PAD + iy * (H + GY))
    width = PAD * 2 + (max(cols) + 1) * (W + GX) - GX
    height = PAD * 2 + max(len(v) for v in cols.values()) * (H + GY) - GY

    paths = []
    for src, dst in edges:
        x1, y1 = pos[src][0] + W, pos[src][1] + H / 2
        x2, y2 = pos[dst]
        y2 += H / 2
        cx = (x1 + x2) / 2
        paths.append(
            f'<path class="viz-edge" d="M{x1},{y1} C{cx},{y1} {cx},{y2} {x2},{y2}" '
            f'fill="none" stroke="{_DAG_EDGE}" stroke-width="1.3"/>'
        )

    nodes = []
    for num, t in by.items():
        x, y = pos[num]
        canon = canonical_status(t.get("status"))
        stroke = STATUS_HEX[canon]
        label = html.escape(str(t.get("title") or "")[:17])
        # Blocker badge: who unblocks this node — a human (ask/no unblock
        # step recorded) or an agent recheck (Unblock: run/agent).
        badge = ""
        blocker = t.get("blocker")
        if blocker in ("human", "agent"):
            glyph = "✋" if blocker == "human" else "⟳"  # ✋ / ⟳
            hint = (
                "human-blocked: needs an answer or decision"
                if blocker == "human"
                else "agent-unblockable: recheck step recorded"
            )
            badge = (
                f'<text class="viz-blocker viz-blocker-{blocker}" '
                f'x="{x + W - 16}" y="{y + 19}" font-size="12">'
                f"<title>{hint}</title>{glyph}</text>"
            )
        nodes.append(
            f'<g class="viz-node" opacity="{0.55 if canon == "done" else 1}">'
            f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="6" '
            f'fill="{_DAG_NODE_FILL}" stroke="{stroke}" stroke-width="1.4"/>'
            f'<text x="{x + 9}" y="{y + 19}" font-family="ui-monospace,Menlo,monospace" '
            f'font-size="11" fill="{stroke}" font-weight="700">{html.escape(str(num))}</text>'
            f'<text x="{x + 32}" y="{y + 19}" font-family="-apple-system,system-ui,sans-serif" '
            f'font-size="11" fill="{_DAG_TEXT}">{label}</text>{badge}</g>'
        )

    return (
        f'<div class="viz-graphwrap"><svg viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-label="task dependency graph">{"".join(paths)}{"".join(nodes)}</svg></div>'
    )


# ---------------------------------------------------------------------------
# timeline() — HTML Gantt
# ---------------------------------------------------------------------------

_EMPTY_TIMELINE = '<div class="viz-empty">No timeline data.</div>'


def timeline(rows: list[dict]) -> str:
    """HTML Gantt: one .viz-lane/.viz-bar per row. Each bar's left/width is
    normalized to [min(start_ts), now], width floored at 0.75% so short
    bars stay visible; rows are ordered by start_ts. Bar class is
    viz-{canonical_status(status)} so VIZ_CSS colors it with zero host
    wiring. Empty input returns a fixed empty-state string. A row with no
    start_ts raises ValueError (caller contract, not silent)."""
    if not rows:
        return _EMPTY_TIMELINE

    for row in rows:
        if row.get("start_ts") is None:
            raise ValueError(f"row missing start_ts: {row!r}")

    ordered = sorted(rows, key=lambda r: r["start_ts"])
    t0 = ordered[0]["start_ts"]
    t1 = time.time()
    span = (t1 - t0) or 1.0

    lanes = []
    for row in ordered:
        start = row["start_ts"]
        end = row["end_ts"] if row.get("end_ts") is not None else t1
        left = (start - t0) / span * 100
        bar_width = max((end - start) / span * 100, 0.75)
        canon = canonical_status(row.get("status"))
        label = html.escape(str(row.get("label") or ""))
        tooltip = html.escape(str(row.get("tooltip") or ""))
        name = (
            f'<a href="{html.escape(row["href"])}">{label}</a>'
            if row.get("href")
            else label
        )
        lanes.append(
            f'<div class="viz-lane">'
            f'<div class="name">{name}</div>'
            f'<div class="viz-track"><div class="viz-bar viz-{canon}" '
            f'style="left:{left:.3f}%;width:{bar_width:.3f}%" title="{tooltip}"></div></div>'
            f"</div>"
        )

    return "".join(lanes)


# ---------------------------------------------------------------------------
# VIZ_CSS — shared structural stylesheet
# ---------------------------------------------------------------------------

_BAR_COLOR_RULES = "\n".join(
    f".viz-bar.viz-{token} {{ background: var(--viz-{token}, {hexval}); }}"
    for token, hexval in STATUS_HEX.items()
)

VIZ_CSS = f"""\
.viz-lane {{ display: grid; grid-template-columns: 180px 1fr; align-items: center; gap: 10px; padding: 4px 0; }}
.viz-lane .name {{ font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.viz-track {{ position: relative; height: 10px; border-radius: 4px; background: rgba(128, 128, 128, 0.25); }}
.viz-bar {{ position: absolute; top: 0; height: 10px; border-radius: 4px; min-width: 4px; }}
{_BAR_COLOR_RULES}
.viz-axis {{ display: grid; grid-template-columns: 180px 1fr; gap: 10px; margin-top: 6px; }}
.viz-axis div {{ display: flex; justify-content: space-between; font-size: 11px; font-variant-numeric: tabular-nums; color: var(--viz-muted, #898781); }}
.viz-graphwrap {{ background: {_DAG_NODE_FILL}; border-radius: 8px; padding: 8px; display: inline-block; }}
/* .viz-node/.viz-edge carry no rules here on purpose: their colors are
   per-node inline SVG attributes (dag()'s STATUS_HEX lookup), and a CSS
   rule targeting them would win the cascade over those attributes and
   flatten every node/edge to one color. The classes exist as host hooks. */
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _emit_fleet_css() -> None:
    print("/* >>> viz:timeline-css BEGIN */")
    print(VIZ_CSS, end="")
    print("/* <<< viz:timeline-css END */")


def _self_sha256() -> str:
    """sha256 of the module body below the `# viz-sha256:` header line."""
    src = Path(__file__).read_text()
    marker = "# viz-sha256:"
    idx = src.index(marker)
    body_start = src.index("\n", idx) + 1
    return hashlib.sha256(src[body_start:].encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="viz.py")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--emit-fleet-css",
        action="store_true",
        help="print VIZ_CSS wrapped in fleet sentinels",
    )
    group.add_argument(
        "--self-sha256", action="store_true", help="print sha256 of the module body"
    )
    args = parser.parse_args(argv)

    if args.emit_fleet_css:
        _emit_fleet_css()
    elif args.self_sha256:
        print(_self_sha256())
    return 0


if __name__ == "__main__":
    sys.exit(main())
