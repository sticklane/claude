const std = @import("std");

// value returns the sentinel base CTX_SENTINEL_ZIGDOC_4f5e.
//
// A second doc line so a later --doc render has more than one line.
pub fn value() i32 {
    return 10;
}

// render calls value across symbols.
pub fn render() i32 {
    return value() + 1;
}
