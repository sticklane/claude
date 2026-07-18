//! C1/C3 note-anchor resolution: map a `<symbol>` argument to the symbol it
//! anchors, using the same suffix semantics as the query commands so
//! `ctx notes add` refuses an ambiguous anchor exactly as `ctx sig` refuses an
//! ambiguous query (C3).

use crate::index::SymbolRow;
use crate::path::resolve_suffix;
use std::collections::HashSet;

/// The outcome of resolving a `<symbol>` argument against the indexed symbols.
pub enum Resolution<'a> {
    /// Exactly one symbol matched — the anchor.
    Unique(&'a SymbolRow),
    /// No symbol matched (exit 1).
    None,
    /// Several symbols matched — the C3 candidate list (exit 3).
    Ambiguous(Vec<&'a SymbolRow>),
}

/// Resolve `query` against `symbols` by C3 suffix matching, returning the unique
/// anchor, no match, or the ambiguous candidate list (sorted by qualified path).
pub fn resolve<'a>(symbols: &'a [SymbolRow], query: &str) -> Resolution<'a> {
    let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
    let matched: HashSet<&str> = resolve_suffix(&qpaths, query).into_iter().collect();
    let mut hits: Vec<&SymbolRow> = symbols
        .iter()
        .filter(|s| matched.contains(s.qpath.as_str()))
        .collect();
    hits.sort_by(|a, b| a.qpath.cmp(&b.qpath));
    match hits.len() {
        0 => Resolution::None,
        1 => Resolution::Unique(hits[0]),
        _ => Resolution::Ambiguous(hits),
    }
}
