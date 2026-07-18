//! R13 re-anchoring integration tests: the layered algorithm driven through the
//! real `ctx` binary and the sync pipeline, two-phase persistence, durability,
//! and the parse-failed transient guard.

use context_tree::sync;
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms).
const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        fs::create_dir_all(parent).unwrap();
    }
    fs::write(p, content).unwrap();
}

fn ctx(root: &Path, args: &[&str]) -> std::process::Output {
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

/// Drive a sync via a note-read query and return the parsed `notes list --json`.
fn list_notes(root: &Path) -> Vec<Value> {
    let out = ctx_ok(root, &["notes", "list", "--json"]);
    serde_json::from_str(&out).unwrap()
}

/// The single note in a one-note fixture, as its `notes list --json` object.
fn only_note(root: &Path) -> Value {
    let notes = list_notes(root);
    assert_eq!(notes.len(), 1, "expected exactly one note: {notes:?}");
    notes[0].clone()
}

fn latest_journal(root: &Path) -> Value {
    let text = fs::read_to_string(sync::cache_dir(root).join("sync-journal.jsonl")).unwrap();
    let last = text.lines().rfind(|l| !l.trim().is_empty()).unwrap();
    serde_json::from_str(last).unwrap()
}

fn note_files(root: &Path) -> Vec<PathBuf> {
    let dir = root.join(".context/notes");
    let mut v: Vec<PathBuf> = fs::read_dir(&dir)
        .unwrap()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("md"))
        .collect();
    v.sort();
    v
}

fn only_note_file_text(root: &Path) -> String {
    let files = note_files(root);
    assert_eq!(files.len(), 1, "expected one note file");
    fs::read_to_string(&files[0]).unwrap()
}

fn anchor(n: &Value) -> String {
    n["anchor"].as_str().unwrap().to_string()
}
fn fresh(n: &Value) -> bool {
    n["fresh"].as_bool().unwrap()
}
fn file_of(n: &Value) -> String {
    n["file"].as_str().unwrap_or("").to_string()
}

fn copy_tree(src: &Path, dst: &Path) {
    fs::create_dir_all(dst).unwrap();
    for entry in fs::read_dir(src).unwrap().flatten() {
        let from = entry.path();
        let to = dst.join(entry.file_name());
        if from.is_dir() {
            copy_tree(&from, &to);
        } else {
            fs::copy(&from, &to).unwrap();
        }
    }
}

// ---------------------------------------------------------------------------
// leg (a): rename a function in-file → re-anchored immediately, fresh, note
// file unchanged until a persistence point.
// ---------------------------------------------------------------------------
#[test]
fn reanchor_rename_in_file() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    // A rename must preserve the body verbatim so the C2 hash is identical.
    write(root, "m.py", "def foo():\n    return 41 + 1\n");
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "foo", "leg-a note"]);
    let before = only_note(root);
    assert!(fresh(&before), "note fresh at creation: {before:?}");
    assert!(anchor(&before).ends_with(".foo"));

    // Rename foo → bar in place (body byte-identical).
    sleep(PAST);
    write(root, "m.py", "def bar():\n    return 41 + 1\n");
    let after = only_note(root);

    assert!(
        anchor(&after).ends_with(".bar"),
        "re-anchored to the renamed symbol: {after:?}"
    );
    assert!(
        fresh(&after),
        "rename preserves the body hash → fresh: {after:?}"
    );
    assert_eq!(file_of(&after), "m.py");
    // Phase 2 has not run: the note FILE still names the old anchor.
    let text = only_note_file_text(root);
    assert!(
        text.contains("anchor_path:")
            && text.contains("foo")
            && !text.contains("anchor_path: m.bar"),
        "note file anchor unchanged until a persistence point: {text}"
    );
}

// ---------------------------------------------------------------------------
// leg (b): edit the body (no rename/move) → stale, anchor unchanged, no pending.
// ---------------------------------------------------------------------------
#[test]
fn reanchor_body_edit() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "m.py", "def foo():\n    return 1\n");
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "foo", "leg-b note"]);
    let before = only_note(root);
    assert!(fresh(&before));
    let a0 = anchor(&before);

    // Edit the body only.
    sleep(PAST);
    write(root, "m.py", "def foo():\n    return 999\n");
    let after = only_note(root);

    assert!(!fresh(&after), "a body edit reads stale: {after:?}");
    assert_eq!(anchor(&after), a0, "anchor unchanged (still resolves)");
    assert_eq!(file_of(&after), "m.py", "pointer to what changed present");
    assert_eq!(
        latest_journal(root)["pending_reanchors"].as_u64(),
        Some(0),
        "a non-move body edit is not a re-anchor"
    );
    let text = only_note_file_text(root);
    assert!(text.contains("leg-b note"), "body preserved");
}

// ---------------------------------------------------------------------------
// leg (c): move + rename + small body edit → tree-diff re-anchor, stale,
// pending_reanchors >= 1 before persistence.
// ---------------------------------------------------------------------------
const C_ORIG: &str =
    "def foo():\n    total = 0\n    for i in range(10):\n        total += i\n    return total\n";
const C_MOVED: &str =
    "def bar():\n    total = 0\n    for i in range(11):\n        total += i\n    return total\n";

#[test]
fn reanchor_move_rename_edit() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "a.py", C_ORIG);
    write(root, "keep.py", "def keep():\n    return 0\n");
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "foo", "leg-c note"]);
    assert!(fresh(&only_note(root)));

    // Move foo out of a.py into b.py, renamed to bar with a one-token body edit.
    sleep(PAST);
    write(root, "a.py", "def other():\n    return 7\n");
    write(root, "b.py", C_MOVED);
    let after = only_note(root);

    assert!(
        anchor(&after).ends_with(".bar"),
        "tree-diff re-anchors to the moved+renamed symbol: {after:?}"
    );
    assert_eq!(file_of(&after), "b.py");
    assert!(!fresh(&after), "the body edit leaves it stale: {after:?}");
    assert!(
        latest_journal(root)["pending_reanchors"].as_u64().unwrap() >= 1,
        "a pending unwritten re-anchor is journaled before persistence"
    );
    let text = only_note_file_text(root);
    assert!(
        text.contains("foo") && !text.contains("anchor_path: b.bar"),
        "note file unchanged"
    );
}

// ---------------------------------------------------------------------------
// leg (d): move without rename/edit. C (file-is-module) re-anchors via
// qualified-name; Go (module = package) keeps identity with NO pending write.
// ---------------------------------------------------------------------------
#[test]
fn reanchor_move_no_edit() {
    // --- C fixture: module component changes with the file → re-anchor. ---
    let cdir = tempfile::tempdir().unwrap();
    let croot = cdir.path();
    ctx_ok(croot, &["init"]);
    write(croot, "a.c", "int foo(void) {\n    return 1;\n}\n");
    write(croot, "keep.c", "int keep(void) {\n    return 0;\n}\n");
    sleep(PAST);
    ctx_ok(croot, &["notes", "add", "foo", "c note"]);
    assert!(fresh(&only_note(croot)));

    sleep(PAST);
    write(croot, "a.c", "int other(void) {\n    return 2;\n}\n");
    write(croot, "b.c", "int foo(void) {\n    return 1;\n}\n");
    let c_after = only_note(croot);
    assert!(
        anchor(&c_after).ends_with(".foo"),
        "still names foo: {c_after:?}"
    );
    assert!(
        anchor(&c_after).starts_with("b."),
        "module moved a.->b.: {c_after:?}"
    );
    assert!(
        fresh(&c_after),
        "no edit → fresh after re-anchor: {c_after:?}"
    );
    assert_eq!(file_of(&c_after), "b.c");
    assert!(
        latest_journal(croot)["pending_reanchors"].as_u64().unwrap() >= 1,
        "the C re-anchor is a pending write"
    );

    // --- Go fixture: package module survives the move → identity stable. ---
    let gdir = tempfile::tempdir().unwrap();
    let groot = gdir.path();
    ctx_ok(groot, &["init"]);
    write(
        groot,
        "a.go",
        "package pkg\n\nfunc Foo() int {\n\treturn 1\n}\n",
    );
    write(
        groot,
        "keep.go",
        "package pkg\n\nfunc Keep() int {\n\treturn 0\n}\n",
    );
    sleep(PAST);
    ctx_ok(groot, &["notes", "add", "Foo", "go note"]);
    let g_before = only_note(groot);
    assert!(fresh(&g_before));
    let g_anchor = anchor(&g_before);

    sleep(PAST);
    write(
        groot,
        "a.go",
        "package pkg\n\nfunc Other() int {\n\treturn 2\n}\n",
    );
    write(
        groot,
        "b.go",
        "package pkg\n\nfunc Foo() int {\n\treturn 1\n}\n",
    );
    let g_after = only_note(groot);
    assert_eq!(
        anchor(&g_after),
        g_anchor,
        "package identity survives the move"
    );
    assert!(
        fresh(&g_after),
        "identity-stable move stays fresh: {g_after:?}"
    );
    assert_eq!(
        file_of(&g_after),
        "b.go",
        "only the query-reported file updates"
    );
    assert_eq!(
        latest_journal(groot)["pending_reanchors"].as_u64(),
        Some(0),
        "an identity-stable move has NO pending write"
    );
}

// ---------------------------------------------------------------------------
// `ctx sync --write-anchors`: phase 2 writes the re-anchored path into the note
// file; a subsequent sync journals pending_reanchors == 0.
// ---------------------------------------------------------------------------
#[test]
fn write_anchors() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "m.py", "def foo():\n    return 41 + 1\n");
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "foo", "wa note"]);

    // Rename → pending re-anchor (leg a).
    sleep(PAST);
    write(root, "m.py", "def bar():\n    return 41 + 1\n");
    let after = only_note(root);
    assert!(anchor(&after).ends_with(".bar"));
    assert!(latest_journal(root)["pending_reanchors"].as_u64().unwrap() >= 1);
    assert!(only_note_file_text(root).contains("foo"));

    // Phase 2.
    ctx_ok(root, &["sync", "--write-anchors"]);
    let text = only_note_file_text(root);
    assert!(
        text.contains("anchor_path:") && text.contains("bar"),
        "the re-anchored path is persisted to frontmatter: {text}"
    );

    // A subsequent sync sees no pending writes.
    sleep(PAST);
    ctx_ok(root, &["notes", "list"]);
    assert_eq!(
        latest_journal(root)["pending_reanchors"].as_u64(),
        Some(0),
        "no pending writes remain after --write-anchors"
    );
    assert!(fresh(&only_note(root)), "still fresh after persistence");
}

// ---------------------------------------------------------------------------
// Durability: after --write-anchors persisted leg (c), the note survives a cache
// rebuild and a fresh clone, resolving to the new symbol and reading stale.
// ---------------------------------------------------------------------------
#[test]
fn reanchor_durability() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "a.py", C_ORIG);
    write(root, "keep.py", "def keep():\n    return 0\n");
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "foo", "dur note"]);

    sleep(PAST);
    write(root, "a.py", "def other():\n    return 7\n");
    write(root, "b.py", C_MOVED);
    let after = only_note(root);
    assert!(anchor(&after).ends_with(".bar") && !fresh(&after));
    ctx_ok(root, &["sync", "--write-anchors"]);

    // (1) cache-rebuild durability.
    fs::remove_dir_all(root.join(".context/cache")).unwrap();
    sleep(PAST);
    let rebuilt = only_note(root);
    assert!(
        anchor(&rebuilt).ends_with(".bar"),
        "resolves to new symbol after rebuild: {rebuilt:?}"
    );
    assert_eq!(file_of(&rebuilt), "b.py");
    assert!(
        !fresh(&rebuilt),
        "still stale after rebuild (hash never system-written)"
    );

    // (2) fresh-clone durability.
    let clone_dir = tempfile::tempdir().unwrap();
    let clone = clone_dir.path().join("proj");
    copy_tree(root, &clone);
    fs::remove_dir_all(clone.join(".context/cache")).ok();
    sleep(PAST);
    let cloned = only_note(&clone);
    assert!(
        anchor(&cloned).ends_with(".bar"),
        "clone resolves to new symbol: {cloned:?}"
    );
    assert!(!fresh(&cloned), "clone reads stale");
}

// ---------------------------------------------------------------------------
// Parse-failed exclusion: a symbol in a file with a mid-function syntax error is
// unresolved-transient — no re-anchor fires, binding untouched, fresh on repair.
// ---------------------------------------------------------------------------
const PF_GOOD: &str = "def good_one():\n    return 1\n\ndef middle():\n    x = 5\n    return x\n\ndef good_two():\n    return 3\n";
const PF_BROKEN: &str = "def good_one():\n    return 1\n\ndef middle():\n    x = = =\n    return 2\n\ndef good_two():\n    return 3\n";

#[test]
fn reanchor_parse_failed_excluded() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "m.py", PF_GOOD);
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "good_one", "sibling note"]);
    ctx_ok(root, &["notes", "add", "middle", "broken note"]);

    let notes = list_notes(root);
    assert_eq!(notes.len(), 2);
    assert!(notes.iter().all(fresh), "both fresh at creation: {notes:?}");

    // Introduce a mid-function syntax error in `middle`.
    sleep(PAST);
    write(root, "m.py", PF_BROKEN);
    let broken = list_notes(root);
    let sibling = broken
        .iter()
        .find(|n| anchor(n).contains("good_one"))
        .unwrap();
    assert!(
        fresh(sibling),
        "the untouched sibling keeps its freshness: {sibling:?}"
    );
    // The broken-symbol note reads stale and its binding is untouched (never
    // re-anchored to a sibling).
    let broken_note = broken.iter().find(|n| !fresh(n)).unwrap();
    assert!(
        anchor(broken_note).contains("middle"),
        "the broken anchor binding is untouched, not re-anchored: {broken_note:?}"
    );
    assert_eq!(
        latest_journal(root)["pending_reanchors"].as_u64(),
        Some(0),
        "no re-anchor attempt fires against a parse-failed file"
    );

    // Repair the file → the broken note re-derives fresh.
    sleep(PAST);
    write(root, "m.py", PF_GOOD);
    let repaired = list_notes(root);
    assert!(
        repaired.iter().all(fresh),
        "freshness re-derives on repair: {repaired:?}"
    );
}

// ---------------------------------------------------------------------------
// Invariant: the system's only note-file write is the anchor path at a
// persistence point; query/background syncs leave tracked note files byte-identical.
// ---------------------------------------------------------------------------
#[test]
fn reanchor_only_writes_anchor_path() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "m.py", "def foo():\n    return 41 + 1\n");
    sleep(PAST);
    ctx_ok(root, &["notes", "add", "foo", "invariant note"]);
    let original = only_note_file_text(root);

    // Rename → re-anchor pending. Several query/background syncs must NOT touch
    // the tracked note file.
    sleep(PAST);
    write(root, "m.py", "def bar():\n    return 41 + 1\n");
    ctx_ok(root, &["notes", "list"]);
    ctx_ok(root, &["notes", "list", "--json"]);
    ctx_ok(root, &["sig", "bar"]);
    assert_eq!(
        only_note_file_text(root),
        original,
        "query/background syncs leave the note file byte-identical"
    );

    // Only --write-anchors writes, and it changes only the anchor_path line.
    ctx_ok(root, &["sync", "--write-anchors"]);
    let written = only_note_file_text(root);
    assert_ne!(
        written, original,
        "the persistence point wrote the anchor path"
    );

    let orig_lines: Vec<&str> = original.lines().collect();
    let new_lines: Vec<&str> = written.lines().collect();
    assert_eq!(orig_lines.len(), new_lines.len(), "no lines added/removed");
    let changed: Vec<usize> = orig_lines
        .iter()
        .zip(&new_lines)
        .enumerate()
        .filter(|(_, (a, b))| a != b)
        .map(|(i, _)| i)
        .collect();
    assert_eq!(changed.len(), 1, "exactly one line changed");
    assert!(
        new_lines[changed[0]]
            .trim_start()
            .starts_with("anchor_path:"),
        "the only changed line is the anchor path: {:?}",
        new_lines[changed[0]]
    );
    // The body is never modified.
    assert!(written.contains("invariant note"), "body preserved");
}
