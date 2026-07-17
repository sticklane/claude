//! The [`LanguageExtractor`] trait and the per-language registration pattern.
//!
//! Registration uses `inventory` so a new language is added with a single
//! `pub mod <lang>;` line in `lang/mod.rs` plus its own file — there is no
//! shared match/dispatch table to hand-edit per grammar.

use crate::facts::{Import, Reference, Scope, Symbol};

/// The full per-file fact set an extractor returns (R1).
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct ExtractResult {
    pub symbols: Vec<Symbol>,
    pub references: Vec<Reference>,
    pub imports: Vec<Import>,
    pub scopes: Vec<Scope>,
    /// True when tree-sitter reported an ERROR at or near the root; facts are
    /// then best-effort from recoverable subtrees.
    pub parse_failed: bool,
}

/// Parses one file's bytes into per-file facts. Facts derive from that file's
/// content alone (R1).
pub trait LanguageExtractor: Sync {
    /// Canonical language name (e.g. `"python"`).
    fn language(&self) -> &'static str;
    /// File extensions this extractor claims (without the dot).
    fn extensions(&self) -> &'static [&'static str];
    /// Extract facts. `rel_path` is the repo-relative path (used for C1 module
    /// derivation where the language keys modules on file path).
    fn extract(&self, rel_path: &str, source: &[u8]) -> ExtractResult;
}

/// A link-time extractor registration collected by `inventory`.
pub struct ExtractorRegistration {
    pub language: &'static str,
    pub extensions: &'static [&'static str],
    pub make: fn() -> Box<dyn LanguageExtractor>,
}

inventory::collect!(ExtractorRegistration);

/// Iterate every registered extractor.
pub fn registrations() -> impl Iterator<Item = &'static ExtractorRegistration> {
    inventory::iter::<ExtractorRegistration>()
}

/// The extractor claiming `ext` (extension without the dot), if any.
pub fn for_extension(ext: &str) -> Option<Box<dyn LanguageExtractor>> {
    registrations()
        .find(|r| r.extensions.contains(&ext))
        .map(|r| (r.make)())
}

/// The extractor for a named language, if registered.
pub fn for_language(lang: &str) -> Option<Box<dyn LanguageExtractor>> {
    registrations()
        .find(|r| r.language == lang)
        .map(|r| (r.make)())
}
