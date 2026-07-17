use context_tree::extract::{self, ExtractResult};
use context_tree::facts::SymbolKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/haskell/Sample.hs";
const SENTINEL: &str = "CTX_SENTINEL_HADDOCK_5e1f";

fn extract_haskell(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("hs").expect("haskell extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_haskell("Sample.hs", &src)
}

#[test]
fn haskell_module_is_the_module_header() {
    let r = extract_fixture();
    assert!(
        r.symbols.iter().any(|s| s.qpath == "Sample.value"),
        "the `module Sample where` header is the C1 module: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn haskell_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(path::resolve_suffix(&paths, "value"), vec!["Sample.value"]);
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn haskell_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"module M where\nfoo = 1\n";
    let renamed = b"module M where\nbar = 1\n";
    let body_edit = b"module M where\nfoo = 2\n";
    let h_orig = extract_haskell("m.hs", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_haskell("m.hs", renamed).symbols[0]
        .body_hash
        .clone();
    let h_edit = extract_haskell("m.hs", body_edit).symbols[0]
        .body_hash
        .clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn haskell_function_with_patterns_is_a_function() {
    let r = extract_fixture();
    let render = r
        .symbols
        .iter()
        .find(|s| s.name == "render")
        .expect("render symbol");
    assert_eq!(
        render.kind,
        SymbolKind::Function,
        "a binding with patterns is a Function"
    );
}

#[test]
fn haskell_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "Sample.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "Haddock should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn haskell_reference_extracted_at_known_use_site() {
    let r = extract_fixture();
    assert!(
        r.references.iter().any(|rf| rf.name == "value"),
        "expected a `value` reference from render: {:?}",
        r.references
    );
}

#[test]
fn haskell_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "Data.List"),
        "expected an `import Data.List` edge: {:?}",
        r.imports
    );
}

#[test]
fn haskell_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: haskell");
    let _ = out.flush();
}
