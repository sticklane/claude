"""``agentic`` command-line entrypoint.

Registers EVERY planned subcommand so sibling tasks stay Touch-disjoint on
their own modules: ``init`` is implemented here; the verbs later tasks fill
(ready, claim, verdict, resume, compose, ctx, inbox, demote) are registered
as stubs that exit 2 ("not implemented").
"""

import argparse
import sys

from agentic import initialize
from agentic.bd import BdError

# Verbs whose bodies belong to later tasks (03, 04, 06, 07, 11). Registered
# now as stubs so the subcommand surface is stable and disjoint.
_STUB_SUBCOMMANDS = (
    "ready",
    "claim",
    "verdict",
    "resume",
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
