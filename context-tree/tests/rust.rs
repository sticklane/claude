use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/rust/sample.rs";
const SENTINEL: &str = "CTX_SENTINEL_RUSTDOC_2d9a";

fn extract_rust(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("rs").expect("rust extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_rust("sample.rs", &src)
}

#[test]
fn rust_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(
        path::resolve_suffix(&paths, "render"),
        vec!["sample.Widget.render"],
        "all paths: {paths:?}"
    );
    assert_eq!(path::resolve_suffix(&paths, "value"), vec!["sample.value"]);
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn rust_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"fn foo(a: i32) -> i32 {\n    a + 1\n}\n";
    let renamed = b"fn bar(a: i32) -> i32 {\n    a + 1\n}\n";
    let body_edit = b"fn foo(a: i32) -> i32 {\n    a + 2\n}\n";
    let h_orig = extract_rust("m.rs", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_rust("m.rs", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_rust("m.rs", body_edit).symbols[0].body_hash.clone();
    assert_eq!(h_orig, h_renamed, "C2: a pure rename must not change the hash");
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn rust_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "sample.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "doc comment should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn rust_reference_extracted_at_known_call_site() {
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
fn rust_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.name.as_deref() == Some("HashMap")),
        "expected a `use std::collections::HashMap` edge: {:?}",
        r.imports
    );
}

#[test]
fn rust_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"fn good_one() -> i32 {\n    1\n}\n\nfn middle() -> i32 {\n    let x = = = ;\n}\n\nfn good_two() -> i32 {\n    3\n}\n";
    let r = extract_rust("m.rs", src);
    assert!(r.parse_failed, "a file with a syntax error must be parse-failed");
    let names: HashSet<&str> = r.symbols.iter().map(|s| s.name.as_str()).collect();
    assert!(names.contains("good_one"), "sibling before error: {names:?}");
    assert!(names.contains("good_two"), "sibling after error: {names:?}");
}

#[test]
fn rust_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: rust");
    let _ = out.flush();
}
