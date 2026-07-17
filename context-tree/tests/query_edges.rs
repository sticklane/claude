//! R3/R9/R10/R19 + C1/C3/C10 integration tests for `ctx deps`, `ctx refs`, and
//! `ctx at` — the import-edge, reference, and position-resolution query verbs.

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
// ctx deps (R9)
// ----------------------------------------------------------------------------

#[test]
fn deps_forward_and_reverse_edges() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "pkg/util.py", "def helper():\n    return 1\n");
    write(
        root,
        "app.py",
        "from pkg.util import helper\n\n\ndef use():\n    return helper()\n",
    );
    sleep(PAST);
    init(root);

    // Forward: edges out of app.py name the imported module.
    let fwd = ctx(root, &["deps", "app.py"]);
    assert_eq!(fwd.status.code(), Some(0), "forward deps exits 0");
    assert!(
        stdout(&fwd).contains("pkg.util"),
        "forward deps names the imported module: {}",
        stdout(&fwd)
    );

    // Reverse: edges into pkg/util.py name the importing source.
    let rev = ctx(root, &["deps", "pkg/util.py", "--reverse"]);
    assert_eq!(rev.status.code(), Some(0), "reverse deps exits 0");
    assert!(
        stdout(&rev).contains("app"),
        "reverse deps names the importing source: {}",
        stdout(&rev)
    );
    // The forward-only target should not appear as a reverse edge into app.py.
    let rev_app = ctx(root, &["deps", "app.py", "--reverse"]);
    assert_eq!(rev_app.status.code(), Some(0));
    assert!(
        stdout(&rev_app).trim().is_empty(),
        "nothing imports app.py, so its reverse deps are empty: {:?}",
        stdout(&rev_app)
    );
}

#[test]
fn deps_empty_scope_exits_0() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "lonely.py", "def x():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["deps", "lonely.py"]);
    assert_eq!(out.status.code(), Some(0), "an import-less scope exits 0");
    assert!(
        stdout(&out).trim().is_empty(),
        "an import-less scope prints nothing: {:?}",
        stdout(&out)
    );
}

#[test]
fn deps_json_has_edges_key() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "pkg/util.py", "def helper():\n    return 1\n");
    write(root, "app.py", "from pkg.util import helper\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["deps", "app.py", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();
    assert!(v.get("edges").is_some(), "deps --json has .edges: {v}");
}

// ----------------------------------------------------------------------------
// ctx refs (R10)
// ----------------------------------------------------------------------------

#[test]
fn refs_heuristic_labels_definitions_and_references() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["refs", "target"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "refs on a defined symbol exits 0"
    );
    let text = stdout(&out);
    assert!(
        text.contains("heuristic"),
        "every result is labeled heuristic (no LSP pass yet): {text}"
    );
    assert!(
        text.lines()
            .any(|l| l.starts_with("def") && l.contains("target")),
        "the definition is listed: {text}"
    );
    assert!(
        text.lines()
            .any(|l| l.starts_with("ref") && l.contains("target")),
        "the call site is listed as a reference: {text}"
    );
    assert!(
        !text.contains("precise"),
        "nothing is labeled precise before the LSP pass: {text}"
    );
}

#[test]
fn refs_caps_at_50_per_direction_with_truncation_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut src = String::from("def target():\n    return 1\n\n\n");
    for i in 0..60 {
        src.push_str(&format!("def c{i}():\n    return target()\n\n\n"));
    }
    write(root, "many.py", &src);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["refs", "target"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let ref_lines = text.lines().filter(|l| l.starts_with("ref")).count();
    assert_eq!(ref_lines, 50, "references cap at 50 by default: {text}");
    assert!(
        text.contains("more") && text.contains("--limit"),
        "a truncation line names the omitted count and --limit: {text}"
    );
    assert!(
        text.contains("10"),
        "the omitted reference count (60 - 50 = 10) is named: {text}"
    );

    // Raising --limit shows more than the default cap.
    let raised = ctx(root, &["refs", "target", "--limit", "100"]);
    assert_eq!(raised.status.code(), Some(0));
    let raised_refs = stdout(&raised)
        .lines()
        .filter(|l| l.starts_with("ref"))
        .count();
    assert_eq!(raised_refs, 60, "--limit 100 lifts the cap to show all 60");
}

#[test]
fn refs_scope_aware_excludes_shadowed_local_keeps_cross_file() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    // Global definition of `target`.
    write(
        root,
        "util.ts",
        "export function target() {\n  return 1;\n}\n",
    );
    // A true cross-file call site (imports and calls the global).
    write(
        root,
        "app.ts",
        "import { target } from \"./util\";\nexport function useIt() {\n  return target();\n}\n",
    );
    // A function-local `const target` shadows the global; its call is a local,
    // not a reference to the global function.
    write(
        root,
        "shadow.ts",
        "export function outer() {\n  const target = () => 9;\n  return target();\n}\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["refs", "target"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "refs resolves the global uniquely: {} / {}",
        stdout(&out),
        stderr(&out)
    );
    let text = stdout(&out);
    let refs: Vec<&str> = text.lines().filter(|l| l.starts_with("ref")).collect();
    let joined = refs.join("\n");
    assert!(
        refs.iter().any(|l| l.contains("app.ts")),
        "the true cross-file call site in app.ts is retained: {joined}"
    );
    assert!(
        !refs.iter().any(|l| l.contains("shadow.ts")),
        "the shadowed function-local reference in shadow.ts is excluded: {joined}"
    );
}

#[test]
fn refs_no_match_exits_1() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def target():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["refs", "nonexistent_symbol"]);
    assert_eq!(out.status.code(), Some(1), "an unresolved symbol exits 1");
}

#[test]
fn refs_json_has_references_key() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["refs", "target", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();
    assert!(
        v.get("references").is_some(),
        "refs --json has .references: {v}"
    );
}

// ----------------------------------------------------------------------------
// ctx at (R19)
// ----------------------------------------------------------------------------

const AT_PY: &str = "\
def outer():
    def nested():
        return 1
    return nested()


# a bare module-level comment
";

#[test]
fn at_containment_chain_for_nested_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", AT_PY);
    sleep(PAST);
    init(root);

    // Line 3 (`return 1`) sits inside the nested function.
    let out = ctx(root, &["at", "app.py:3"]);
    assert_eq!(out.status.code(), Some(0), "a resolvable position exits 0");
    let text = stdout(&out);
    assert!(
        text.contains("module"),
        "the chain starts at the module: {text}"
    );
    assert!(
        text.contains("outer"),
        "the chain names the outer function: {text}"
    );
    assert!(
        text.contains("nested"),
        "the chain names the innermost function: {text}"
    );
    // Innermost is indented more deeply than its container.
    let outer_indent = indent_of(&text, "outer");
    let nested_indent = indent_of(&text, "nested");
    assert!(
        nested_indent > outer_indent,
        "the nested symbol is indented under its container: {text}"
    );
}

#[test]
fn at_containment_module_fallback_outside_definitions() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", AT_PY);
    sleep(PAST);
    init(root);

    // Line 7 (the module-level comment) is enclosed by no definition.
    let out = ctx(root, &["at", "app.py:7"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "the module fallback still exits 0"
    );
    let text = stdout(&out);
    assert!(
        text.contains("module"),
        "an out-of-definition line resolves to the module symbol: {text}"
    );
    assert!(
        !text.contains("nested"),
        "the module fallback names no enclosing function: {text}"
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
fn at_exit4_nonexistent() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def a():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["at", "nope.py:1"]);
    assert_eq!(out.status.code(), Some(4), "a nonexistent file exits 4");
    assert!(
        !stderr(&out).trim().is_empty() || !stdout(&out).trim().is_empty(),
        "the failure names a reason"
    );
}

#[test]
fn at_exit4_unsupported_extension() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def a():\n    return 1\n");
    write(root, "notes.txt", "not source code\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["at", "notes.txt:1"]);
    assert_eq!(
        out.status.code(),
        Some(4),
        "an unsupported extension exits 4"
    );
    let reason = format!("{}{}", stdout(&out), stderr(&out));
    assert!(
        reason.to_lowercase().contains("unsupported")
            || reason.to_lowercase().contains("extension"),
        "the reason names the unsupported extension: {reason}"
    );
}

#[test]
fn at_exit4_ignored() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def a():\n    return 1\n");
    write(root, "secret.py", "def s():\n    return 2\n");
    write(root, ".ctxignore", "secret.py\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["at", "secret.py:1"]);
    assert_eq!(out.status.code(), Some(4), "an ignored file exits 4");
    let reason = format!("{}{}", stdout(&out), stderr(&out));
    assert!(
        reason.to_lowercase().contains("ignore"),
        "the reason names the ignore: {reason}"
    );
}

#[test]
fn at_resolves_symbol_on_its_own_signature_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", AT_PY);
    sleep(PAST);
    init(root);

    // Line 2 is `nested`'s own signature line (`    def nested():`), indented.
    // The queried byte at column 0 precedes the def token, so start-byte
    // containment alone would resolve to the parent; span/line overlap must
    // still resolve to `nested` itself.
    let out = ctx(root, &["at", "app.py:2"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let innermost = text
        .lines()
        .rev()
        .find(|l| !l.trim().is_empty())
        .unwrap_or("");
    assert!(
        innermost.contains("nested"),
        "querying a symbol's own signature line resolves to that symbol: {text}"
    );
}

#[test]
fn at_containment_keeps_nested_module() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    // `helper` lives inside a nested module `tests` — a real container that must
    // stay in the chain (only the file-level module is deduped).
    write(
        root,
        "lib.rs",
        "mod tests {\n    fn helper() {\n        let x = 1;\n    }\n}\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["at", "lib.rs:3"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(
        text.contains("helper"),
        "the chain names the enclosing function: {text}"
    );
    assert!(
        text.lines()
            .any(|l| l.trim_start().starts_with("module") && l.contains("tests")),
        "the nested module `tests` is retained as a chain entry: {text}"
    );
}
