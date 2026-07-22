//! specs/ctx-output-shape-gaps R1 — zero-result diagnostic tails for `ctx refs`
//! and `ctx deps`. A resolved-but-empty query must explain the emptiness on
//! stderr (and a `--json` `note` field) instead of printing silent nothing, so
//! an agent can tell "queried the wrong thing" from "genuinely zero" without
//! falling back to grep. Three branches:
//!   (a) `refs` on a resolved symbol with zero references — defs stay on stdout,
//!       stderr tails "0 references to <query>"; a module-level symbol also
//!       suggests `ctx deps --reverse <file>`.
//!   (b) `deps` on an INDEXED path with zero edges — states the fact.
//!   (c) `deps` on a path NOT in the index — states "path not in index".
//! Exit codes are unchanged; a symbol no-match keeps absence-check's output and
//! never emits an R1 tail.

use serde_json::{Value, json};
use std::io::{Read, Write};
use std::path::Path;
use std::process::{Command, Output, Stdio};
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

/// The shared fixture used by every branch:
/// - `w.ts` — a TS `namespace Widget` (kind == "module") with zero refs.
/// - `o.py` — `def orphan()` : a non-module symbol with zero refs, and a leaf
///   file no one imports (zero reverse edges, zero forward).
/// - `pkg/util.py` + `app.py` — `helper` is imported and called, so `helper`
///   has references and `pkg/util.py` has a reverse importer.
fn setup(root: &Path) {
    write(
        root,
        "w.ts",
        "namespace Widget {\n  export const x = 1;\n}\n",
    );
    write(root, "o.py", "def orphan():\n    return 1\n");
    write(root, "pkg/util.py", "def helper():\n    return 1\n");
    write(
        root,
        "app.py",
        "from pkg.util import helper\n\n\ndef use():\n    return helper()\n",
    );
    sleep(PAST);
    init(root);
}

// ----------------------------------------------------------------------------
// (a) refs zero references
// ----------------------------------------------------------------------------

#[test]
fn refs_zero_refs_keeps_defs_on_stdout_and_tails_stderr() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["refs", "orphan"]);
    assert_eq!(out.status.code(), Some(0), "zero-ref refs still exits 0");
    assert!(
        stdout(&out).contains("def "),
        "the def line is preserved on stdout: {:?}",
        stdout(&out)
    );
    assert!(
        stderr(&out).contains("0 references to orphan"),
        "stderr tails the zero-reference fact using the QUERY: {:?}",
        stderr(&out)
    );
    // A non-module symbol does NOT get the deps suggestion.
    assert!(
        !stderr(&out).contains("ctx deps --reverse"),
        "a non-module symbol gets no deps suggestion: {:?}",
        stderr(&out)
    );
}

#[test]
fn refs_zero_refs_module_symbol_suggests_deps_reverse() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["refs", "Widget"]);
    assert_eq!(out.status.code(), Some(0), "module zero-ref refs exits 0");
    assert!(
        stderr(&out).contains("0 references to Widget"),
        "stderr tails the zero-reference fact: {:?}",
        stderr(&out)
    );
    assert!(
        stderr(&out).contains("ctx deps --reverse w.ts"),
        "a module-level symbol suggests deps --reverse on its file: {:?}",
        stderr(&out)
    );
}

#[test]
fn refs_zero_refs_json_gains_note_and_keeps_legacy_keys() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["refs", "orphan", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();
    assert!(
        v.get("note").and_then(Value::as_str).is_some(),
        "zero-ref --json gains a note field: {v}"
    );
    // Legacy keys (the task-07 shape) survive unchanged.
    assert!(v.get("symbol").is_some(), "legacy symbol key survives: {v}");
    assert!(
        v.get("definitions").is_some(),
        "legacy definitions key survives: {v}"
    );
    assert!(
        v.get("truncated").is_some(),
        "legacy truncated key survives: {v}"
    );
    let refs = v.get("references").and_then(Value::as_array).unwrap();
    assert!(refs.is_empty(), "references array is empty: {v}");
}

#[test]
fn refs_with_references_json_has_no_note() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["refs", "helper", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();
    let refs = v.get("references").and_then(Value::as_array).unwrap();
    assert!(!refs.is_empty(), "helper has references: {v}");
    assert!(
        v.get("note").is_none(),
        "a non-empty result carries no note (note is zero-result only): {v}"
    );
}

// ----------------------------------------------------------------------------
// (b) deps on an indexed path with zero edges
// ----------------------------------------------------------------------------

#[test]
fn deps_reverse_indexed_leaf_tails_no_importers() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["deps", "o.py", "--reverse"]);
    assert_eq!(out.status.code(), Some(0), "zero-edge deps exits 0");
    assert!(
        stdout(&out).trim().is_empty(),
        "stdout stays empty for a zero-edge deps: {:?}",
        stdout(&out)
    );
    assert!(
        stderr(&out).contains("no indexed importers of o.py"),
        "stderr states the zero-importers fact for an indexed leaf: {:?}",
        stderr(&out)
    );
}

#[test]
fn deps_forward_indexed_zero_edges_tails_the_fact() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["deps", "o.py"]);
    assert_eq!(out.status.code(), Some(0));
    assert!(
        stdout(&out).trim().is_empty(),
        "stdout stays empty: {:?}",
        stdout(&out)
    );
    assert!(
        stderr(&out).contains("o.py") && !stderr(&out).contains("not in index"),
        "forward zero-edge on an indexed path states the fact, not 'not in index': {:?}",
        stderr(&out)
    );
}

// ----------------------------------------------------------------------------
// (c) deps on a path NOT in the index
// ----------------------------------------------------------------------------

#[test]
fn deps_nonexistent_path_tails_path_not_in_index() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["deps", "zzz/nope.py", "--reverse"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "a not-in-index path still exits 0"
    );
    assert!(
        stdout(&out).trim().is_empty(),
        "stdout stays empty: {:?}",
        stdout(&out)
    );
    assert!(
        stderr(&out).contains("path not in index: zzz/nope.py"),
        "stderr states the path is not indexed: {:?}",
        stderr(&out)
    );
}

#[test]
fn deps_indexed_leaf_and_typo_are_distinguished() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let leaf = ctx(root, &["deps", "o.py", "--reverse"]);
    let typo = ctx(root, &["deps", "zzz/nope.py", "--reverse"]);
    // The whole point: an indexed leaf and a typo are NOT byte-identical.
    assert_ne!(
        stderr(&leaf),
        stderr(&typo),
        "an indexed leaf and a non-indexed typo must produce different tails"
    );
    assert!(
        stderr(&leaf).contains("no indexed importers"),
        "leaf → no-importers: {:?}",
        stderr(&leaf)
    );
    assert!(
        stderr(&typo).contains("not in index"),
        "typo → not-in-index: {:?}",
        stderr(&typo)
    );
}

#[test]
fn deps_json_zero_edges_gains_note_and_keeps_legacy_keys() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["deps", "o.py", "--reverse", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();
    assert!(
        v.get("note").and_then(Value::as_str).is_some(),
        "zero-edge deps --json gains a note: {v}"
    );
    assert!(v.get("path").is_some(), "legacy path key survives: {v}");
    assert!(
        v.get("reverse").is_some(),
        "legacy reverse key survives: {v}"
    );
    let edges = v.get("edges").and_then(Value::as_array).unwrap();
    assert!(edges.is_empty(), "edges array is empty: {v}");
}

#[test]
fn deps_json_nonexistent_path_note_says_not_in_index() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["deps", "zzz/nope.py", "--reverse", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();
    let note = v.get("note").and_then(Value::as_str).unwrap();
    assert!(
        note.contains("not in index"),
        "the note distinguishes not-in-index: {v}"
    );
    let edges = v.get("edges").and_then(Value::as_array).unwrap();
    assert!(edges.is_empty(), "edges array is empty: {v}");
}

// ----------------------------------------------------------------------------
// Negative: a symbol no-match keeps absence-check's output, never an R1 tail
// ----------------------------------------------------------------------------

#[test]
fn refs_symbol_no_match_keeps_boundary_output_and_no_r1_tail() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let out = ctx(root, &["refs", "NoSuchSymbol"]);
    assert_eq!(
        out.status.code(),
        Some(1),
        "a symbol no-match keeps its own exit code (EXIT_NO_MATCH)"
    );
    assert!(
        stderr(&out).contains("no symbol matches"),
        "no-match keeps absence-check's boundary output: {:?}",
        stderr(&out)
    );
    assert!(
        !stderr(&out).contains("0 references to"),
        "a no-match must NOT emit R1's zero-references tail: {:?}",
        stderr(&out)
    );
}

// ----------------------------------------------------------------------------
// MCP parity — the note arrives through the shared render() core, not just CLI
// ----------------------------------------------------------------------------

/// Spawn `ctx mcp`, run the handshake + `requests`, and return every parsed
/// JSON-RPC message. (Compact local copy of tests/mcp.rs's helper.)
fn mcp_session(root: &Path, requests: &[Value]) -> Vec<Value> {
    let mut child = Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .arg("mcp")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();

    let mut stdin = child.stdin.take().unwrap();
    let initialize = json!({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": { "name": "ctx-test", "version": "0" }
        }
    });
    writeln!(stdin, "{initialize}").unwrap();
    let initialized = json!({ "jsonrpc": "2.0", "method": "notifications/initialized" });
    writeln!(stdin, "{initialized}").unwrap();
    for r in requests {
        writeln!(stdin, "{r}").unwrap();
    }
    drop(stdin);

    let mut out = String::new();
    child
        .stdout
        .take()
        .unwrap()
        .read_to_string(&mut out)
        .unwrap();
    child.wait().unwrap();

    out.lines()
        .filter_map(|l| serde_json::from_str::<Value>(l).ok())
        .collect()
}

fn response(responses: &[Value], id: i64) -> &Value {
    responses
        .iter()
        .find(|r| r["id"] == json!(id))
        .unwrap_or_else(|| panic!("no JSON-RPC response with id {id}; got {responses:?}"))
}

#[test]
fn refs_zero_refs_note_arrives_through_mcp() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let call = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": { "name": "refs", "arguments": { "symbol": "orphan" } }
    });
    let responses = mcp_session(root, &[call]);
    let resp = response(&responses, 1);
    let text = resp["result"]["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("tools/call refs has no text content: {resp}"));
    let v: Value = serde_json::from_str(text).unwrap();
    assert!(
        v.get("note").and_then(Value::as_str).is_some(),
        "the zero-ref note arrives through the MCP refs tool: {v}"
    );
}

#[test]
fn deps_zero_edges_note_arrives_through_mcp() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    setup(root);

    let call = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": { "name": "deps", "arguments": { "path": "o.py", "reverse": true } }
    });
    let responses = mcp_session(root, &[call]);
    let resp = response(&responses, 1);
    let text = resp["result"]["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("tools/call deps has no text content: {resp}"));
    let v: Value = serde_json::from_str(text).unwrap();
    assert!(
        v.get("note").and_then(Value::as_str).is_some(),
        "the zero-edge note arrives through the MCP deps tool: {v}"
    );
}
