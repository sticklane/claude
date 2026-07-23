"""``agentic`` command-line entrypoint.

Registers EVERY planned subcommand so sibling tasks stay Touch-disjoint on
their own modules: ``init`` is implemented here; the verbs later tasks fill
(ready, claim, verdict, resume, compose, ctx, inbox, demote) are registered
as stubs that exit 2 ("not implemented").
"""

import argparse
import sys

from agentic import audit, claim, initialize, ready, resume, verdict
from agentic.bd import BdError

# Verbs whose bodies belong to later tasks (06, 07, 11). Registered now as
# stubs so the subcommand surface is stable and disjoint. ready/resume (03)
# and claim/verdict (04) are implemented and routed to their modules below.
_STUB_SUBCOMMANDS = (
    "compose",
    "ctx",
    "inbox",
    "demote",
)


def _make_stub(name):
    def _run(_args):
        print(f"agentic {name}: not implemented", file=sys.stderr)
        return 2

    return _run


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agentic",
        description="Run the agent work pipeline over a pinned bd tracker.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Bootstrap the bd tracker from the committed JSONL (curated).",
    )
    p_init.set_defaults(func=initialize.run)

    p_ready = sub.add_parser(
        "ready", help="List the dispatch frontier (blockers done, Touch-disjoint)."
    )
    p_ready.add_argument(
        "--json", action="store_true", help="emit a JSON array of ready tasks"
    )
    p_ready.set_defaults(func=ready.run)

    p_resume = sub.add_parser(
        "resume", help="Show the frontier plus in-flight claims (who/what/since)."
    )
    p_resume.add_argument(
        "--json", action="store_true", help="emit the frontier + claims as JSON"
    )
    p_resume.set_defaults(func=resume.run)

    p_claim = sub.add_parser(
        "claim", help="Atomically claim one task (assignee=you, in_progress)."
    )
    p_claim.add_argument("id", help="the task id to claim")
    p_claim.set_defaults(func=claim.run)

    p_verdict = sub.add_parser(
        "verdict", help="Validate a worker's JSON result and record it on the task."
    )
    p_verdict.add_argument("id", help="the task id the verdict is for")
    p_verdict.add_argument(
        "--file", required=True, help="path to the worker's verdict JSON file"
    )
    p_verdict.set_defaults(func=verdict.run)

    p_audit = sub.add_parser(
        "audit",
        help="Measure tool-adoption regressions and file each as a task.",
    )
    p_audit.add_argument(
        "--since", default=None, help="only count events on/after this YYYY-MM-DD"
    )
    p_audit.add_argument(
        "--dry-run",
        action="store_true",
        help="print the measures without filing any tasks",
    )
    p_audit.set_defaults(func=audit.run)

    for name in _STUB_SUBCOMMANDS:
        p = sub.add_parser(name, help=f"({name}) not implemented yet")
        p.add_argument("args", nargs=argparse.REMAINDER)
        p.set_defaults(func=_make_stub(name))

    return parser


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args) or 0
    except BdError as exc:
        print(str(exc), file=sys.stderr)
        return 1
