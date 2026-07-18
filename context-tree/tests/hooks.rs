//! Integration tests for `ctx hooks install` / `ctx hooks uninstall` (R16).
//! Each spins up a throwaway git repo, exercises the installed hooks, and
//! asserts on the hook files, the C5 journal, and the partial-commit rule.

use std::path::Path;
use std::process::{Command, Output};
use std::time::{Duration, Instant};

fn ctx(root: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .output()
        .unwrap()
}

fn git(root: &Path, args: &[&str]) -> Output {
    Command::new("git")
        .current_dir(root)
        .args(args)
        .output()
        .unwrap()
}

fn git_init(root: &Path) {
    assert!(git(root, &["init", "-q"]).status.success());
    git(root, &["config", "user.email", "t@example.com"]);
    git(root, &["config", "user.name", "Tester"]);
    git(root, &["config", "commit.gpgsign", "false"]);
}

fn init(root: &Path) {
    assert!(ctx(root, &["init"]).status.success());
}

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

fn read(root: &Path, rel: &str) -> String {
    std::fs::read_to_string(root.join(rel)).unwrap()
}

/// The single note file `ctx notes add` wrote, as a repo-relative path.
fn note_file(root: &Path) -> String {
    let dir = root.join(".context/notes");
    let mut names: Vec<_> = std::fs::read_dir(&dir)
        .unwrap()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("md"))
        .collect();
    names.sort();
    let p = names.first().expect("a note file exists");
    format!(".context/notes/{}", p.file_name().unwrap().to_string_lossy())
}

/// The `anchor_path:` frontmatter value of a note file.
fn anchor_path(root: &Path, rel: &str) -> String {
    for line in read(root, rel).lines() {
        if let Some(v) = line.trim_start().strip_prefix("anchor_path:") {
            return v.trim().to_string();
        }
    }
    panic!("no anchor_path line in {rel}");
}

#[test]
fn hooks_install_preserves_existing() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def foo():\n    return 1\n");
    init(root);
    // A pre-existing, non-ctx post-checkout hook.
    write(root, ".git/hooks/post-checkout", "#!/bin/sh\necho existing-hook\n");

    let out = ctx(root, &["hooks", "install"]);
    assert!(out.status.success(), "install failed: {out:?}");

    let hook = read(root, ".git/hooks/post-checkout");
    assert!(
        hook.contains("echo existing-hook"),
        "pre-existing content lost:\n{hook}"
    );
    assert!(
        hook.contains("sync --hook"),
        "ctx pre-warm block not appended:\n{hook}"
    );
    assert!(hook.contains("managed"), "no managed marker:\n{hook}");
}

#[test]
fn hooks_checkout_triggers_sync() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def foo():\n    return 1\n");
    init(root);
    git(root, &["add", "-A"]);
    git(root, &["commit", "-qm", "base"]);

    assert!(ctx(root, &["hooks", "install"]).status.success());

    // A branch checkout fires post-checkout, which runs `ctx sync --hook`.
    assert!(git(root, &["checkout", "-q", "-b", "other"]).status.success());

    let journal = root.join(".context/cache/sync-journal.jsonl");
    let deadline = Instant::now() + Duration::from_secs(10);
    let mut saw_hook = false;
    while Instant::now() < deadline {
        if let Ok(text) = std::fs::read_to_string(&journal) {
            if text.lines().any(|l| l.contains("\"trigger\":\"hook\"")) {
                saw_hook = true;
                break;
            }
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    assert!(saw_hook, "no `trigger: hook` journal record within 10s");
}

#[test]
fn hooks_fsmonitor_reporting() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def foo():\n    return 1\n");
    init(root);

    let out = ctx(root, &["hooks", "install"]);
    assert!(out.status.success());
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains("fsmonitor"),
        "no fsmonitor line in output:\n{stdout}"
    );
    assert!(
        stdout.contains("enabled") || stdout.contains("skipped"),
        "fsmonitor decision not reported:\n{stdout}"
    );
}

#[test]
fn hooks_posttooluse_snippet() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def foo():\n    return 1\n");
    init(root);

    let out = ctx(root, &["hooks", "install"]);
    assert!(out.status.success());
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains("notes list --file"),
        "PostToolUse snippet missing `ctx notes list --file`:\n{stdout}"
    );
}

/// Build a repo with a note on `foo` in a.py, then move `foo` to b.py.
/// Returns (note rel path, the note's original anchor_path).
fn setup_moved_symbol(root: &Path) -> (String, String) {
    git_init(root);
    write(root, "a.py", "def foo():\n    return 41 + 1\n");
    init(root);
    assert!(ctx(root, &["notes", "add", "foo", "watch this symbol"]).status.success());
    git(root, &["add", "-A"]);
    git(root, &["commit", "-qm", "base"]);

    let note = note_file(root);
    let original = anchor_path(root, &note);

    assert!(ctx(root, &["hooks", "install"]).status.success());

    // Refactor: move `foo` from a.py to b.py (identical body — a pure move).
    write(root, "a.py", "def other():\n    return 0\n");
    write(root, "b.py", "def foo():\n    return 41 + 1\n");

    (note, original)
}

#[test]
fn hooks_precommit_partial_commit() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let (note, original) = setup_moved_symbol(root);

    // Stage only the moved-FROM file; b.py (moved-TO) stays unstaged.
    assert!(git(root, &["add", "a.py"]).status.success());
    assert!(git(root, &["commit", "-qm", "partial refactor"]).status.success());

    // b.py not staged -> the anchor update stays pending, note file unchanged.
    assert_eq!(
        anchor_path(root, &note),
        original,
        "anchor was written despite moved-TO file being unstaged"
    );
}

#[test]
fn hooks_precommit_full_commit() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let (note, original) = setup_moved_symbol(root);

    // Stage BOTH files: the moved-TO file b.py is now in the staged set.
    assert!(git(root, &["add", "a.py", "b.py"]).status.success());
    assert!(git(root, &["commit", "-qm", "full refactor"]).status.success());

    // b.py staged -> the anchor update is written to the note file...
    let updated = anchor_path(root, &note);
    assert_ne!(updated, original, "anchor update was not written");
    // ...and staged in the same commit (working tree clean vs HEAD for the note).
    let status = git(root, &["status", "--porcelain", &note]);
    let porcelain = String::from_utf8_lossy(&status.stdout);
    assert!(
        porcelain.trim().is_empty(),
        "note file not committed (still dirty): {porcelain:?}"
    );
}

#[test]
fn hooks_uninstall_restores_original() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def foo():\n    return 1\n");
    init(root);

    // A pre-existing post-checkout hook and a pre-existing fsmonitor setting.
    let original = "#!/bin/sh\necho keep-me\n";
    write(root, ".git/hooks/post-checkout", original);
    git(root, &["config", "core.fsmonitor", "true"]);

    assert!(ctx(root, &["hooks", "install"]).status.success());
    assert!(ctx(root, &["hooks", "uninstall"]).status.success());

    // The pre-existing hook is restored byte-for-byte.
    assert_eq!(
        read(root, ".git/hooks/post-checkout"),
        original,
        "pre-existing hook not restored exactly"
    );
    // A ctx-created hook file is deleted.
    assert!(
        !root.join(".git/hooks/pre-commit").exists(),
        "ctx-created pre-commit hook not removed"
    );
    // The pre-existing fsmonitor setting is left untouched.
    let cfg = git(root, &["config", "--get", "core.fsmonitor"]);
    assert_eq!(
        String::from_utf8_lossy(&cfg.stdout).trim(),
        "true",
        "pre-existing fsmonitor setting was reverted"
    );
}
