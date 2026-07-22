//! R1 minified-detection tests: the classifier's boundary behavior (unit
//! tests, run via `cargo test minified`) and a sync-level integration check
//! that a synced `*.min.js` fixture is recorded skipped and yields zero
//! symbols (run via `cargo test --test minified`).

use context_tree::index::IndexStore;
use context_tree::minified::{self, MinifiedReason};
use context_tree::sync::{self, journal::Trigger};
use std::fs;
use std::path::Path;
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms).
const PAST: Duration = Duration::from_millis(250);

const SIZE_THRESHOLD: usize = 50 * 1024;

fn write(root: &Path, rel: &str, content: &[u8]) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        fs::create_dir_all(parent).unwrap();
    }
    fs::write(p, content).unwrap();
}

// --- Name-pattern classification -------------------------------------------

#[test]
fn minified_classify_flags_dot_min_js_by_name() {
    assert_eq!(
        minified::classify("vendor/paper-full.min.js", b"x"),
        Some(MinifiedReason::Name)
    );
}

#[test]
fn minified_classify_flags_dot_min_mjs_by_name() {
    assert_eq!(
        minified::classify("vendor/bundle.min.mjs", b"x"),
        Some(MinifiedReason::Name)
    );
}

#[test]
fn minified_classify_does_not_flag_plain_js_by_name() {
    assert_eq!(minified::classify("src/app.js", b"const x = 1;"), None);
}

// --- Content heuristic: average line length ---------------------------------

fn one_long_line(bytes: usize) -> Vec<u8> {
    vec![b'x'; bytes]
}

#[test]
fn minified_classify_flags_large_file_with_long_average_lines() {
    // > 50 KB, single line (avg line length == file size, way over 400).
    let content = one_long_line(SIZE_THRESHOLD + 1024);
    assert_eq!(
        minified::classify("bundle.js", &content),
        Some(MinifiedReason::Content)
    );
}

#[test]
fn minified_classify_does_not_flag_just_under_size_threshold() {
    // Boundary: exactly at/just under 50 KB never classifies as minified,
    // no matter the line shape (false-negative-favoring).
    let content = one_long_line(SIZE_THRESHOLD);
    assert_eq!(minified::classify("bundle.js", &content), None);
}

#[test]
fn minified_classify_does_not_flag_avg_line_length_at_400_boundary() {
    // > 50 KB but built from many lines of exactly 400 bytes each (avg ==
    // 400, not > 400) and line count is well above the short-file guard.
    let line = vec![b'x'; 400];
    let mut content = Vec::new();
    for _ in 0..150 {
        content.extend_from_slice(&line);
        content.push(b'\n');
    }
    assert!(content.len() > SIZE_THRESHOLD);
    assert_eq!(minified::classify("bundle.js", &content), None);
}

// --- Content heuristic: short file, one dominant line -----------------------

#[test]
fn minified_classify_flags_short_file_with_one_dominant_line() {
    // > 50 KB, <= 5 lines, one line holds > 50% of the bytes.
    let mut content = one_long_line(SIZE_THRESHOLD + 1024);
    content.push(b'\n');
    content.extend_from_slice(b"a();\nb();\n");
    assert_eq!(
        minified::classify("bundle.js", &content),
        Some(MinifiedReason::Content)
    );
}

#[test]
fn minified_classify_does_not_flag_six_line_file_with_dominant_line() {
    // Same dominant-line shape, but 6 lines (over the <=5 short-file guard)
    // and unremarkable average line length — must NOT classify as minified.
    // This is exactly the "one giant embedded literal amid ordinary code"
    // shape the guard exists to exempt.
    let mut content = one_long_line(SIZE_THRESHOLD + 1024);
    for _ in 0..5 {
        content.push(b'\n');
        content.extend_from_slice(b"ordinary_code_here();");
    }
    // 6 lines total (5 newlines).
    assert_eq!(content.split(|&b| b == b'\n').count(), 6);
    assert_eq!(minified::classify("bundle.js", &content), None);
}

// --- R3 false-positive guards -----------------------------------------------

#[test]
fn minified_classify_does_not_flag_normal_large_file_with_ordinary_lines() {
    // > 50 KB of ordinary source: 4000 lines of ~30 bytes each.
    let mut content = Vec::new();
    for i in 0..4000 {
        content.extend_from_slice(format!("let variable_{i} = {i};").as_bytes());
        content.push(b'\n');
    }
    assert!(content.len() > SIZE_THRESHOLD);
    assert_eq!(minified::classify("normal.js", &content), None);
}

#[test]
fn minified_classify_does_not_flag_many_ordinary_lines_with_one_embedded_literal() {
    // A normal source file with many ordinary lines plus one embedded
    // >50%-of-bytes literal line (e.g. a base64 blob) — the exact
    // false-positive shape the <=5-line guard on the dominant-line
    // criterion exists to exempt (R3 in specs/ctx-minified-skip/SPEC.md).
    let mut content = Vec::new();
    for i in 0..1000 {
        content.extend_from_slice(format!("const v{i} = {i};").as_bytes());
        content.push(b'\n');
    }
    let literal = vec![b'Q'; 40_000];
    content.extend_from_slice(&literal);
    content.push(b'\n');
    assert!(content.len() > SIZE_THRESHOLD);
    assert!(literal.len() as f64 > content.len() as f64 * 0.5);
    assert_eq!(minified::classify("embedded-literal.js", &content), None);
}

// --- sourceMappingURL: strengthens but never suffices alone -----------------

#[test]
fn minified_classify_does_not_flag_sourcemap_comment_alone() {
    let content = b"function a() { return 1; }\n//# sourceMappingURL=a.js.map\n";
    assert_eq!(minified::classify("small.js", content), None);
}

// --- Sync-level integration: a synced *.min.js yields zero symbols ---------

#[test]
fn sync_records_skip_reason_and_yields_zero_symbols_for_min_js() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "vendor/paper-full.min.js",
        b"function a(b){return b+1}function c(d){return d*2}",
    );
    write(root, "src/app.js", b"function real() { return 1; }\n");
    sleep(PAST);

    sync::run_sync(root, Trigger::Cli).unwrap();

    let store = IndexStore::open(&sync::cache_dir(root)).unwrap();
    assert_eq!(
        store
            .symbol_count_for_path("vendor/paper-full.min.js")
            .unwrap(),
        0,
        "a minified file yields zero symbols"
    );
    assert!(
        store.symbol_count_for_path("src/app.js").unwrap() > 0,
        "a normal source file still parses"
    );
    assert_eq!(
        store
            .skip_reason_for_path("vendor/paper-full.min.js")
            .unwrap(),
        Some("minified-name".to_string())
    );
    assert_eq!(
        store.skip_reason_for_path("src/app.js").unwrap(),
        None,
        "a normally-parsed file carries no skip reason"
    );
}
