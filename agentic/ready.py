"""``agentic ready [--json]`` — the dispatch frontier.

Lists open tasks whose blocking dependencies are all done and whose Touch
paths (bd ``touch`` metadata) do not overlap any claimed (in-progress) task
or a higher-priority ready task, in priority order. The Touch-disjoint
co-admission and ordering are ported from
``.claude/skills/drain/drain_frontier.py`` onto bd tracker state.

``--json`` prints a JSON array; each element carries the documented fields
``id``, ``title``, ``priority`` (bd integer, 0 highest), and ``touch`` (the
sorted list of declared paths). The plain form prints one task per line.
"""

import json
import os

from agentic import frontier


def frontier_rows(cwd=None):
    """The ready frontier as a list of ``{id, title, priority, touch}`` dicts."""
    fr = frontier.compute_frontier(frontier.load_issues(cwd=cwd))
    return [
        {
            "id": i["id"],
            "title": i.get("title", ""),
            "priority": frontier.priority_of(i),
            "touch": sorted(frontier.issue_touch(i)),
        }
        for i in fr["admissible"]
    ]


def run(args=None):
    as_json = bool(getattr(args, "json", False))
    rows = frontier_rows(os.getcwd())

    if as_json:
        print(json.dumps(rows))
        return 0

    if not rows:
        print("no ready tasks")
        return 0
    for r in rows:
        touch = f"  [touch: {', '.join(r['touch'])}]" if r["touch"] else ""
        print(f"{r['id']}  P{r['priority']}  {r['title']}{touch}")
    return 0
