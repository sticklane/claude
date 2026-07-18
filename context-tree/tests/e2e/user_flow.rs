//! Task 14 Step 3: end-to-end user-flow walkthrough (the SPEC CUJ0/thesis
//! adoption journey exercised as a real command flow) on a fixture repo
//! containing three of the twelve supported languages. Compiled as a module of
//! the top-level `tests/e2e.rs` target so `cargo test e2e_user_flow` runs it.

use serde_json::Value;
use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms).
const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

fn ctx(root: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .output()
        .unwrap()
}

fn ctx_ok(root: &Path, args: &[&str]) -> String {
    let out = ctx(root, args);
    assert!(out.status.success(), "ctx {args:?} failed: {out:?}");
    String::from_utf8(out.stdout).unwrap()
}

fn list_notes(root: &Path) -> Vec<Value> {
    serde_json::from_str(&ctx_ok(root, &["notes", "list", "--json"])).unwrap()
}

// Three languages: Python, TypeScript, Go — proves `ctx map` spans a
// multi-language repo before the note flow operates on the Python symbol.
const APP_PY: &str = "def process():\n    return 1\n";
const APP_PY_REFACTORED: &str = "def process():\n    return 42\n";
const LIB_TS: &str = "export function handler() {\n  return 2;\n}\n";
const MAIN_GO: &str = "package main\n\nfunc Run() int {\n\treturn 3\n}\n";

#[test]
fn e2e_user_flow() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();

    // init -> a multi-language working tree.
    ctx_ok(root, &["init"]);
    write(root, "app.py", APP_PY);
    write(root, "lib.ts", LIB_TS);
    write(root, "main.go", MAIN_GO);
    sleep(PAST);

    // map: the whole-repo surface spans all three languages.
    let map = ctx_ok(root, &["map"]);
    assert!(
        map.contains("process") && map.contains("handler") && map.contains("Run"),
        "map spans Python + TypeScript + Go symbols: {map}"
    );

    // sig: the targeted single-symbol view resolves the Python symbol.
    let sig = ctx_ok(root, &["sig", "process"]);
    assert!(
        sig.contains("process"),
        "sig resolves the noted symbol: {sig}"
    );

    // notes add: attach a note to the symbol; it starts fresh.
    ctx_ok(
        root,
        &["notes", "add", "process", "watch the return contract"],
    );
    let notes = list_notes(root);
    assert_eq!(notes.len(), 1, "one note attached: {notes:?}");
    assert!(
        notes[0]["fresh"].as_bool().unwrap(),
        "note fresh at creation: {notes:?}"
    );

    // refactor: edit the noted symbol's body.
    sleep(PAST);
    write(root, "app.py", APP_PY_REFACTORED);
    sleep(PAST);

    // stale flag: the note's derived freshness flips.
    let after = list_notes(root);
    assert_eq!(after.len(), 1);
    assert!(
        !after[0]["fresh"].as_bool().unwrap(),
        "note reads stale after the refactor: {after:?}"
    );

    // notes list --stale: the refactored symbol's note surfaces.
    let stale = ctx_ok(root, &["notes", "list", "--stale"]);
    assert!(
        stale.contains("process"),
        "the stale note surfaces in `notes list --stale`: {stale}"
    );
}
