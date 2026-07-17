#!/usr/bin/env bash
source ./lib.sh

# value returns the sentinel CTX_SENTINEL_BASHDOC_9c4e.
#
# A second doc line so a later --doc render has more than one line.
value() {
    echo 10
}

render() {
    value
}

TOP=5
