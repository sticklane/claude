//! R3/R6/R7/R8/R18 + C1/C3/C4/C7/C10 query-command integration tests for
//! `ctx tree`, `ctx sig`, and `ctx map`.

use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms), so fixture files
/// sit safely outside it relative to a later query's sweep.
const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

/// Run `ctx <args>` in `root`, returning the raw output (exit code NOT asserted).
fn ctx(root: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .output()
        .unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

fn stderr(out: &Output) -> String {
    String::from_utf8(out.stderr.clone()).unwrap()
}

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

// ----------------------------------------------------------------------------
// C4 root guard
// ----------------------------------------------------------------------------

#[test]
fn root_guard_exits_2_and_names_ctx_init_without_a_context_root() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(2), "no .context/ ancestor exits 2");
    assert!(
        stderr(&out).contains("ctx init"),
        "the guard names `ctx init`: {}",
        stderr(&out)
    );
}

#[test]
fn root_guard_query_succeeds_after_init() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0), "map succeeds once initialized");
}

// ----------------------------------------------------------------------------
// ctx tree
// ----------------------------------------------------------------------------

const NESTED_PY: &str = "\
class Handler:
    def handle(self):
        return 1


def helper():
    return 2
";

#[test]
fn tree_outlines_containment_with_indentation() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", NESTED_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "app.py"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(text.contains("Handler"), "outline names the class: {text}");
    assert!(text.contains("handle"), "outline names the method: {text}");
    assert!(text.contains("helper"), "outline names the function: {text}");
    // The method is nested more deeply than its containing class.
    let class_indent = indent_of(&text, "Handler");
    let method_indent = indent_of(&text, "handle");
    assert!(
        method_indent > class_indent,
        "the method is indented under its class: {text}"
    );
}

/// Leading-space count of the first line mentioning `needle`.
fn indent_of(text: &str, needle: &str) -> usize {
    let line = text
        .lines()
        .find(|l| l.contains(needle))
        .unwrap_or_else(|| panic!("no line contains {needle:?} in:\n{text}"));
    line.len() - line.trim_start().len()
}

#[test]
fn tree_depth_cap_hides_deeper_symbols() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", NESTED_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "app.py", "--depth", "1"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(text.contains("Handler"), "top-level class shown: {text}");
    assert!(
        !text.contains("handle"),
        "the nested method is hidden by --depth 1: {text}"
    );
}

#[test]
fn tree_limit_cap_emits_a_truncation_line_naming_the_flag() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut src = String::new();
    for i in 0..10 {
        src.push_str(&format!("def f{i}():\n    return {i}\n\n\n"));
    }
    write(root, "many.py", &src);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "many.py", "--limit", "3"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(
        text.contains("more") && text.contains("--limit"),
        "a truncation line names the omitted count and --limit: {text}"
    );
    // 10 functions, limit 3 -> 7 omitted.
    assert!(text.contains('7'), "the omitted count (7) is named: {text}");
}

#[test]
fn tree_doc_appends_first_docstring_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "d.py",
        "def documented():\n    \"\"\"First line.\n\n    More.\n    \"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let plain = stdout(&ctx(root, &["tree", "d.py"]));
    assert!(
        !plain.contains("First line."),
        "the default omits docstrings: {plain}"
    );
    let out = ctx(root, &["tree", "d.py", "--doc"]);
    assert_eq!(out.status.code(), Some(0));
    let doc = stdout(&out);
    assert!(
        doc.contains("First line."),
        "--doc appends the first docstring line: {doc}"
    );
    assert!(
        !doc.contains("More."),
        "--doc appends only the FIRST docstring line: {doc}"
    );
}

#[test]
fn tree_empty_scope_prints_nothing_and_exits_0() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "does/not/exist"]);
    assert_eq!(out.status.code(), Some(0), "an empty scope still exits 0");
    assert!(
        stdout(&out).trim().is_empty(),
        "an empty scope prints nothing: {:?}",
        stdout(&out)
    );
}

#[test]
fn tree_marker_plumbing_renders_c10_grammar() {
    // C10 marker rendering (task 09 populates the counts; the grammar is fixed
    // here). The store returns None today, so real output carries no marker.
    assert_eq!(context_tree::cmd::format_note_marker(None), "");
    assert_eq!(
        context_tree::cmd::format_note_marker(Some((3, false))),
        " [notes:3]"
    );
    assert_eq!(
        context_tree::cmd::format_note_marker(Some((2, true))),
        " [notes:2!]"
    );
}

// ----------------------------------------------------------------------------
// ctx sig
// ----------------------------------------------------------------------------

const TWO_HANDLERS: &str = "\
class Handler:
    \"\"\"Handles things.\"\"\"
    pass


class AuthHandler:
    \"\"\"Handles auth.\"\"\"
    pass
";

#[test]
fn sig_default_prints_signature_and_first_docstring_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def solo():\n    \"\"\"Only line.\n\n    Detail.\n    \"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "solo"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(text.contains("solo"), "signature is printed: {text}");
    assert!(text.contains("Only line."), "first docstring line: {text}");
    assert!(
        !text.contains("Detail."),
        "the default prints only the first docstring line: {text}"
    );
    assert!(
        !text.contains("[notes:"),
        "no note marker until task 09: {text}"
    );
}

#[test]
fn sig_doc_prints_the_full_docstring() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def solo():\n    \"\"\"Only line.\n\n    Detail.\n    \"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "solo", "--doc"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(
        text.contains("Only line.") && text.contains("Detail."),
        "--doc prints the full docstring: {text}"
    );
}

#[test]
fn sig_c3_suffix_resolves_to_the_boundary_match_not_a_substring() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", TWO_HANDLERS);
    sleep(PAST);
    init(root);

    // `Handler` is a `.`-boundary suffix of `app.Handler` only; a substring
    // matcher would ambiguously also hit `app.AuthHandler` and exit 3.
    let out = ctx(root, &["sig", "Handler"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "suffix match is unambiguous: {}",
        stdout(&out)
    );
    assert!(
        stdout(&out).contains("Handles things."),
        "resolved to app.Handler: {}",
        stdout(&out)
    );
}

#[test]
fn sig_no_match_exits_1() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", TWO_HANDLERS);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "Nonexistent"]);
    assert_eq!(out.status.code(), Some(1), "no match exits 1");
}

#[test]
fn sig_ambiguous_lists_candidates_and_exits_3() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "class Handler:\n    pass\n");
    write(root, "b.py", "class Handler:\n    pass\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "Handler"]);
    assert_eq!(out.status.code(), Some(3), "an ambiguous name exits 3");
    let text = stdout(&out);
    assert!(
        text.contains("a.py") && text.contains("b.py"),
        "the candidate list names each file: {text}"
    );
    assert!(
        text.contains("a.Handler") && text.contains("b.Handler"),
        "the candidate list names each qualified path: {text}"
    );
}

// ----------------------------------------------------------------------------
// ctx map
// ----------------------------------------------------------------------------

/// `zeta_used` is called 3 times and sorts LAST alphabetically; `alpha_unused`
/// is never called and sorts FIRST. Reference-graph ranking must invert the
/// alphabetical order.
const RANKED_PY: &str = "\
def zeta_used():
    return 1


def alpha_unused():
    return 2


def c1():
    return zeta_used()


def c2():
    return zeta_used()


def c3():
    return zeta_used()
";

#[test]
fn map_ranking_orders_by_reference_count_not_alphabetical() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", RANKED_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let zi = text
        .find("zeta_used")
        .unwrap_or_else(|| panic!("zeta_used absent:\n{text}"));
    let ai = text
        .find("alpha_unused")
        .unwrap_or_else(|| panic!("alpha_unused absent:\n{text}"));
    assert!(
        zi < ai,
        "the referenced symbol ranks above the unreferenced one:\n{text}"
    );
}

#[test]
fn map_token_budget_truncates_output() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut src = String::new();
    for i in 0..20 {
        src.push_str(&format!("def f{i}():\n    return {i}\n\n\n"));
    }
    write(root, "many.py", &src);
    sleep(PAST);
    init(root);

    let small = stdout(&ctx(root, &["map", "--tokens", "5"]));
    let big = stdout(&ctx(root, &["map", "--tokens", "100000"]));
    // C7: ceil(bytes/4) <= budget.
    let small_tokens = small.len().div_ceil(4);
    assert!(
        small_tokens <= 5,
        "a --tokens 5 budget bounds the output to <=5 tokens ({small_tokens}): {small:?}"
    );
    assert!(
        small.lines().count() < big.lines().count(),
        "the small budget truncates relative to the large one"
    );
}

#[test]
fn map_doc_appends_first_docstring_lines() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "d.py",
        "def documented():\n    \"\"\"Doc marker.\"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let plain = stdout(&ctx(root, &["map"]));
    assert!(!plain.contains("Doc marker."), "default omits docs: {plain}");
    let doc = stdout(&ctx(root, &["map", "--doc"]));
    assert!(
        doc.contains("Doc marker."),
        "--doc appends the first docstring line: {doc}"
    );
}

// ----------------------------------------------------------------------------
// --json variants
// ----------------------------------------------------------------------------

#[test]
fn json_variants_emit_the_asserted_key_per_verb() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def solo():\n    return 1\n");
    sleep(PAST);
    init(root);

    let tree = ctx(root, &["tree", "app.py", "--json"]);
    assert_eq!(tree.status.code(), Some(0));
    let tv: serde_json::Value = serde_json::from_str(&stdout(&tree)).unwrap();
    assert!(tv.get("symbols").is_some(), "tree --json has .symbols");

    let sig = ctx(root, &["sig", "solo", "--json"]);
    assert_eq!(sig.status.code(), Some(0));
    let sv: serde_json::Value = serde_json::from_str(&stdout(&sig)).unwrap();
    assert!(sv.get("signature").is_some(), "sig --json has .signature");

    let map = ctx(root, &["map", "--json"]);
    assert_eq!(map.status.code(), Some(0));
    let mv: serde_json::Value = serde_json::from_str(&stdout(&map)).unwrap();
    assert!(mv.get("symbols").is_some(), "map --json has .symbols");
}

// ----------------------------------------------------------------------------
// Rebuild equivalence (C4, CUJ11)
// ----------------------------------------------------------------------------

const EQUIV_PY: &str = "\
class Handler:
    \"\"\"Handles.\"\"\"
    def handle(self):
        return other()


def other():
    return 1
";

fn cache_dir(root: &Path) -> std::path::PathBuf {
    root.join(".context").join("cache")
}

fn journal_last_parsed(root: &Path) -> u64 {
    let text = std::fs::read_to_string(cache_dir(root).join("sync-journal.jsonl")).unwrap();
    let last = text.lines().filter(|l| !l.trim().is_empty()).next_back().unwrap();
    let v: serde_json::Value = serde_json::from_str(last).unwrap();
    v["parsed"].as_u64().unwrap()
}

#[test]
fn rebuild_equivalence_byte_identical_after_cache_delete() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", EQUIV_PY);
    sleep(PAST);
    init(root);

    let before_map = stdout(&ctx(root, &["map"]));
    let before_tree = stdout(&ctx(root, &["tree", "app.py"]));
    let before_sig = stdout(&ctx(root, &["sig", "Handler"]));

    std::fs::remove_dir_all(cache_dir(root)).unwrap();
    sleep(PAST);

    let after_map = stdout(&ctx(root, &["map"]));
    let after_tree = stdout(&ctx(root, &["tree", "app.py"]));
    let after_sig = stdout(&ctx(root, &["sig", "Handler"]));

    assert_eq!(before_map, after_map, "map output is rebuild-stable");
    assert_eq!(before_tree, after_tree, "tree output is rebuild-stable");
    assert_eq!(before_sig, after_sig, "sig output is rebuild-stable");
}

#[test]
fn rebuild_equivalence_transparent_rebuild_on_tampered_schema_version() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", EQUIV_PY);
    write(root, "other.py", "def z():\n    return 1\n");
    sleep(PAST);
    init(root);

    // Prime the index.
    let _ = ctx(root, &["map"]);

    // Tamper the persisted schema version so the next open must rebuild (C4).
    {
        let conn = rusqlite::Connection::open(cache_dir(root).join("index.sqlite")).unwrap();
        conn.execute("UPDATE schema_meta SET version = 999", []).unwrap();
    }
    sleep(PAST);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0), "the query still succeeds");
    // A transparent rebuild re-parses every indexed file.
    let indexed = 2;
    assert_eq!(
        journal_last_parsed(root),
        indexed,
        "the post-tamper sweep re-parsed the full indexed file count"
    );
}
