//! R2 integration tests: `ctx tree <dir>` lists minified-skipped CANDIDATES
//! with a `(skipped: minified)` marker — a new file-level output class — while
//! symbol-bearing files render as today and non-candidate files (.md) stay
//! omitted. A regression test asserts `map`/`refs`/`sig` surface none of a
//! skipped file's symbols (already true once the file is skipped at index
//! time; this pins it).

use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms).
const PAST: Duration = Duration::from_millis(250);

/// A distinctive name that only appears inside the skipped `*.min.js` fixture,
/// so any query returning it would prove the skipped file was parsed.
const SKIPPED_SYMBOL: &str = "zzzMinifiedOnlyFn";

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

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

/// A fixture dir with one skipped `*.min.js` (classified minified by name),
/// one symbol-bearing `.rs`, and one non-candidate `.md`.
fn fixture() -> tempfile::TempDir {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "proj/vendor.min.js",
        &format!("function {SKIPPED_SYMBOL}(a){{return a+1}}"),
    );
    write(
        root,
        "proj/lib.rs",
        "pub fn real_symbol() -> i32 {\n    1\n}\n",
    );
    write(
        root,
        "proj/README.md",
        "# Notes\n\nplain prose, no symbols\n",
    );
    sleep(PAST);
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
    dir
}

#[test]
fn tree_lists_skipped_min_js_with_marker() {
    let dir = fixture();
    let text = stdout(&ctx(dir.path(), &["tree", "proj"]));

    // The skipped candidate appears as its own file-level line carrying the
    // marker — a skip must never read as absence.
    let marked = text
        .lines()
        .find(|l| l.contains("proj/vendor.min.js"))
        .unwrap_or_else(|| panic!("skipped min.js listed in tree: {text:?}"));
    assert!(
        marked.contains("(skipped: minified)"),
        "min.js line carries the marker: {marked:?}"
    );
}

#[test]
fn tree_still_renders_symbol_bearing_file() {
    let dir = fixture();
    let text = stdout(&ctx(dir.path(), &["tree", "proj"]));

    assert!(text.contains("proj/lib.rs"), "lib.rs listed: {text:?}");
    assert!(
        text.contains("real_symbol"),
        "lib.rs symbol still rendered: {text:?}"
    );
}

#[test]
fn tree_omits_non_candidate_markdown_file() {
    let dir = fixture();
    let text = stdout(&ctx(dir.path(), &["tree", "proj"]));

    assert!(
        !text.contains("README.md"),
        "non-candidate .md stays unlisted: {text:?}"
    );
}

#[test]
fn tree_never_lists_a_skipped_files_symbol() {
    let dir = fixture();
    let text = stdout(&ctx(dir.path(), &["tree", "proj"]));

    assert!(
        !text.contains(SKIPPED_SYMBOL),
        "skipped file's symbol never rendered as a symbol line: {text:?}"
    );
}

#[test]
fn tree_json_reports_skipped_candidate() {
    let dir = fixture();
    let out = ctx(dir.path(), &["tree", "proj", "--json"]);
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();
    let skipped = v
        .get("skipped")
        .and_then(|s| s.as_array())
        .expect("tree --json carries a skipped array");
    assert!(
        skipped
            .iter()
            .any(|e| e.get("path").and_then(|p| p.as_str()) == Some("proj/vendor.min.js")),
        "skipped array names the min.js: {skipped:?}"
    );
}

#[test]
fn map_refs_sig_return_none_of_a_skipped_files_symbols() {
    let dir = fixture();
    let root = dir.path();

    // map lists ranked symbols — the skipped file contributes none.
    let map = stdout(&ctx(root, &["map"]));
    assert!(
        !map.contains(SKIPPED_SYMBOL),
        "map omits the skipped file's symbols: {map:?}"
    );
    assert!(
        map.contains("real_symbol"),
        "map still ranks the parsed file's symbol: {map:?}"
    );

    // sig / refs resolve by symbol name — a skipped file's symbol is unknown,
    // so both fail to match (non-zero exit) and never print the name.
    let sig = ctx(root, &["sig", SKIPPED_SYMBOL]);
    assert_ne!(sig.status.code(), Some(0), "sig finds no skipped symbol");
    assert!(!stdout(&sig).contains(SKIPPED_SYMBOL));

    let refs = ctx(root, &["refs", SKIPPED_SYMBOL]);
    assert_ne!(refs.status.code(), Some(0), "refs finds no skipped symbol");
    assert!(!stdout(&refs).contains(SKIPPED_SYMBOL));
}
