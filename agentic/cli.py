"""``agentic`` command-line entrypoint.

Working commands are registered for normal discovery. Retired pre-2.0 names
are handled before parser construction so they remain exact compatibility
aliases without appearing in help or completion metadata.
"""

import argparse
import sys

from agentic import audit, claim, initialize, ready, register, resume, verdict
from agentic.bd import BdError

_RETIRED_DIAGNOSTICS = {
    "compose": (
        "agentic compose: retired by the native-orchestration pivot; "
        "use /work, /build, or /drain"
    ),
    "ctx": "agentic ctx: wrapper not shipped; use ctx directly",
    "inbox": "agentic inbox: retired; use bd ready and bd human list",
    "demote": "agentic demote: retired; use bd update <id> --status deferred",
    "shadow-sync": (
        "agentic shadow-sync: retired; task state lives in bd; "
        "use register-spec only for new tasks"
    ),
}
_RETIRED_SUBCOMMANDS = (
    "compose",
    "ctx",
    "inbox",
    "demote",
    "shadow-sync",
)


def _build_compatibility_parser():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in _RETIRED_SUBCOMMANDS:
        sub.add_parser(name, add_help=False)
    return parser


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

    p_register = sub.add_parser(
        "register-spec",
        help="Create absent bd issues and dependency edges for one spec.",
    )
    p_register.add_argument("spec_dir", help="spec directory containing tasks/")
    p_register.set_defaults(func=register.run)

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

    return parser


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in _RETIRED_DIAGNOSTICS:
        _build_compatibility_parser().parse_args(argv[:1])
        print(_RETIRED_DIAGNOSTICS[argv[0]], file=sys.stderr)
        return 2
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args) or 0
    except BdError as exc:
        print(str(exc), file=sys.stderr)
        return 1
