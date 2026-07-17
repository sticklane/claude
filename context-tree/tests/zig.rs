use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/zig/sample.zig";
const SENTINEL: &str = "CTX_SENTINEL_ZIGDOC_4f5e";

fn extract_zig(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("zig").expect("zig extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_zig("sample.zig", &src)
}

#[test]
fn zig_c1_paths_are_unique_and_resolve_by_suffix() {
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
fn zig_module_is_the_repo_relative_file_path() {
    // C1 fallback: no module concept, so the file path is the module component.
    let r = extract_zig("some/dir/other.zig", &std::fs::read(FIXTURE).unwrap());
    assert!(
        r.symbols
            .iter()
            .all(|s| s.qpath.starts_with("some.dir.other.")),
        "module must be the file path: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn zig_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"pub fn foo() i32 {\n    return 1;\n}\n";
    let renamed = b"pub fn bar() i32 {\n    return 1;\n}\n";
    let body_edit = b"pub fn foo() i32 {\n    return 2;\n}\n";
    let h_orig = extract_zig("m.zig", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_zig("m.zig", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_zig("m.zig", body_edit).symbols[0].body_hash.clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn zig_c8_docstring_carries_fixture_sentinel() {
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
fn zig_reference_extracted_at_known_call_site() {
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
fn zig_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "std"),
        "expected an `@import(\"std\")` edge: {:?}",
        r.imports
    );
}

#[test]
fn zig_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"pub fn good_one() i32 {\n    return 1;\n}\n\npub fn middle() i32 {\n    return = =;\n}\n\npub fn good_two() i32 {\n    return 3;\n}\n";
    let r = extract_zig("m.zig", src);
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
fn zig_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: zig");
    let _ = out.flush();
}
