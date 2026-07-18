//! R12/R14 + C1/C2/C3/C9/C10 notes-CRUD and derived-freshness integration
//! tests for `ctx notes add`, `ctx notes <symbol>`, and `ctx notes list`, plus
//! the C10 marker on all four query surfaces and the R2 deletion-freshness half.

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

fn ctx_env(root: &Path, args: &[&str], key: &str, val: &str) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .env(key, val)
        .output()
        .unwrap()
}

fn ctx_stdin(root: &Path, args: &[&str], input: &str) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(input.as_bytes())
        .unwrap();
    child.wait_with_output().unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

fn stderr(out: &Output) -> String {
    String::from_utf8(out.stderr.clone()).unwrap()
}

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

/// Every `*.md` under `.context/notes/`.
fn note_files(root: &Path) -> Vec<PathBuf> {
    let dir = root.join(".context/notes");
    let mut out = Vec::new();
    if let Ok(rd) = std::fs::read_dir(&dir) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) == Some("md") {
                out.push(p);
            }
        }
    }
    out.sort();
    out
}

/// Read the single note file's text (asserts exactly one exists).
fn only_note(root: &Path) -> String {
    let files = note_files(root);
    assert_eq!(
        files.len(),
        1,
        "expected exactly one note file, got {files:?}"
    );
    std::fs::read_to_string(&files[0]).unwrap()
}

/// Parse a `key: value` line out of a note's YAML frontmatter.
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

const TARGET_PY: &str = "def target():\n    return 1\n";

// ----------------------------------------------------------------------------
// notes_add — frontmatter fields, C9 author resolution, C3 ambiguous refusal
// ----------------------------------------------------------------------------

#[test]
fn notes_add_writes_frontmatter_and_body() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["notes", "add", "target", "a gotcha body"]);
    assert!(out.status.success(), "add failed: {}", stderr(&out));

    let note = only_note(root);
    assert!(
        frontmatter_field(&note, "id").is_some(),
        "missing id: {note}"
    );
    assert_eq!(
        frontmatter_field(&note, "anchor_path").as_deref(),
        Some("a.target")
    );
    let hash = frontmatter_field(&note, "anchor_hash").unwrap();
    assert!(!hash.is_empty(), "anchor_hash empty");
    assert!(note.contains("a gotcha body"), "body missing: {note}");
    assert!(
        frontmatter_field(&note, "created").is_some(),
        "missing created"
    );
}

#[test]
fn notes_add_records_kind() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    let out = ctx(
        root,
        &["notes", "add", "target", "b", "--kind", "invariant"],
    );
    assert!(out.status.success(), "add failed: {}", stderr(&out));
    assert_eq!(
        frontmatter_field(&only_note(root), "kind").as_deref(),
        Some("invariant")
    );
}

#[test]
fn notes_add_author_from_ctx_author_env() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    let out = ctx_env(
        root,
        &["notes", "add", "target", "b"],
        "CTX_AUTHOR",
        "alice",
    );
    assert!(out.status.success(), "add failed: {}", stderr(&out));
    assert_eq!(
        frontmatter_field(&only_note(root), "author").as_deref(),
        Some("alice")
    );
}

#[test]
fn notes_add_author_unknown_in_no_vcs_fixture() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    // No git, CTX_AUTHOR explicitly cleared -> author: unknown (C9).
    let out = Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(["notes", "add", "target", "b"])
        .env_remove("CTX_AUTHOR")
        .output()
        .unwrap();
    assert!(out.status.success(), "add failed: {}", stderr(&out));
    assert_eq!(
        frontmatter_field(&only_note(root), "author").as_deref(),
        Some("unknown")
    );
}

#[test]
fn notes_add_refuses_ambiguous_anchor_exit3() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def Handler():\n    return 1\n");
    write(root, "b.py", "def Handler():\n    return 2\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["notes", "add", "Handler", "body"]);
    assert_eq!(out.status.code(), Some(3), "ambiguous add exits 3: {out:?}");
    assert!(
        stdout(&out).contains("a.Handler") && stdout(&out).contains("b.Handler"),
        "candidate list printed: {}",
        stdout(&out)
    );
    assert!(note_files(root).is_empty(), "no note written on refusal");
}

// ----------------------------------------------------------------------------
// notes_body_sources — positional, --file, stdin (--file -)
// ----------------------------------------------------------------------------

#[test]
fn notes_body_sources_positional_file_and_stdin() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    // positional
    assert!(
        ctx(root, &["notes", "add", "target", "positional body"])
            .status
            .success()
    );
    // --file
    write(root, "body.md", "file-sourced body\n");
    assert!(
        ctx(root, &["notes", "add", "target", "--file", "body.md"])
            .status
            .success()
    );
    // stdin via --file -
    assert!(
        ctx_stdin(
            root,
            &["notes", "add", "target", "--file", "-"],
            "stdin-sourced body"
        )
        .status
        .success()
    );

    let bodies: Vec<String> = note_files(root)
        .iter()
        .map(|p| std::fs::read_to_string(p).unwrap())
        .collect();
    assert!(
        bodies.iter().any(|b| b.contains("positional body")),
        "positional"
    );
    assert!(
        bodies.iter().any(|b| b.contains("file-sourced body")),
        "file"
    );
    assert!(
        bodies.iter().any(|b| b.contains("stdin-sourced body")),
        "stdin"
    );
}

// ----------------------------------------------------------------------------
// notes_freshness — fresh iff anchor resolves and body hash matches
// ----------------------------------------------------------------------------

#[test]
fn notes_freshness_flips_stale_on_body_edit() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    assert!(
        ctx(root, &["notes", "add", "target", "note body"])
            .status
            .success()
    );

    let fresh = ctx(root, &["notes", "target"]);
    assert!(fresh.status.success(), "show failed: {}", stderr(&fresh));
    assert!(
        stdout(&fresh).contains("fresh"),
        "fresh before edit: {}",
        stdout(&fresh)
    );

    // Edit the anchored body -> C2 hash changes -> derived stale.
    write(root, "a.py", "def target():\n    return 2\n");
    sleep(PAST);

    let stale = ctx(root, &["notes", "target"]);
    assert!(stale.status.success());
    assert!(
        stdout(&stale).contains("stale"),
        "stale after edit: {}",
        stdout(&stale)
    );
}

// ----------------------------------------------------------------------------
// notes_list — --kind, --stale, --file filters
// ----------------------------------------------------------------------------

#[test]
fn notes_list_filters_by_kind_stale_and_file() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    write(root, "b.py", "def other():\n    return 9\n");
    sleep(PAST);
    init(root);

    assert!(
        ctx(root, &["notes", "add", "target", "n1", "--kind", "gotcha"])
            .status
            .success()
    );
    assert!(
        ctx(root, &["notes", "add", "other", "n2", "--kind", "todo"])
            .status
            .success()
    );

    // --kind gotcha returns only the target note.
    let by_kind = ctx(root, &["notes", "list", "--kind", "gotcha"]);
    assert!(by_kind.status.success());
    assert!(
        stdout(&by_kind).contains("a.target"),
        "kind filter keeps target"
    );
    assert!(
        !stdout(&by_kind).contains("b.other"),
        "kind filter drops other"
    );

    // --file b.py returns only the other note.
    let by_file = ctx(root, &["notes", "list", "--file", "b.py"]);
    assert!(by_file.status.success());
    assert!(
        stdout(&by_file).contains("b.other"),
        "file filter keeps other"
    );
    assert!(
        !stdout(&by_file).contains("a.target"),
        "file filter drops target"
    );

    // Make target's note stale, then --stale returns only it.
    write(root, "a.py", "def target():\n    return 5\n");
    sleep(PAST);
    let stale = ctx(root, &["notes", "list", "--stale"]);
    assert!(stale.status.success());
    assert!(
        stdout(&stale).contains("a.target"),
        "stale filter keeps stale target"
    );
    assert!(
        !stdout(&stale).contains("b.other"),
        "stale filter drops fresh other"
    );
}

// ----------------------------------------------------------------------------
// notes_corrupted_frontmatter — skipped with one diagnostic, query exits 0
// ----------------------------------------------------------------------------

#[test]
fn notes_corrupted_frontmatter_is_skipped_with_diagnostic() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    assert!(
        ctx(root, &["notes", "add", "target", "good note"])
            .status
            .success()
    );
    // A second note file with unparseable frontmatter.
    write(
        root,
        ".context/notes/broken.md",
        "no frontmatter here at all\n",
    );

    let out = ctx(root, &["notes", "list"]);
    assert_eq!(out.status.code(), Some(0), "query still exits 0");
    assert!(stdout(&out).contains("a.target"), "valid note still listed");
    let diag = stderr(&out);
    assert!(
        diag.contains("broken.md"),
        "diagnostic names the bad file: {diag}"
    );
    let lines = diag.lines().filter(|l| l.contains("broken.md")).count();
    assert_eq!(lines, 1, "exactly one diagnostic line: {diag}");
}

// ----------------------------------------------------------------------------
// notes_merge_conflict — R14: divergent note copies conflict, nothing else
// ----------------------------------------------------------------------------

#[test]
fn notes_merge_conflict_only_on_the_note_file() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    git_init(root);
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);
    assert!(
        ctx(root, &["notes", "add", "target", "original line"])
            .status
            .success()
    );

    let note = note_files(root);
    assert_eq!(note.len(), 1);
    let note_rel = note[0]
        .strip_prefix(root)
        .unwrap()
        .to_string_lossy()
        .to_string();

    assert!(git(root, &["add", "-A"]).status.success());
    assert!(git(root, &["commit", "-qm", "base"]).status.success());

    // Branch with a divergent edit to the same body line.
    assert!(git(root, &["checkout", "-qb", "other"]).status.success());
    let text = std::fs::read_to_string(&note[0]).unwrap();
    std::fs::write(&note[0], text.replace("original line", "OTHER branch line")).unwrap();
    assert!(
        git(root, &["commit", "-aqm", "other edit"])
            .status
            .success()
    );

    // Divergent edit on the first branch.
    let default_branch =
        String::from_utf8(git(root, &["rev-parse", "--abbrev-ref", "HEAD"]).stdout).unwrap();
    let _ = default_branch; // (informational)
    assert!(git(root, &["checkout", "-q", "-"]).status.success());
    let text = std::fs::read_to_string(&note[0]).unwrap();
    std::fs::write(&note[0], text.replace("original line", "MAIN branch line")).unwrap();
    assert!(git(root, &["commit", "-aqm", "main edit"]).status.success());

    // Merge -> conflict on the note file only.
    let merge = git(root, &["merge", "other"]);
    assert!(!merge.status.success(), "merge conflicts");
    let unmerged =
        String::from_utf8(git(root, &["diff", "--name-only", "--diff-filter=U"]).stdout).unwrap();
    let conflicted: Vec<&str> = unmerged.lines().filter(|l| !l.is_empty()).collect();
    assert_eq!(
        conflicted,
        vec![note_rel.as_str()],
        "only the note file conflicts"
    );
}

// ----------------------------------------------------------------------------
// c10_markers_all_surfaces — [notes:2!] on tree/sig/map/at for one symbol
// ----------------------------------------------------------------------------

#[test]
fn c10_markers_all_surfaces_show_fresh_and_stale_note_count() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);

    // One fresh note via the CLI.
    assert!(
        ctx(root, &["notes", "add", "target", "fresh note"])
            .status
            .success()
    );
    let anchor = frontmatter_field(&only_note(root), "anchor_path").unwrap();

    // One stale note written directly with a wrong (never-matching) anchor hash.
    let stale = format!(
        "---\nid: 01STALESTALESTALESTALESTALE\nanchor_path: {anchor}\nanchor_hash: {}\nkind: gotcha\nauthor: unknown\ncreated: 2020-01-01T00:00:00Z\n---\nstale note\n",
        "0".repeat(64)
    );
    write(root, ".context/notes/stale.md", &stale);
    sleep(PAST);

    for (args, label) in [
        (vec!["tree", "a.py"], "tree"),
        (vec!["sig", "target"], "sig"),
        (vec!["map"], "map"),
        (vec!["at", "a.py:2"], "at"),
    ] {
        let out = ctx(root, &args);
        assert!(out.status.success(), "{label} failed: {}", stderr(&out));
        assert!(
            stdout(&out).contains("[notes:2!]"),
            "{label} shows [notes:2!]: {}",
            stdout(&out)
        );
    }
}

// ----------------------------------------------------------------------------
// notes_deletion_freshness — R2: delete indexed file, purge + note goes stale
// ----------------------------------------------------------------------------

#[test]
fn notes_deletion_freshness_purges_symbol_and_stales_note() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", TARGET_PY);
    sleep(PAST);
    init(root);
    assert!(
        ctx(root, &["notes", "add", "target", "note body"])
            .status
            .success()
    );

    // Before deletion: target present.
    let before = ctx(root, &["tree", "a.py"]);
    assert!(
        stdout(&before).contains("target"),
        "target present before delete"
    );

    // Delete the indexed file.
    std::fs::remove_file(root.join("a.py")).unwrap();
    sleep(PAST);

    // Next sync (driven by a query) purges the symbol from ctx tree.
    let after = ctx(root, &["tree", "a.py"]);
    assert!(
        after.status.success(),
        "tree after delete: {}",
        stderr(&after)
    );
    assert!(
        !stdout(&after).contains("target"),
        "symbol purged: {}",
        stdout(&after)
    );
    assert_eq!(
        ctx(root, &["sig", "target"]).status.code(),
        Some(1),
        "sig not found after purge"
    );

    // The note's derived freshness now reads stale (anchor no longer resolves).
    let listed = ctx(root, &["notes", "list", "--stale"]);
    assert!(listed.status.success());
    assert!(
        stdout(&listed).contains("a.target"),
        "note reads stale: {}",
        stdout(&listed)
    );
}
