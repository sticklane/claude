use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE_TS: &str = "tests/fixtures/languages/typescript/sample.ts";
const SENTINEL: &str = "CTX_SENTINEL_TSDOC_9b2c";

fn extract_ext(ext: &str, rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension(ext).expect("typescript extractor registered");
    ex.extract(rel, src)
}

fn extract_ts_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE_TS).expect("read fixture");
    extract_ext("ts", "sample.ts", &src)
}

#[test]
fn typescript_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_ts_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");

    assert_eq!(
        path::resolve_suffix(&paths, "deep"),
        vec!["sample.Outer.Inner.deep"],
        "all paths: {paths:?}"
    );
    assert_eq!(
        path::resolve_suffix(&paths, "Widget.render"),
        vec!["sample.Widget.render"]
    );
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn typescript_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"function foo(a) {\n  return a + 1;\n}\n";
    let renamed = b"function bar(a) {\n  return a + 1;\n}\n";
    let body_edit = b"function foo(a) {\n  return a + 2;\n}\n";
    let h_orig = extract_ext("ts", "m.ts", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_ext("ts", "m.ts", renamed).symbols[0]
        .body_hash
        .clone();
    let h_edit = extract_ext("ts", "m.ts", body_edit).symbols[0]
        .body_hash
        .clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn typescript_c8_docstring_carries_fixture_sentinel() {
    let r = extract_ts_fixture();
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
fn typescript_reference_extracted_at_known_call_site() {
    let r = extract_ts_fixture();
    assert!(
        r.references
            .iter()
            .any(|rf| rf.kind == RefKind::Call && rf.name == "value"),
        "expected a `value()` call reference: {:?}",
        r.references
    );
    assert!(
        r.references
            .iter()
            .any(|rf| rf.kind == RefKind::Call && rf.name == "helper"),
        "expected a cross-file `helper()` call reference"
    );
}

#[test]
fn typescript_import_edges_extracted() {
    let r = extract_ts_fixture();
    assert!(
        r.imports
            .iter()
            .any(|i| i.module == "./helper" && i.name.as_deref() == Some("helper")),
        "expected `import {{ helper }} from './helper'` edge: {:?}",
        r.imports
    );
}

#[test]
fn typescript_locals_scope_distinguishes_local_from_global() {
    let r = extract_ts_fixture();
    let global_value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "sample.value")
        .expect("module-level value function");
    let local = r
        .scopes
        .iter()
        .find(|sc| sc.name == "value")
        .expect("a local `value` scope fact");
    assert!(
        !local.contains_byte(global_value.ident_span.start_byte),
        "the global `value` def must not fall inside the local scope span"
    );
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
fn typescript_tsx_and_js_dispatch_by_extension() {
    let tsx = std::fs::read("tests/fixtures/languages/typescript/widget.tsx").expect("read tsx");
    let r_tsx = extract_ext("tsx", "widget.tsx", &tsx);
    assert!(
        r_tsx.symbols.iter().any(|s| s.qpath == "widget.Button"),
        ".tsx must dispatch to the TSX grammar: {:?}",
        r_tsx.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );

    let js = std::fs::read("tests/fixtures/languages/typescript/helper.js").expect("read js");
    let r_js = extract_ext("js", "helper.js", &js);
    assert!(
        r_js.symbols.iter().any(|s| s.qpath == "helper.helper"),
        ".js must dispatch to the JavaScript grammar: {:?}",
        r_js.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
    assert!(
        r_js.references
            .iter()
            .any(|rf| rf.kind == RefKind::Call && rf.name == "value"),
        ".js references extracted"
    );
    assert!(
        r_js.imports
            .iter()
            .any(|i| i.name.as_deref() == Some("value")),
        ".js import edges extracted"
    );
}

#[test]
fn typescript_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"function good_one() {\n  return 1;\n}\n\nfunction middle() {\n  let x = = =;\n}\n\nfunction good_two() {\n  return 3;\n}\n";
    let r = extract_ext("ts", "m.ts", src);
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
fn typescript_coverage_marker_emitted() {
    let r = extract_ts_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: typescript");
    let _ = out.flush();
}
