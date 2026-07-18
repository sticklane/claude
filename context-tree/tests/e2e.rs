//! Top-level cargo test target for the end-to-end user-flow script. The script
//! itself lives under `tests/e2e/` (task 14 Touch scope); this file makes it a
//! compiled test target so `cargo test e2e_user_flow` discovers it.

#[path = "e2e/user_flow.rs"]
mod user_flow;
