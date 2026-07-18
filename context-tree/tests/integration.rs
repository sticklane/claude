//! Cross-subsystem integration tests (task 14). These exercise contracts that
//! genuinely span extraction + query + notes + re-anchoring together — flows no
//! single earlier task's unit tests could cover in isolation. They drive the
//! real `ctx` binary end to end.

use context_tree::sync;
use serde_json::Value;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
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

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

/// `ctx notes list --json` as a vector of note objects (drives a sync first).
fn list_notes(root: &Path) -> Vec<Value> {
    serde_json::from_str(&ctx_ok(root, &["notes", "list", "--json"])).unwrap()
}

fn anchor(n: &Value) -> String {
    n["anchor"].as_str().unwrap().to_string()
}
fn fresh(n: &Value) -> bool {
    n["fresh"].as_bool().unwrap()
}

fn latest_journal(root: &Path) -> Value {
    let text = std::fs::read_to_string(sync::cache_dir(root).join("sync-journal.jsonl")).unwrap();
    let last = text.lines().rfind(|l| !l.trim().is_empty()).unwrap();
    serde_json::from_str(last).unwrap()
}

fn note_files(root: &Path) -> Vec<PathBuf> {
    let dir = root.join(".context/notes");
    let mut v: Vec<PathBuf> = std::fs::read_dir(&dir)
        .unwrap()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("md"))
        .collect();
    v.sort();
    v
}

/// The `anchor_hash:` frontmatter field of the note file whose `anchor_path`
/// contains `symbol`.
fn anchor_hash_for(root: &Path, symbol: &str) -> String {
    for f in note_files(root) {
        let text = std::fs::read_to_string(&f).unwrap();
        let anchors_symbol = text
            .lines()
            .any(|l| l.starts_with("anchor_path:") && l.contains(symbol));
        if anchors_symbol {
            for l in text.lines() {
                if let Some(rest) = l.strip_prefix("anchor_hash:") {
                    return rest.trim().to_string();
                }
            }
        }
    }
    panic!("no note file anchored to {symbol}");
}

// A file with three sibling functions where `middle` carries a mid-function
// syntax error in the BROKEN variant (`x = = =`) while `good_one`/`good_two`
// stay recoverable (R1 best-effort). Byte-identical GOOD form so a repair
// restores the exact C2 body hash and re-derives freshness.
const PF_GOOD: &str = "def good_one():\n    return 1\n\ndef middle():\n    x = 5\n    return x\n\ndef good_two():\n    return 3\n";
const PF_BROKEN: &str = "def good_one():\n    return 1\n\ndef middle():\n    x = = =\n    return 2\n\ndef good_two():\n    return 3\n";

/// Task 14 Step 1: one integration test covering all six mid-edit-robustness
/// sub-assertions across extraction + query + notes + re-anchoring, driven
/// through the full sync+query+notes flow (task 10 unit-tests re-anchoring
/// exclusion in isolation; this test exercises it inside the whole pipeline).
#[test]
fn mid_edit_robustness() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "m.py", PF_GOOD);
    sleep(PAST);

    // Notes on the soon-to-break symbol and on an untouched sibling.
    ctx_ok(root, &["notes", "add", "middle", "broken-symbol note"]);
    ctx_ok(root, &["notes", "add", "good_one", "sibling note"]);
    assert!(
        list_notes(root).iter().all(fresh),
        "both notes fresh at creation"
    );
    let hash_before = anchor_hash_for(root, "middle");

    // Introduce a mid-function syntax error inside `middle`.
    sleep(PAST);
    write(root, "m.py", PF_BROKEN);
    sleep(PAST);

    // (a) sibling symbols in the same file still list via `ctx tree`.
    let tree = ctx_ok(root, &["tree", "m.py"]);
    assert!(
        tree.contains("good_one") && tree.contains("good_two"),
        "recoverable siblings still list under a parse failure: {tree}"
    );

    // (b) `ctx at` on the broken span resolves to the module fallback, no error.
    let at = ctx(root, &["at", "m.py:5", "--json"]);
    assert!(at.status.success(), "at on broken span exits 0: {at:?}");
    let at_v: Value = serde_json::from_str(&stdout(&at)).unwrap();
    let chain = at_v["chain"].as_array().expect("at --json has .chain");
    assert_eq!(
        chain.first().and_then(|e| e["kind"].as_str()),
        Some("module"),
        "broken span falls back to the module surface: {at_v}"
    );

    let broken = list_notes(root);
    // (c) the note anchored to the untouched sibling keeps its freshness.
    let sibling = broken
        .iter()
        .find(|n| anchor(n).contains("good_one"))
        .unwrap();
    assert!(fresh(sibling), "untouched sibling stays fresh: {sibling:?}");

    // (d) no re-anchoring fires for the parse-failed file.
    assert_eq!(
        latest_journal(root)["pending_reanchors"].as_u64(),
        Some(0),
        "no re-anchor attempt against a parse-failed file"
    );

    // (e) the note on the BROKEN symbol reads stale while broken, its anchor
    // binding untouched, and re-derives fresh after repair.
    let broken_note = broken
        .iter()
        .find(|n| anchor(n).contains("middle"))
        .unwrap();
    assert!(
        !fresh(broken_note),
        "broken-symbol note reads stale: {broken_note:?}"
    );
    assert_eq!(
        anchor_hash_for(root, "middle"),
        hash_before,
        "anchor hash binding is never system-rewritten (R13)"
    );

    // (f) repairing the error restores full facts on the next sync.
    sleep(PAST);
    write(root, "m.py", PF_GOOD);
    sleep(PAST);
    let repaired = list_notes(root);
    assert!(
        repaired.iter().all(fresh),
        "both notes re-derive fresh after repair: {repaired:?}"
    );
    let tree2 = ctx_ok(root, &["tree", "m.py"]);
    assert!(
        tree2.contains("good_one") && tree2.contains("middle") && tree2.contains("good_two"),
        "all three symbols list again after repair: {tree2}"
    );
    assert!(
        ctx(root, &["sig", "middle"]).status.success(),
        "the repaired symbol resolves for full facts again"
    );
}

/// Pipe `json` through `jq .`; assert jq exits 0 (parses as JSON).
fn pipe_through_jq(json: &str) {
    let mut child = Command::new("jq")
        .arg(".")
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .expect("jq must be installed for the --json aggregate test");
    child
        .stdin
        .take()
        .unwrap()
        .write_all(json.as_bytes())
        .unwrap();
    assert!(
        child.wait().unwrap().success(),
        "jq rejected the payload: {json}"
    );
}

// A fixture exercising every query verb: `solo` carries a docstring and is
// referenced by `caller`, so tree/sig/map/deps/refs/at all have real payloads.
const JSON_FIXTURE: &str = "def solo():\n    \"\"\"A solo function.\"\"\"\n    return 1\n\n\ndef caller():\n    return solo()\n";

/// Task 14 Step 2: cross-verb `--json` consistency — each of the six query
/// verbs pipes through `jq .` with exit 0 and carries its asserted payload key
/// (tasks 06/07 test this per-command; this is the aggregate consistency check).
#[test]
fn json_all_verbs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "app.py", JSON_FIXTURE);
    sleep(PAST);

    let cases: [(&[&str], &str); 6] = [
        (&["tree", "app.py", "--json"], "symbols"),
        (&["sig", "solo", "--json"], "signature"),
        (&["map", "--json"], "symbols"),
        (&["deps", "app.py", "--json"], "edges"),
        (&["refs", "solo", "--json"], "references"),
        (&["at", "app.py:2", "--json"], "chain"),
    ];
    for (args, key) in cases {
        let out = ctx(root, args);
        assert!(out.status.success(), "ctx {args:?} exits 0: {out:?}");
        let text = stdout(&out);
        pipe_through_jq(&text);
        let v: Value = serde_json::from_str(&text).unwrap();
        assert!(v.get(key).is_some(), "ctx {args:?} carries .{key}: {v}");
    }
}
