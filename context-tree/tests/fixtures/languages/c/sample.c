#include <stdio.h>

const int GLOBAL_LIMIT = 10;

// value returns the sentinel base count CTX_SENTINEL_CDOC_7a1b.
//
// A second doc line so a later --doc render has more than one line.
int value(void) {
    return GLOBAL_LIMIT;
}

// render calls value across symbols.
int render(void) {
    return value() + 1;
}
