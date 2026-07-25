"""Pre-2.0 compatibility entrypoint for the retired shadow sync."""

import sys

RETIREMENT_DIAGNOSTIC = (
    "agentic shadow-sync: retired; task state lives in bd; "
    "use register-spec only for new tasks"
)


def run(_args=None):
    print(RETIREMENT_DIAGNOSTIC, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(run())
