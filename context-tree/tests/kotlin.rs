use context_tree::extract::{self, ExtractResult};
use context_tree::facts::{RefKind, SymbolKind};
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/kotlin/Sample.kt";
const SENTINEL: &str = "CTX_SENTINEL_KDOC_7a2c";

fn extract_kotlin(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("kt").expect("kotlin extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_kotlin("Sample.kt", &src)
}

#[test]
fn kotlin_module_is_the_package() {
    let r = extract_fixture();
    assert!(
        r.symbols.iter().any(|s| s.qpath == "com.example.value"),
        "package must be the C1 module: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn kotlin_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(
        path::resolve_suffix(&paths, "value"),
        vec!["com.example.value"]
    );
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn kotlin_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"fun foo(): Int {\n    return 1\n}\n";
    let renamed = b"fun bar(): Int {\n    return 1\n}\n";
    let body_edit = b"fun foo(): Int {\n    return 2\n}\n";
    let h_orig = extract_kotlin("m.kt", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_kotlin("m.kt", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_kotlin("m.kt", body_edit).symbols[0]
        .body_hash
        .clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn kotlin_val_is_a_constant() {
    let r = extract_fixture();
    let top = r
        .symbols
        .iter()
        .find(|s| s.name == "top")
        .expect("top symbol");
    assert_eq!(
        top.kind,
        SymbolKind::Constant,
        "a `val` binding is a Constant"
    );
}

#[test]
fn kotlin_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "com.example.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "KDoc should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn kotlin_reference_extracted_at_known_call_site() {
    let r = extract_fixture();
    assert!(
        r.references
            .iter()
            .any(|rf| rf.kind == RefKind::Call && rf.name == "value"),
        "expected a `value()` call reference: {:?}",
        r.references
    );
}

#[test]
fn kotlin_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "kotlin.math.PI"),
        "expected an `import kotlin.math.PI` edge: {:?}",
        r.imports
    );
}

#[test]
fn kotlin_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"fun good_one(): Int {\n    return 1\n}\n\nfun middle(): Int {\n    return = =\n}\n\nfun good_two(): Int {\n    return 3\n}\n";
    let r = extract_kotlin("m.kt", src);
    assert!(
        r.parse_failed,
        "a file with a syntax error must be parse-failed"
    );
    let names: HashSet<&str> = r.symbols.iter().map(|s| s.name.as_str()).collect();
    assert!(
        names.contains("good_one"),
        "sibling before error: {names:?}"
    );
    assert!(names.contains("good_two"), "sibling after error: {names:?}");
}

#[test]
fn kotlin_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: kotlin");
    let _ = out.flush();
}
