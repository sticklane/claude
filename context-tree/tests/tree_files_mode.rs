//! R2 integration tests for `ctx tree --files <path>` — a files-only listing
//! mode: one indexed file path per line (no symbol lines), a `--json` array of
//! paths, `--depth` counted as directory levels below the query path, and an
//! emitted count equal to the index's file membership under the path.

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

/// A fixture where file count ≠ symbol-mode tree line count: four files under
/// `proj/`, one carrying two top-level symbols, plus one and two levels of
/// nesting. Returns the root's tempdir (kept alive by the caller).
///
/// Directory-level depth (relative to `proj`, 1-based): a.py=1, b.py=1,
/// sub/c.py=2, sub/deep/d.py=3.
fn fixture() -> tempfile::TempDir {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "proj/a.py", "def fa():\n    return 1\n");
    // Two symbols in one file, so symbol-mode emits more lines than files.
    write(
        root,
        "proj/b.py",
        "def fb1():\n    return 1\n\n\ndef fb2():\n    return 2\n",
    );
    write(root, "proj/sub/c.py", "def fc():\n    return 3\n");
    write(root, "proj/sub/deep/d.py", "def fd():\n    return 4\n");
    sleep(PAST);
    init(root);
    dir
}

/// The four files created under `proj/`, sorted — the index's file membership.
const PROJ_FILES: [&str; 4] = [
    "proj/a.py",
    "proj/b.py",
    "proj/sub/c.py",
    "proj/sub/deep/d.py",
];

/// Non-empty, non-truncation lines of a command's stdout.
fn content_lines(text: &str) -> Vec<&str> {
    text.lines().filter(|l| !l.trim().is_empty()).collect()
}

#[test]
fn files_mode_emits_one_path_per_line_and_no_symbol_lines() {
    let dir = fixture();
    let root = dir.path();

    let out = ctx(root, &["tree", "proj", "--files"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let lines = content_lines(&text);

    // Every emitted line is one of the indexed file paths, and every file
    // appears — no symbol lines, no indentation.
    for f in PROJ_FILES {
        assert!(lines.contains(&f), "files mode emits {f}: {text:?}");
    }
    // No symbol names leak into files mode.
    for sym in ["fa", "fb1", "fb2", "fc", "fd"] {
        assert!(
            !text.contains(sym),
            "files mode emits no symbol names, but saw {sym}: {text:?}"
        );
    }
    // No indented (symbol) lines.
    assert!(
        lines.iter().all(|l| !l.starts_with(' ')),
        "files mode emits no indented symbol lines: {text:?}"
    );
}

#[test]
fn files_mode_count_equals_index_file_membership() {
    let dir = fixture();
    let root = dir.path();

    let files = ctx(root, &["tree", "proj", "--files"]);
    let files_text = stdout(&files);
    let files_lines = content_lines(&files_text);
    assert_eq!(
        files_lines.len(),
        PROJ_FILES.len(),
        "files-mode line count equals file membership under proj"
    );

    // Symbol-mode tree over the same path emits strictly more lines (file
    // headers + symbol lines), so file count ≠ tree line count today.
    let symbols = ctx(root, &["tree", "proj"]);
    let symbols_text = stdout(&symbols);
    let symbol_lines = content_lines(&symbols_text);
    assert!(
        symbol_lines.len() > files_lines.len(),
        "symbol-mode line count ({}) exceeds files-mode count ({})",
        symbol_lines.len(),
        files_lines.len()
    );
}

#[test]
fn files_mode_json_is_an_array_of_paths() {
    let dir = fixture();
    let root = dir.path();

    let out = ctx(root, &["tree", "proj", "--files", "--json"]);
    assert_eq!(out.status.code(), Some(0));
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();
    let arr = v.as_array().expect("files --json is a JSON array");
    let got: Vec<&str> = arr.iter().map(|e| e.as_str().unwrap()).collect();
    assert_eq!(
        got,
        PROJ_FILES.to_vec(),
        "files --json is the sorted array of indexed paths"
    );
}

#[test]
fn files_mode_depth_1_lists_only_files_directly_under_the_path() {
    let dir = fixture();
    let root = dir.path();

    let out = ctx(root, &["tree", "proj", "--files", "--depth", "1"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let lines = content_lines(&text);

    assert!(lines.contains(&"proj/a.py"), "depth 1 keeps proj/a.py");
    assert!(lines.contains(&"proj/b.py"), "depth 1 keeps proj/b.py");
    assert!(
        !lines.contains(&"proj/sub/c.py"),
        "depth 1 excludes the depth-2 proj/sub/c.py: {lines:?}"
    );
    assert!(
        !lines.contains(&"proj/sub/deep/d.py"),
        "depth 1 excludes the depth-3 proj/sub/deep/d.py: {lines:?}"
    );
    assert_eq!(lines.len(), 2, "exactly the two depth-1 files: {lines:?}");
}

#[test]
fn files_mode_depth_2_reaches_one_subdirectory_down() {
    let dir = fixture();
    let root = dir.path();

    let out = ctx(root, &["tree", "proj", "--files", "--depth", "2"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let lines = content_lines(&text);

    assert!(lines.contains(&"proj/a.py"), "depth 2 keeps proj/a.py");
    assert!(lines.contains(&"proj/b.py"), "depth 2 keeps proj/b.py");
    assert!(
        lines.contains(&"proj/sub/c.py"),
        "depth 2 reaches the depth-2 proj/sub/c.py: {lines:?}"
    );
    assert!(
        !lines.contains(&"proj/sub/deep/d.py"),
        "depth 2 still excludes the depth-3 proj/sub/deep/d.py: {lines:?}"
    );
    assert_eq!(lines.len(), 3, "exactly the three depth≤2 files: {lines:?}");
}

#[test]
fn default_symbol_mode_still_emits_symbol_lines_without_files_flag() {
    let dir = fixture();
    let root = dir.path();

    // Without --files, the mode is unchanged: symbol names appear, indented
    // under their file header.
    let out = ctx(root, &["tree", "proj"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    for sym in ["fa", "fb1", "fb2", "fc", "fd"] {
        assert!(text.contains(sym), "symbol mode names {sym}: {text:?}");
    }
    assert!(
        text.lines().any(|l| l.starts_with(' ')),
        "symbol mode still indents symbol lines: {text:?}"
    );
}
