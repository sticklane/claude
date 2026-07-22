"""Toy in-mount fixture repo for the headtohead runner selftest.

This is NOT one of the three real corpus tasks (T1-T3); it exists only so
`run.sh --task fixture` can exercise the whole session-run path — cost summing
across a spawned child, schema-valid row emission, hidden-assert scoring —
without any paid model session. A real arm would edit this file; the stub
session simulates that edit by writing solution.txt.
"""


def greet(name):
    return f"hello {name}"
