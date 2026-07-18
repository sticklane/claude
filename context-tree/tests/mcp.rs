//! R15 MCP-server integration tests. Each drives `ctx mcp` over stdio with a
//! scripted newline-delimited JSON-RPC exchange (spec handshake, then the
//! request under test), asserting the typed tool set, byte-identical `tree`
//! output vs the CLI, and that a `notes add` tool call writes a note file.

use serde_json::{Value, json};
use std::collections::HashSet;
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

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

/// Spawn `ctx mcp` in `root`, send the MCP `initialize`/`initialized` handshake
/// followed by `requests`, close stdin, and return every JSON-RPC message
/// parsed from stdout. Closing stdin drives the server to EOF, so reading
/// stdout to end never hangs; the requests are tiny, so writing them all before
/// reading cannot fill the stdout pipe and deadlock.
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
    drop(stdin); // EOF -> server shuts down after answering.

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

/// The single response whose `id` matches `id`.
fn response(responses: &[Value], id: i64) -> &Value {
    responses
        .iter()
        .find(|r| r["id"] == json!(id))
        .unwrap_or_else(|| panic!("no JSON-RPC response with id {id}; got {responses:?}"))
}

/// Number of `.md` files directly under `dir` (0 when it does not exist).
fn count_notes(dir: &Path) -> usize {
    match std::fs::read_dir(dir) {
        Ok(entries) => entries
            .filter_map(Result::ok)
            .filter(|e| e.path().extension().is_some_and(|x| x == "md"))
            .count(),
        Err(_) => 0,
    }
}

#[test]
fn mcp_tool_list() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);
    init(root);

    let list = json!({ "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {} });
    let responses = mcp_session(root, &[list]);
    let resp = response(&responses, 1);
    let tools = resp["result"]["tools"]
        .as_array()
        .unwrap_or_else(|| panic!("tools/list result has no tools array: {resp}"));
    let names: HashSet<&str> = tools
        .iter()
        .map(|t| t["name"].as_str().expect("tool name is a string"))
        .collect();

    for expected in [
        "tree",
        "sig",
        "map",
        "deps",
        "refs",
        "at",
        "notes_add",
        "notes",
        "notes_list",
    ] {
        assert!(
            names.contains(expected),
            "MCP tool `{expected}` must be present; got {names:?}"
        );
    }
}

#[test]
fn mcp_tree_matches_cli() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "a.py",
        "def a():\n    return 1\n\nclass C:\n    def m(self):\n        return 2\n",
    );
    sleep(PAST);
    init(root);

    // Warm the index via the CLI so the expected output and the MCP call both
    // observe an identical, already-synced snapshot.
    let expected = stdout(&ctx(root, &["tree", "--json", "."]));

    let call = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": { "name": "tree", "arguments": { "path": "." } }
    });
    let responses = mcp_session(root, &[call]);
    let resp = response(&responses, 1);
    let text = resp["result"]["content"][0]["text"]
        .as_str()
        .unwrap_or_else(|| panic!("tools/call tree result has no text content: {resp}"));

    assert_eq!(
        text, expected,
        "MCP `tree` output must be byte-identical to `ctx tree --json .`"
    );
}

#[test]
fn mcp_notes_add_writes_file() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def alpha():\n    return 1\n");
    sleep(PAST);
    init(root);

    let notes_dir = root.join(".context/notes");
    let before = count_notes(&notes_dir);

    let call = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "notes_add",
            "arguments": { "symbol": "alpha", "text": "remember this" }
        }
    });
    let responses = mcp_session(root, &[call]);
    let resp = response(&responses, 1);
    assert_ne!(
        resp["result"]["isError"],
        json!(true),
        "notes_add must not report an error: {resp}"
    );

    let after = count_notes(&notes_dir);
    assert_eq!(
        after,
        before + 1,
        "notes_add via the MCP path must create exactly one note file on disk"
    );
}
