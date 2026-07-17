use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/python/sample.py";
const SENTINEL: &str = "CTX_SENTINEL_PYDOC_7f3a";

fn extract_py(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("py").expect("python extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_py("sample.py", &src)
}

#[test]
fn python_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");

    // Whole-trailing-component suffix resolves to the one deep method.
    assert_eq!(
        path::resolve_suffix(&paths, "deep"),
        vec!["sample.Outer.Inner.deep"]
    );
    // A multi-component suffix on `.` boundaries.
    assert_eq!(
        path::resolve_suffix(&paths, "Outer.method"),
        vec!["sample.Outer.method"]
    );
    // No spurious substring match, no false positive on a missing name.
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn python_overload_shaped_defs_get_distinct_c1_ordinals() {
    // Two module-level defs sharing a path → distinct #-ordinal C1 paths.
    let src = b"def dup():\n    return 1\n\n\ndef dup():\n    return 2\n";
    let r = extract_py("m.py", src);
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    assert!(paths.contains(&"m.dup#1".to_string()), "{paths:?}");
    assert!(paths.contains(&"m.dup#2".to_string()), "{paths:?}");
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "ordinal-suffixed paths stay unique");
    // The bare suffix is ambiguous across both (C3's caller resolves that).
    assert_eq!(path::resolve_suffix(&paths, "dup").len(), 2);
}

#[test]
fn python_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"def foo(a):\n    return a + 1\n";
    let renamed = b"def bar(a):\n    return a + 1\n";
    let body_edit = b"def foo(a):\n    return a + 2\n";
    let h_orig = extract_py("m.py", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_py("m.py", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_py("m.py", body_edit).symbols[0].body_hash.clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn python_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "sample.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "docstring should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn python_reference_extracted_at_known_call_site() {
    let r = extract_fixture();
    let value_calls: Vec<_> = r
        .references
        .iter()
        .filter(|rf| rf.kind == RefKind::Call && rf.name == "value")
        .collect();
    assert!(
        !value_calls.is_empty(),
        "expected at least one call reference to `value`"
    );
    // The cross-symbol call in Inner.deep is on the `return value()` line (0-based row 29).
    assert!(
        value_calls.iter().any(|rf| rf.location.point.row == 29),
        "expected a `value()` call at the Inner.deep call site: {:?}",
        value_calls
            .iter()
            .map(|c| c.location.point)
            .collect::<Vec<_>>()
    );
    assert!(
        r.references
            .iter()
            .any(|rf| rf.name == "getpid" && rf.kind == RefKind::Call),
        "expected an os.getpid() call reference"
    );
}

#[test]
fn python_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports
            .iter()
            .any(|i| i.module == "os" && i.name.is_none()),
        "expected `import os` edge: {:?}",
        r.imports
    );
    assert!(
        r.imports
            .iter()
            .any(|i| i.module == "collections" && i.name.as_deref() == Some("OrderedDict")),
        "expected `from collections import OrderedDict` edge: {:?}",
        r.imports
    );
}

#[test]
fn python_locals_scope_distinguishes_local_from_global() {
    let r = extract_fixture();
    let global_value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "sample.value")
        .expect("module-level value function");
    // A scope fact binds the function-local `value` (the assignment in method).
    let local = r
        .scopes
        .iter()
        .find(|sc| sc.name == "value")
        .expect("a local `value` scope fact");
    // The module-level definition is OUTSIDE the local scope → distinguishable.
    assert!(
        !local.contains_byte(global_value.ident_span.start_byte),
        "the global `value` def must not fall inside the local scope span"
    );
    // The local read reference IS inside the local scope.
    let local_read = r
        .references
        .iter()
        .find(|rf| rf.name == "value" && rf.kind == RefKind::Read)
        .expect("a local read of `value`");
    assert!(
        local.contains_byte(local_read.location.byte),
        "the local read of `value` must fall inside the local scope span"
    );
}

#[test]
fn python_parse_failed_file_yields_best_effort_sibling_facts() {
    // `middle` has a mid-function syntax error (`x = = =`); the flanking
    // `good_one`/`good_two` siblings must still extract best-effort (R1).
    let src = b"def good_one():\n    return 1\n\ndef middle():\n    x = = =\n    return 2\n\ndef good_two():\n    return 3\n";
    let r = extract_py("m.py", src);
    assert!(
        r.parse_failed,
        "a file with a syntax error must be marked parse-failed"
    );
    let names: HashSet<&str> = r.symbols.iter().map(|s| s.name.as_str()).collect();
    assert!(
        names.contains("good_one"),
        "sibling before the error should still extract: {names:?}"
    );
    assert!(
        names.contains("good_two"),
        "sibling after the error should still extract: {names:?}"
    );
}

#[test]
fn python_coverage_marker_emitted() {
    // Direct stdout write (bypasses libtest capture) so the mechanical
    // language-coverage criterion `cargo test | grep -Fx "covered: python"`
    // observes the line without needing --nocapture.
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: python");
    let _ = out.flush();
}
