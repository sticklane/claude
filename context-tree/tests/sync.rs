//! R2/R4/R5/C5/C6 sync-engine integration tests.

use context_tree::index::IndexStore;
use context_tree::sync::{self, journal::Trigger, lock::AdvisoryLock};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::process::Command;
use std::thread::sleep;
use std::time::{Duration, Instant};

/// Larger than the sync engine's racy-edit window (100 ms), so a fixture's
/// files sit safely outside it relative to a later sync's timestamp.
const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        fs::create_dir_all(parent).unwrap();
    }
    fs::write(p, content).unwrap();
}

fn store(root: &Path) -> IndexStore {
    IndexStore::open(&sync::cache_dir(root)).unwrap()
}

fn journal_lines(root: &Path) -> usize {
    fs::read_to_string(sync::cache_dir(root).join("sync-journal.jsonl"))
        .map(|t| t.lines().filter(|l| !l.trim().is_empty()).count())
        .unwrap_or(0)
}

const PY_A: &str = "import os\n\n\ndef a():\n    return os.getpid()\n";

#[test]
fn sync_incremental_reparses_only_changed_content() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", PY_A);
    write(root, "b.py", "def b():\n    return 2\n");
    sleep(PAST);

    let s0 = sync::run_sync(root, Trigger::Cli).unwrap();
    assert!(
        s0.parsed >= 2,
        "first sync indexes every source file: {s0:?}"
    );

    // Edit exactly one file's content.
    sleep(PAST);
    write(
        root,
        "a.py",
        "import os\n\n\ndef a():\n    return os.getppid()\n",
    );
    let s1 = sync::run_sync(root, Trigger::Cli).unwrap();
    assert_eq!(s1.parsed, 1, "only the edited file re-parses: {s1:?}");
    assert_eq!(s1.hashed, 1, "only the candidate file is hashed: {s1:?}");

    // Pure mtime bump: rewrite identical bytes.
    sleep(PAST);
    write(root, "b.py", "def b():\n    return 2\n");
    let s2 = sync::run_sync(root, Trigger::Cli).unwrap();
    assert_eq!(s2.parsed, 0, "a pure mtime bump does not re-parse: {s2:?}");
}

fn ctx_bin(root: &Path, args: &[&str]) -> String {
    let out = Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .output()
        .unwrap();
    assert!(out.status.success(), "ctx {args:?} failed: {out:?}");
    String::from_utf8(out.stdout).unwrap()
}

fn parse_stats(line: &str) -> HashMap<String, usize> {
    line.split_whitespace()
        .filter_map(|tok| tok.split_once('='))
        .map(|(k, v)| (k.to_string(), v.trim().parse().unwrap()))
        .collect()
}

#[test]
fn sync_incremental_cli_stats_reports_parsed_and_hashed() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    write(root, "b.py", "def b():\n    return 2\n");
    sleep(PAST);
    ctx_bin(root, &["sync"]);

    sleep(PAST);
    write(root, "a.py", "def a():\n    return 99\n");
    let out = ctx_bin(root, &["sync", "--stats"]);
    let stats = parse_stats(out.trim());
    assert_eq!(stats.get("parsed"), Some(&1), "stats: {out:?}");
    assert_eq!(stats.get("hashed"), Some(&1), "stats: {out:?}");
}

#[test]
fn sync_deletion_purges_removed_file_facts() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "gone.py", "def gone():\n    return 1\n");
    write(root, "keep.py", "def keep():\n    return 2\n");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();
    assert!(store(root).symbol_count_for_path("gone.py").unwrap() >= 1);

    fs::remove_file(root.join("gone.py")).unwrap();
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    assert_eq!(
        store(root).symbol_count_for_path("gone.py").unwrap(),
        0,
        "a removed file's facts are purged"
    );
    assert!(
        store(root).symbol_count_for_path("keep.py").unwrap() >= 1,
        "a surviving file is kept"
    );
    assert!(
        !store(root)
            .indexed_paths()
            .unwrap()
            .contains(&"gone.py".to_string())
    );
}

#[test]
fn sync_journal_appends_one_c5_record_per_sync() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();
    sleep(PAST);
    write(root, "a.py", "def a():\n    return 2\n");
    sync::run_sync(root, Trigger::Cli).unwrap();

    let text = fs::read_to_string(sync::cache_dir(root).join("sync-journal.jsonl")).unwrap();
    let lines: Vec<&str> = text.lines().filter(|l| !l.trim().is_empty()).collect();
    assert_eq!(lines.len(), 2, "one record per sync");
    for line in &lines {
        let v: serde_json::Value = serde_json::from_str(line).unwrap();
        assert!(
            v["timestamp"].as_str().unwrap().ends_with('Z'),
            "UTC timestamp: {line}"
        );
        assert_eq!(v["trigger"].as_str(), Some("cli"));
        assert!(v["scanned"].as_u64().is_some());
        assert!(v["hashed"].as_u64().is_some());
        assert!(v["parsed"].as_u64().is_some());
        assert_eq!(v["pending_reanchors"].as_u64(), Some(0));
    }
}

#[test]
fn sync_references_imports_persisted_without_duplication() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", PY_A);
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    let imports = store(root).imports_count_for_path("a.py").unwrap();
    let references = store(root).references_count_for_path("a.py").unwrap();
    assert!(imports >= 1, "an Import fact is queryable after sync");
    assert!(references >= 1, "a Reference fact is queryable after sync");

    // Force a re-parse that leaves the import set unchanged.
    sleep(PAST);
    write(
        root,
        "a.py",
        "import os\n\n\ndef a():\n    x = 1\n    return os.getpid()\n",
    );
    let s = sync::run_sync(root, Trigger::Cli).unwrap();
    assert_eq!(s.parsed, 1, "the edit re-parses the file");
    assert_eq!(
        store(root).imports_count_for_path("a.py").unwrap(),
        imports,
        "a re-parse replaces rows rather than accumulating them"
    );
}

#[test]
fn sync_concurrency_query_skips_sweep_under_held_lock() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", PY_A);
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    // A concurrent sync holds the advisory lock.
    let held = AdvisoryLock::try_acquire(&sync::cache_dir(root))
        .unwrap()
        .expect("lock free before the test acquires it");
    let before = journal_lines(root);

    let t = Instant::now();
    let snapshot = sync::query_sweep(root).unwrap();
    let elapsed = t.elapsed();

    assert!(
        elapsed < Duration::from_millis(500),
        "the query returns bounded under a held lock: {elapsed:?}"
    );
    assert_eq!(
        journal_lines(root),
        before,
        "no new journal record while a sync holds the lock"
    );
    assert!(
        snapshot.total_symbols().unwrap() >= 1,
        "the last-completed snapshot is served"
    );
    drop(held);
}

#[test]
fn ignore_rules_exclude_gitignored_and_context_cache() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    assert!(
        Command::new("git")
            .current_dir(root)
            .arg("init")
            .status()
            .unwrap()
            .success()
    );
    write(root, ".gitignore", "ignored.py\n");
    write(root, "ignored.py", "def ignored():\n    return 1\n");
    write(root, "kept.py", "def kept():\n    return 2\n");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    let st = store(root);
    assert_eq!(
        st.symbol_count_for_path("ignored.py").unwrap(),
        0,
        "a .gitignore-matched file is excluded from the index"
    );
    assert!(st.symbol_count_for_path("kept.py").unwrap() >= 1);
    assert!(
        st.indexed_paths()
            .unwrap()
            .iter()
            .all(|p| !p.starts_with(".context/")),
        ".context/cache is never indexed even without an ignore entry"
    );
}

#[test]
fn ignore_rules_ctxignore_excludes_in_baseline() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, ".ctxignore", "secret.py\n");
    write(root, "secret.py", "def secret():\n    return 1\n");
    write(root, "open.py", "def open_():\n    return 2\n");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    let st = store(root);
    assert_eq!(
        st.symbol_count_for_path("secret.py").unwrap(),
        0,
        "a .ctxignore-matched file is excluded in the no-VCS baseline"
    );
    assert!(st.symbol_count_for_path("open.py").unwrap() >= 1);
}

#[test]
fn no_vcs_baseline_builds_and_syncs_without_git() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    assert!(!root.join(".git").exists());
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);

    let s0 = sync::run_sync(root, Trigger::Cli).unwrap();
    assert!(s0.parsed >= 1, "the baseline indexes a plain directory");
    assert!(store(root).total_symbols().unwrap() >= 1);

    // A second sync over an unchanged tree re-parses nothing.
    let s1 = sync::run_sync(root, Trigger::Cli).unwrap();
    assert_eq!(s1.parsed, 0, "an unchanged tree re-parses nothing");
}
