//! R2 `ctx show <symbol>` integration tests: exact-span retrieval from the
//! freshly-reconciled index, staleness re-resolution, `--head` truncation, and
//! `--json`.

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

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

#[test]
fn show_prints_exact_symbol_span_no_more_no_less() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "x = 1\n\n\ndef solo():\n    return 1\n\n\ny = 2\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["show", "solo"]);
    assert_eq!(out.status.code(), Some(0), "unique match exits 0: {out:?}");
    assert_eq!(stdout(&out), "def solo():\n    return 1\n");
}

#[test]
fn show_reresolves_span_after_an_edit_shifts_the_symbol_down() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def solo():\n    return 1\n");
    sleep(PAST);
    init(root);

    let before = ctx(root, &["show", "solo", "--json"]);
    assert_eq!(before.status.code(), Some(0));
    let before_json: serde_json::Value = serde_json::from_str(&stdout(&before)).unwrap();
    assert_eq!(before_json["start_line"], 1);

    // Insert lines ABOVE the symbol so its line range moves down. A
    // fixed-range re-read (no re-sync) would keep pointing at the OLD lines
    // and fail this assertion.
    write(
        root,
        "app.py",
        "a = 1\nb = 2\nc = 3\n\ndef solo():\n    return 1\n",
    );
    sleep(PAST);

    let after = ctx(root, &["show", "solo", "--json"]);
    assert_eq!(after.status.code(), Some(0));
    let after_json: serde_json::Value = serde_json::from_str(&stdout(&after)).unwrap();
    assert_eq!(
        after_json["start_line"], 5,
        "the sweep re-resolves the shifted span: {after_json}"
    );
    assert_eq!(after_json["end_line"], 6);
    assert_eq!(after_json["text"], "def solo():\n    return 1");
}

#[test]
fn show_head_caps_output_at_n_lines() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut body = String::from("def solo():\n");
    for i in 0..10 {
        body.push_str(&format!("    x{i} = {i}\n"));
    }
    body.push_str("    return 1\n");
    write(root, "app.py", &body);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["show", "solo", "--head", "3"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let lines: Vec<&str> = text.lines().collect();
    assert_eq!(lines.len(), 4, "3 body lines + 1 truncation tail: {text:?}");
    assert_eq!(lines[0], "def solo():");
    assert_eq!(lines[1], "    x0 = 0");
    assert_eq!(lines[2], "    x1 = 1");
    assert!(
        lines[3].contains("more lines") && lines[3].contains("--head"),
        "tail names the flag: {text:?}"
    );
}

#[test]
fn show_default_truncates_a_body_over_200_lines_with_a_tail() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut body = String::from("def solo():\n");
    for i in 0..205 {
        body.push_str(&format!("    x{i} = {i}\n"));
    }
    body.push_str("    return 1\n");
    write(root, "app.py", &body);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["show", "solo"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let lines: Vec<&str> = text.lines().collect();
    assert_eq!(
        lines.len(),
        201,
        "200 capped body lines + 1 truncation tail: got {}",
        lines.len()
    );
    assert_eq!(lines[0], "def solo():");
    assert!(
        lines[200].contains("more lines") && lines[200].contains("--head/Read"),
        "tail names --head/Read: {}",
        lines[200]
    );
}

#[test]
fn show_json_emits_path_start_line_end_line_and_exact_text() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "x = 1\n\n\ndef solo():\n    return 1\n\n\ny = 2\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["show", "solo", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();
    assert_eq!(v["path"], "app.py");
    assert_eq!(v["start_line"], 4);
    assert_eq!(v["end_line"], 5);
    assert_eq!(v["text"], "def solo():\n    return 1");
}
