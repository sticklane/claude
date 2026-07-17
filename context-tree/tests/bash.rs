use context_tree::extract::{self, ExtractResult};
use context_tree::facts::RefKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/bash/sample.sh";
const SENTINEL: &str = "CTX_SENTINEL_BASHDOC_9c4e";

fn extract_bash(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("sh").expect("bash extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_bash("sample.sh", &src)
}

#[test]
fn bash_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(path::resolve_suffix(&paths, "value"), vec!["sample.value"]);
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn bash_module_is_the_repo_relative_file_path() {
    let r = extract_bash("some/dir/other.sh", &std::fs::read(FIXTURE).unwrap());
    assert!(
        r.symbols.iter().all(|s| s.qpath.starts_with("some.dir.other.")),
        "module must be the file path (C1 fallback): {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn bash_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"value() {\n    echo 1\n}\n";
    let renamed = b"other() {\n    echo 1\n}\n";
    let body_edit = b"value() {\n    echo 2\n}\n";
    let h_orig = extract_bash("m.sh", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_bash("m.sh", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_bash("m.sh", body_edit).symbols[0].body_hash.clone();
    assert_eq!(h_orig, h_renamed, "C2: a pure rename must not change the hash");
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn bash_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r.symbols.iter().find(|s| s.qpath == "sample.value").expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "leading `#` comment should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn bash_reference_extracted_at_known_call_site() {
    let r = extract_fixture();
    assert!(
        r.references
            .iter()
            .any(|rf| rf.kind == RefKind::Call && rf.name == "value"),
        "expected a `value` call reference from render: {:?}",
        r.references
    );
}

#[test]
fn bash_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "./lib.sh"),
        "expected a `source ./lib.sh` edge: {:?}",
        r.imports
    );
}

#[test]
fn bash_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"good_one() {\n    echo 1\n}\n\ngood_two() {\n    echo 2\n}\n\nif then fi\n";
    let r = extract_bash("m.sh", src);
    assert!(r.parse_failed, "a file with a syntax error must be parse-failed");
    let names: HashSet<&str> = r.symbols.iter().map(|s| s.name.as_str()).collect();
    assert!(names.contains("good_one"), "sibling before error: {names:?}");
}

#[test]
fn bash_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: bash");
    let _ = out.flush();
}
