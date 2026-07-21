//! `.ctxignore` exclusion-overlay integration tests (spec
//! `ctxignore-git-overlay`, R1–R5). Under git, `.ctxignore` becomes a
//! VCS-independent subtractive overlay over the git adapter; the no-VCS
//! baseline keeps its built-in `.ctxignore` handling and is never
//! double-wrapped.

use context_tree::index::IndexStore;
use context_tree::sync::{self, journal::Trigger};
use context_tree::vcs::{self, NoVcsBaseline, VcsAdapter};
use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms), so fixture files
/// sit safely outside it relative to a later sync's timestamp.
const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

fn store(root: &Path) -> IndexStore {
    IndexStore::open(&sync::cache_dir(root)).unwrap()
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

fn stderr(out: &Output) -> String {
    String::from_utf8(out.stderr.clone()).unwrap()
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

fn git_commit_all(root: &Path, msg: &str) {
    assert!(git(root, &["add", "-A"]).status.success());
    assert!(git(root, &["commit", "-qm", msg]).status.success());
}

/// The single note file's text (asserts exactly one exists).
fn only_note(root: &Path) -> String {
    let dir = root.join(".context/notes");
    let mut files: Vec<_> = std::fs::read_dir(&dir)
        .unwrap()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("md"))
        .collect();
    files.sort();
    assert_eq!(
        files.len(),
        1,
        "expected exactly one note file, got {files:?}"
    );
    std::fs::read_to_string(&files[0]).unwrap()
}

fn frontmatter_field(note: &str, key: &str) -> Option<String> {
    let body = note.strip_prefix("---\n")?;
    let end = body.find("\n---")?;
    for line in body[..end].lines() {
        if let Some(rest) = line.strip_prefix(&format!("{key}:")) {
            return Some(rest.trim().to_string());
        }
    }
    None
}

// ---------------------------------------------------------------------------
// R1 — overlay subtracts committed-but-derived paths under git.
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_excludes_committed_paths_under_git() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    // A committed dist/ twin of a src/ symbol, byte-identical.
    write(root, "src/lib.py", "def shared():\n    return 1\n");
    write(root, "dist/lib.py", "def shared():\n    return 1\n");
    write(root, ".ctxignore", "dist/\n");
    git_commit_all(root, "src + committed dist twin");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    let st = store(root);
    assert!(
        st.symbol_count_for_path("src/lib.py").unwrap() >= 1,
        "the src/ copy is indexed"
    );
    assert_eq!(
        st.symbol_count_for_path("dist/lib.py").unwrap(),
        0,
        "the committed dist/ twin is excluded by the overlay"
    );
    assert!(
        !st.indexed_paths()
            .unwrap()
            .contains(&"dist/lib.py".to_string()),
        "dist/lib.py is not in the indexed set"
    );

    // refs on a symbol defined in both trees returns only the src/ def.
    let refs = ctx(root, &["refs", "shared"]);
    assert_eq!(
        refs.status.code(),
        Some(0),
        "refs exits 0: {}",
        stderr(&refs)
    );
    let text = stdout(&refs);
    assert!(
        text.lines()
            .any(|l| l.starts_with("def") && l.contains("shared")),
        "the src/ definition is listed: {text}"
    );
    assert!(
        !text.contains("dist"),
        "no dist/ definition or reference is surfaced: {text}"
    );
}

// ---------------------------------------------------------------------------
// R2 — subtractive only: a .ctxignore entry cannot re-include a gitignored file.
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_cannot_reinclude_gitignored() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, ".gitignore", "hidden.py\n");
    write(root, "hidden.py", "def hidden():\n    return 1\n");
    write(root, "visible.py", "def visible():\n    return 2\n");
    // A negation entry is NOT honored — the matcher has no `!` syntax, and the
    // overlay can only subtract, never add.
    write(root, ".ctxignore", "!hidden.py\n");
    git_commit_all(root, "gitignored hidden + visible");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    let st = store(root);
    assert_eq!(
        st.symbol_count_for_path("hidden.py").unwrap(),
        0,
        "a git-ignored file stays excluded; .ctxignore cannot resurrect it"
    );
    assert!(
        st.symbol_count_for_path("visible.py").unwrap() >= 1,
        "a non-ignored file is still indexed"
    );
}

// ---------------------------------------------------------------------------
// R4 — editing .ctxignore takes effect on the next query's sweep, both ways.
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_edit_takes_effect_on_next_query() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "src/keep.py", "def keep():\n    return 1\n");
    write(root, "gen/derived.py", "def derived():\n    return 2\n");
    git_commit_all(root, "src + committed generated tree");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();
    assert!(
        store(root).symbol_count_for_path("gen/derived.py").unwrap() >= 1,
        "derived symbol is indexed before any overlay entry"
    );

    // Add an entry -> symbol gone on the next sweep.
    write(root, ".ctxignore", "gen/\n");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();
    assert_eq!(
        store(root).symbol_count_for_path("gen/derived.py").unwrap(),
        0,
        "adding the overlay entry excludes the file on the next query"
    );

    // Remove the entry -> symbol re-indexed on the next sweep.
    std::fs::remove_file(root.join(".ctxignore")).unwrap();
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();
    assert!(
        store(root).symbol_count_for_path("gen/derived.py").unwrap() >= 1,
        "removing the entry re-indexes the path on the next query"
    );
}

// ---------------------------------------------------------------------------
// R5 — a repo with no .ctxignore behaves as today.
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_absent_file_changes_nothing() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def a():\n    return 1\n");
    write(root, "b.py", "def b():\n    return 2\n");
    git_commit_all(root, "no .ctxignore present");
    sleep(PAST);
    sync::run_sync(root, Trigger::Cli).unwrap();

    let st = store(root);
    assert!(
        st.symbol_count_for_path("a.py").unwrap() >= 1,
        "a.py indexed"
    );
    assert!(
        st.symbol_count_for_path("b.py").unwrap() >= 1,
        "b.py indexed"
    );
    let paths = st.indexed_paths().unwrap();
    assert!(paths.contains(&"a.py".to_string()));
    assert!(paths.contains(&"b.py".to_string()));
}

// ---------------------------------------------------------------------------
// R3 — the baseline is returned unwrapped: its file list is byte-identical to a
// direct NoVcsBaseline call (double-subtraction never introduced).
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_baseline_list_unchanged() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    // No git: detect() selects the no-VCS baseline.
    write(root, ".ctxignore", "secret.py\n");
    write(root, "secret.py", "def secret():\n    return 1\n");
    write(root, "open.py", "def open_():\n    return 2\n");

    let via_detect = vcs::detect(root).list_files(root).unwrap();
    assert!(
        !via_detect.contains(&"secret.py".to_string()),
        "the baseline still subtracts .ctxignore: {via_detect:?}"
    );
    assert!(via_detect.contains(&"open.py".to_string()));

    let via_baseline = NoVcsBaseline.list_files(root).unwrap();
    assert_eq!(
        via_detect, via_baseline,
        "detect()'s baseline list is byte-identical to a direct NoVcsBaseline list"
    );
}

// ---------------------------------------------------------------------------
// R4 — a note anchored in a newly excluded file goes stale (unresolved), is not
// re-anchored elsewhere, and resolves again when the entry is removed.
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_note_goes_stale_not_reanchored() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    // A UNIQUE symbol with no byte-identical twin anywhere, so the re-anchor
    // body-hash layer finds no candidate once the file leaves the index.
    write(
        root,
        "vendor/thing.py",
        "def unique_vendored():\n    return 41\n",
    );
    write(root, "keep.py", "def keep():\n    return 2\n");
    git_commit_all(root, "committed vendored tree");
    sleep(PAST);
    assert!(ctx(root, &["init"]).status.success());

    assert!(
        ctx(root, &["notes", "add", "unique_vendored", "a gotcha"])
            .status
            .success()
    );
    let anchor = frontmatter_field(&only_note(root), "anchor_path").unwrap();
    assert!(
        !stdout(&ctx(root, &["notes", "list", "--stale"])).contains(&anchor),
        "the note resolves (is fresh) before any overlay entry"
    );

    // Exclude the vendored tree -> its symbol leaves the index on the next sweep.
    write(root, ".ctxignore", "vendor/\n");
    sleep(PAST);
    assert!(ctx(root, &["sync"]).status.success());

    let staled = stdout(&ctx(root, &["notes", "list", "--stale"]));
    assert!(
        staled.contains(&anchor),
        "the note reads stale once its file is overlay-excluded: {staled}"
    );
    assert_eq!(
        frontmatter_field(&only_note(root), "anchor_path").as_deref(),
        Some(anchor.as_str()),
        "the note is not re-anchored to any other symbol"
    );

    // Un-ignore the path -> the symbol returns and the note resolves again.
    std::fs::remove_file(root.join(".ctxignore")).unwrap();
    sleep(PAST);
    assert!(ctx(root, &["sync"]).status.success());
    assert!(
        !stdout(&ctx(root, &["notes", "list", "--stale"])).contains(&anchor),
        "removing the entry restores note resolution"
    );
}

// ---------------------------------------------------------------------------
// R3 delegation — the wrapper's user_identity reaches the inner git adapter, so
// a note records the git committer email as author (not the trait default).
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_git_note_author_preserved() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", "def target():\n    return 1\n");
    write(root, ".ctxignore", "dist/\n");
    git_commit_all(root, "source with a .ctxignore present");
    sleep(PAST);
    assert!(ctx(root, &["init"]).status.success());

    assert!(
        ctx(root, &["notes", "add", "target", "body"])
            .status
            .success()
    );
    assert_eq!(
        frontmatter_field(&only_note(root), "author").as_deref(),
        Some("t@example.com"),
        "the note author is the git committer email, via delegated user_identity"
    );
}

// ---------------------------------------------------------------------------
// R1 — the composed is_ignored (not just the file list) applies the overlay:
// `ctx at` on a committed-but-excluded file exits 4.
// ---------------------------------------------------------------------------

#[test]
fn ctxignore_overlay_at_excluded_file_exits_4() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "src/app.py", "def a():\n    return 1\n");
    write(root, "dist/app.py", "def a():\n    return 1\n");
    write(root, ".ctxignore", "dist/\n");
    git_commit_all(root, "src + committed dist twin");
    sleep(PAST);
    assert!(ctx(root, &["init"]).status.success());

    let out = ctx(root, &["at", "dist/app.py:1"]);
    assert_eq!(
        out.status.code(),
        Some(4),
        "an overlay-excluded committed file exits 4"
    );
    let reason = format!("{}{}", stdout(&out), stderr(&out));
    assert!(
        reason.to_lowercase().contains("ignore"),
        "the reason names the ignore: {reason}"
    );
}
