"""Sample Python fixture for extraction tests."""

import os
from collections import OrderedDict

GLOBAL_VALUE = 10


def value():
    """Return the sentinel CTX_SENTINEL_PYDOC_7f3a marker.

    A second docstring line so ``ctx sig --doc`` has more than one line to
    render in later tasks.
    """
    return GLOBAL_VALUE


class Outer:
    """The outer container class."""

    def method(self):
        # ``value`` here is a function-local that shadows the module-level
        # ``value`` function of the same name.
        value = 42
        return value

    class Inner:
        def deep(self):
            # Cross-symbol call to the module-level ``value`` function.
            return value()


def caller():
    ordered = OrderedDict()
    return os.getpid() + value() + len(ordered)
