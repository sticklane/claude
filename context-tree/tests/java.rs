use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/java/Sample.java";
const SENTINEL: &str = "CTX_SENTINEL_JAVADOC_8f1b";

fn extract_java(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("java").expect("java extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_java("Sample.java", &src)
}

#[test]
fn java_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(
        path::resolve_suffix(&paths, "value"),
        vec!["com.example.Sample.value"],
        "all paths: {paths:?}"
    );
    assert_eq!(
        path::resolve_suffix(&paths, "Sample.render"),
        vec!["com.example.Sample.render"]
    );
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn java_module_is_the_package_not_the_file_path() {
    let r = extract_java("weird/path/Other.java", &std::fs::read(FIXTURE).unwrap());
    assert!(
        r.symbols
            .iter()
            .all(|s| s.qpath.starts_with("com.example.")),
        "module must be package `com.example`: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn java_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"class Foo {\n    int m() {\n        return 1;\n    }\n}\n";
    let renamed = b"class Bar {\n    int m() {\n        return 1;\n    }\n}\n";
    let body_edit = b"class Foo {\n    int m() {\n        return 2;\n    }\n}\n";
    let h_orig = extract_java("A.java", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_java("A.java", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_java("A.java", body_edit).symbols[0]
        .body_hash
        .clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn java_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "com.example.Sample.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "javadoc should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn java_reference_extracted_at_known_call_site() {
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
fn java_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.name.as_deref() == Some("List")),
        "expected `import java.util.List` edge: {:?}",
        r.imports
    );
}

#[test]
fn java_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"class M {\n    int goodOne() {\n        return 1;\n    }\n    int middle() {\n        return = = ;\n    }\n    int goodTwo() {\n        return 3;\n    }\n}\n";
    let r = extract_java("M.java", src);
    assert!(
        r.parse_failed,
        "a file with a syntax error must be parse-failed"
    );
    let names: HashSet<&str> = r.symbols.iter().map(|s| s.name.as_str()).collect();
    assert!(names.contains("goodOne"), "sibling before error: {names:?}");
    assert!(names.contains("goodTwo"), "sibling after error: {names:?}");
}

#[test]
fn java_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: java");
    let _ = out.flush();
}
