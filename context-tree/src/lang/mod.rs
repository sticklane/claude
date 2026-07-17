//! Language extractor modules. Adding a language is a single `pub mod <lang>;`
//! line here plus the language's own file — the `inventory` registration in
//! that file wires it in, so there is no shared dispatch table to hand-edit.

pub mod python;
pub mod typescript;
