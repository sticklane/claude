use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/c/sample.c";
const SENTINEL: &str = "CTX_SENTINEL_CDOC_7a1b";

fn extract_c(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("c").expect("c extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_c("sample.c", &src)
}

#[test]
fn c_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(
        path::resolve_suffix(&paths, "value"),
        vec!["sample.value"],
        "all paths: {paths:?}"
    );
    assert_eq!(
        path::resolve_suffix(&paths, "render"),
        vec!["sample.render"]
    );
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn c_module_is_the_repo_relative_file_path() {
    // C1 fallback: no module concept, so the file path is the module component.
    let r = extract_c("some/nested/dir/other.c", &std::fs::read(FIXTURE).unwrap());
    assert!(
        r.symbols
            .iter()
            .all(|s| s.qpath.starts_with("some.nested.dir.other.")),
        "module must be the file path: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn c_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"int foo(int a) {\n\treturn a + 1;\n}\n";
    let renamed = b"int bar(int a) {\n\treturn a + 1;\n}\n";
    let body_edit = b"int foo(int a) {\n\treturn a + 2;\n}\n";
    let h_orig = extract_c("m.c", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_c("m.c", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_c("m.c", body_edit).symbols[0].body_hash.clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn c_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "sample.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "leading comment should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn c_reference_extracted_at_known_call_site() {
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
fn c_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "stdio.h"),
        "expected `#include <stdio.h>` edge: {:?}",
        r.imports
    );
}

#[test]
fn c_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"int good_one(void) {\n\treturn 1;\n}\n\nint middle(void) {\n\treturn = =;\n}\n\nint good_two(void) {\n\treturn 3;\n}\n";
    let r = extract_c("m.c", src);
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
fn c_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: c");
    let _ = out.flush();
}
