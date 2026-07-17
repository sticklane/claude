use context_tree::extract::{self, ExtractResult};
use context_tree::facts::SymbolKind;
use context_tree::path;
use std::collections::HashSet;
use std::io::Write;

const FIXTURE: &str = "tests/fixtures/languages/ocaml/sample.ml";
const SENTINEL: &str = "CTX_SENTINEL_OCAMLDOC_3b9d";

fn extract_ocaml(rel: &str, src: &[u8]) -> ExtractResult {
    let ex = extract::for_extension("ml").expect("ocaml extractor registered");
    ex.extract(rel, src)
}

fn extract_fixture() -> ExtractResult {
    let src = std::fs::read(FIXTURE).expect("read fixture");
    extract_ocaml("sample.ml", &src)
}

#[test]
fn ocaml_c1_paths_are_unique_and_resolve_by_suffix() {
    let r = extract_fixture();
    let paths: Vec<String> = r.symbols.iter().map(|s| s.qpath.clone()).collect();
    let set: HashSet<&String> = paths.iter().collect();
    assert_eq!(set.len(), paths.len(), "C1 paths must be unique: {paths:?}");
    assert_eq!(path::resolve_suffix(&paths, "value"), vec!["sample.value"]);
    assert!(path::resolve_suffix(&paths, "nonexistent").is_empty());
}

#[test]
fn ocaml_nested_module_contributes_to_qpath() {
    let r = extract_fixture();
    assert!(
        r.symbols.iter().any(|s| s.qpath == "sample.Inner.nested"),
        "a nested module must add a C1 container: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn ocaml_module_component_uses_file_path_for_the_compilation_unit() {
    let r = extract_ocaml("some/dir/other.ml", &std::fs::read(FIXTURE).unwrap());
    assert!(
        r.symbols.iter().any(|s| s.qpath == "some.dir.other.value"),
        "compilation-unit module is the file path: {:?}",
        r.symbols.iter().map(|s| &s.qpath).collect::<Vec<_>>()
    );
}

#[test]
fn ocaml_c2_hash_stable_under_pure_rename_changes_on_body_edit() {
    let orig = b"let foo = 1\n";
    let renamed = b"let bar = 1\n";
    let body_edit = b"let foo = 2\n";
    let h_orig = extract_ocaml("m.ml", orig).symbols[0].body_hash.clone();
    let h_renamed = extract_ocaml("m.ml", renamed).symbols[0].body_hash.clone();
    let h_edit = extract_ocaml("m.ml", body_edit).symbols[0]
        .body_hash
        .clone();
    assert_eq!(
        h_orig, h_renamed,
        "C2: a pure rename must not change the hash"
    );
    assert_ne!(h_orig, h_edit, "C2: a body edit must change the hash");
}

#[test]
fn ocaml_let_with_parameter_is_a_function() {
    let r = extract_fixture();
    let render = r
        .symbols
        .iter()
        .find(|s| s.name == "render")
        .expect("render symbol");
    assert_eq!(
        render.kind,
        SymbolKind::Function,
        "a parameterized let is a Function"
    );
    let value = r
        .symbols
        .iter()
        .find(|s| s.name == "value")
        .expect("value symbol");
    assert_eq!(
        value.kind,
        SymbolKind::Constant,
        "a value let is a Constant"
    );
}

#[test]
fn ocaml_c8_docstring_carries_fixture_sentinel() {
    let r = extract_fixture();
    let value = r
        .symbols
        .iter()
        .find(|s| s.qpath == "sample.value")
        .expect("value symbol");
    assert!(
        value.docstring.contains(SENTINEL),
        "(** *) doc should embed the sentinel: {:?}",
        value.docstring
    );
}

#[test]
fn ocaml_reference_extracted_at_known_use_site() {
    let r = extract_fixture();
    assert!(
        r.references.iter().any(|rf| rf.name == "value"),
        "expected a `value` reference from render: {:?}",
        r.references
    );
}

#[test]
fn ocaml_import_edges_extracted() {
    let r = extract_fixture();
    assert!(
        r.imports.iter().any(|i| i.module == "Printf"),
        "expected an `open Printf` edge: {:?}",
        r.imports
    );
}

#[test]
fn ocaml_scope_facts_extracted_from_locals_query() {
    // OCaml ships a locals query with @local.scope captures (R10).
    let r = extract_fixture();
    assert!(
        !r.scopes.is_empty(),
        "OCaml ships a locals query, so scope facts must be produced: {:?}",
        r.scopes
    );
    assert!(
        r.scopes.iter().any(|sc| sc.name == "x"),
        "the `x` parameter must be a locally-scoped binding: {:?}",
        r.scopes
    );
}

#[test]
fn ocaml_parse_failed_file_yields_best_effort_sibling_facts() {
    let src = b"let good_one = 1\n\nlet middle = )(\n\nlet good_two = 3\n";
    let r = extract_ocaml("m.ml", src);
    assert!(
        r.parse_failed,
        "a file with a syntax error must be parse-failed"
    );
    let names: HashSet<&str> = r.symbols.iter().map(|s| s.name.as_str()).collect();
    assert!(
        names.contains("good_one") || names.contains("good_two"),
        "at least one sibling around the error survives: {names:?}"
    );
}

#[test]
fn ocaml_coverage_marker_emitted() {
    let r = extract_fixture();
    assert!(!r.symbols.is_empty(), "fixture must yield symbols");
    let mut out = std::io::stdout();
    let _ = writeln!(out, "covered: ocaml");
    let _ = out.flush();
}
