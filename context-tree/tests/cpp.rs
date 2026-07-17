use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/cpp/sample.cpp";
const OVERLOAD_FIXTURE: &str = "tests/fixtures/languages/cpp/overload.cpp";
const SENTINEL: &str = "CTX_SENTINEL_CPPDOC_9c2d";

fn extract_cpp(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("cpp").expect("cpp extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_cpp("sample.cpp", &src)
}

fn extract_overload() -> ExtractResult {
    let src = std::fs::read(OVERLOAD_FIXTURE).expect("read overload fixture");
    extract_cpp("overload.cpp", &src)
}

#[test]
fn cpp_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(
        path::resolve_suffix(&paths, "base"),
        vec!["app.base"],
        "all paths: {paths:?}"
    );
    assert_eq!(path::resolve_suffix(&paths, "render"), vec!["app.render"]);
}

#[test]
fn cpp_namespace_is_a_container_not_the_module_component() {
    // A symbol inside `namespace app` is qualified by the namespace container,
    // not by the file path — the file-path module is used only where no
    // enclosing namespace exists.
    let r = extract_fixture();
    assert!(
        r.symbols.iter().any(|s| s.qpath == "app.base"),
        "namespace member must key under its namespace: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn cpp_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let base = r
        .symbols
        .iter()
        .find(|s| s.qpath == "app.base")
        .expect("base symbol");
    assert!(
        base.docstring.contains(SENTINEL),
        "leading comment should embed the sentinel: {:?}",
        base.docstring
    );
}

#[test]
fn cpp_overload_qpaths_are_distinct_and_each_resolves_unambiguously() {
    let r = extract_overload();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    // (a) the two overloads carry DISTINCT C1 paths, each with an ordinal suffix.
    let adds: Vec<&String> = paths
        .iter()
        .filter(|p| p.split('#').next() == Some("math.add"))
        .collect();
    assert_eq!(adds.len(), 2, "two `add` overloads expected: {paths:?}");
    assert_ne!(adds[0], adds[1], "overloads must have distinct C1 paths");
    assert!(
        adds.iter().all(|p| p.contains('#')),
        "each overload carries a C1 ordinal suffix: {adds:?}"
    );
    // (b) each disambiguated full path resolves to exactly one symbol, while the
    //     bare suffix `add` is ambiguous across both — the reason C1 ordinals exist.
    for a in &adds {
        assert_eq!(
            paths.iter().filter(|p| p == a).count(),
            1,
            "full path {a} must resolve to exactly one symbol"
        );
    }
    assert_eq!(
        path::resolve_suffix(&paths, "add").len(),
        2,
        "bare suffix `add` is ambiguous across overloads: {paths:?}"
    );
}

#[test]
fn cpp_reference_extracted_at_known_call_site() {
    let r = extract_fixture();
    assert!(
        r.references
            .iter()
            .any(|rf| rf.kind == RefKind::Call && rf.name == "base"),
        "expected a `base()` call reference: {:?}",
        r.references
    );
}

#[test]
fn cpp_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "string"),
        "expected `#include <string>` edge: {:?}",
        r.imports
    );
}

#[test]
fn cpp_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"int good_one() {\n\treturn 1;\n}\n\nint middle() {\n\treturn = =;\n}\n\nint good_two() {\n\treturn 3;\n}\n";
    let r = extract_cpp("m.cpp", src);
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
fn cpp_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: cpp");
    let _ = out.flush();
}
