//! Crate-level fixture for Rust extraction tests.

use std::collections::HashMap;

/// A crate-level constant.
pub const GLOBAL: i32 = 10;

/// Return the sentinel CTX_SENTINEL_RUSTDOC_2d9a marker.
///
/// A second doc line so a later --doc render has more than one line.
pub fn value() -> i32 {
    GLOBAL
}

/// A sample struct type.
pub struct Widget {
    name: String,
}

impl Widget {
    /// Render calls value across symbols and touches HashMap.
    pub fn render(&self) -> i32 {
        let mut map = HashMap::new();
        map.insert(0, self.name.len());
        value() + GLOBAL
    }
}
