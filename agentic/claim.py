"""``agentic claim <id>`` — atomically claim one task (SPEC S4).

The claim is bd's own atomic ``update --claim`` (sets assignee to the actor,
status to in_progress; idempotent if already claimed by you), wrapped in the
D8 lock and D9 sync sequence so the claim is committed and pushed as a
tracker write. A task already claimed by someone else fails cleanly with
bd's "already claimed" message — the loser of a two-clone race (R-C b).
"""

import os

from agentic import bd
from agentic.sync import sync_write


def claim(cwd, issue_id):
    """Claim ``issue_id`` under the write lock + sync rules. Raises BdError
    (with bd's "already claimed" message) if another actor holds it."""

    def _apply(root):
        return bd.bd_claim(issue_id, cwd=str(root))

    return sync_write(cwd, _apply)


def run(args):
    issue_id = args.id
    claim(os.getcwd(), issue_id)
    print(f"claimed {issue_id}")
    return 0
