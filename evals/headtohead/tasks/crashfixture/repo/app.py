"""Toy in-mount fixture repo for the headtohead crash-handling selftest.

Its stub session deliberately dies mid-run (simulating a crash / session-cap
trip) AFTER emitting a partial cost transcript. The runner must still record a
schema-valid row with pass:false and the non-null partial usd/tokens — crashed
runs are recorded, never dropped (SPEC.md controls; acceptance criterion 6).
"""


def greet(name):
    return f"hello {name}"
