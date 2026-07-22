//! Zone-filtering integration goldens (spec `ctx-dead-code-zones`, task 03 /
//! R2, R3). `refs` and `map` gain two composable, mutually-exclusive-per-
//! invocation filters over the already-resolved result set: `--zone <label>`
//! keeps only in-that-zone results; `--live-only` excludes every zoned result.
//! An undeclared `--zone` label errors (exit 2) listing the declared labels.
//! Crucially, `refs <sym> --live-only` that filters away every reference of a
//! symbol whose references are ALL in-zone emits a one-line
//! `N references exist only in zones: <labels>` tail (stderr in text mode, a
//! `note` field in `--json`) and exits 0 — it is the R3 liveness primitive and
//! must NOT be misread as the `no_match` boundary (resolution succeeded; only
//! filtering emptied the set).

use serde_json::Value;
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

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

/// A fixture whose symbol `dead_only` is defined in a live file and referenced
/// ONLY from an in-zone (`attic/`) file, with a `.ctxzones` mapping
/// `archived: attic/`. This is the R3 "only kept alive by dead code" shape: the
/// symbol resolves, but every one of its references lives in a zone. `target` is
/// a companion symbol referenced from BOTH a live and an in-zone file, used for
/// the mixed-result `--zone` / `--live-only` goldens.
fn fixture(root: &Path) {
    write(
        root,
        "src/live.py",
        "def target():\n    return 1\n\n\ndef dead_only():\n    return 2\n\n\n\
         def caller_live():\n    return target()\n",
    );
    write(
        root,
        "attic/old.py",
        "def caller_dead():\n    return target() + dead_only()\n",
    );
    write(root, ".ctxzones", "archived: attic/\n");
    sleep(PAST);
    init(root);
}

/// Find the array-element object whose `key` field equals `val`.
fn find_by<'a>(arr: &'a [Value], key: &str, val: &str) -> Option<&'a Value> {
    arr.iter()
        .find(|o| o.get(key).and_then(Value::as_str) == Some(val))
}

// ---------------------------------------------------------------------------
// refs: plain (baseline — the in-zone ref is present and tagged)
// ---------------------------------------------------------------------------

#[test]
fn refs_plain_shows_in_zone_refs_exit_zero() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "dead_only"]);
    assert_eq!(out.status.code(), Some(0), "plain refs exits 0: {out:?}");
    let text = stdout(&out);
    let dead_line = text
        .lines()
        .find(|l| l.starts_with("ref") && l.contains("attic/old.py"))
        .unwrap_or_else(|| panic!("no in-zone ref line: {text}"));
    assert!(
        dead_line.trim_end().ends_with("[zone:archived]"),
        "plain refs shows the in-zone ref tagged: {dead_line}"
    );
}

// ---------------------------------------------------------------------------
// refs --live-only: the R3 liveness primitive
// ---------------------------------------------------------------------------

#[test]
fn refs_live_only_all_in_zone_emits_tail_exit_zero_text() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "dead_only", "--live-only"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "live-only filtered-empty still exits 0 (resolution succeeded): {out:?}"
    );
    let text = stdout(&out);
    // No `ref` lines survive — every reference was in a zone.
    assert!(
        !text.lines().any(|l| l.starts_with("ref ")),
        "no ref lines survive live-only when all refs are in-zone: {text}"
    );
    // The one-line tail states the filtered fact on stderr, naming the zone.
    let err = stderr(&out);
    assert!(
        err.contains("references exist only in zones") && err.contains("archived"),
        "stderr tails the zones-only fact naming the zone: {err:?}"
    );
    // It is NOT the no_match boundary output.
    assert!(
        !err.contains("no symbol matches") && !err.contains("Absence of a symbol"),
        "filtered-empty is not the no_match boundary: {err:?}"
    );
}

#[test]
fn refs_live_only_all_in_zone_json_note_not_no_match() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "dead_only", "--live-only", "--json"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "live-only --json exits 0: {out:?}"
    );
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();

    // references empty, a note carries the zones-only fact.
    let refs = v["references"].as_array().unwrap();
    assert!(
        refs.is_empty(),
        "references array is empty under live-only: {v}"
    );
    let note = v
        .get("note")
        .and_then(Value::as_str)
        .unwrap_or_else(|| panic!("live-only --json gains a note field: {v}"));
    assert!(
        note.contains("references exist only in zones") && note.contains("archived"),
        "the note carries the zones-only fact: {note}"
    );
    // NOT the no_match shape.
    assert!(
        v.get("error").is_none(),
        "filtered-empty --json is not the no_match error object: {v}"
    );
    // Legacy keys survive.
    assert!(v.get("symbol").is_some(), "legacy symbol key survives: {v}");
    assert!(
        v.get("definitions").is_some(),
        "legacy definitions key survives: {v}"
    );
}

#[test]
fn refs_live_only_mixed_keeps_live_ref_no_tail() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    // `target` is referenced from a live file AND an in-zone file: live-only
    // keeps the live ref, so no zones-only tail fires.
    let out = ctx(root, &["refs", "target", "--live-only"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "mixed live-only exits 0: {out:?}"
    );
    let text = stdout(&out);
    let live_ref = text
        .lines()
        .find(|l| l.starts_with("ref") && l.contains("src/live.py"))
        .unwrap_or_else(|| panic!("live ref survives live-only: {text}"));
    assert!(
        !live_ref.contains("[zone:"),
        "surviving live ref carries no zone marker: {live_ref}"
    );
    // The in-zone ref is gone.
    assert!(
        !text.contains("attic/old.py"),
        "the in-zone ref is filtered out under live-only: {text}"
    );
    assert!(
        !stderr(&out).contains("references exist only in zones"),
        "no zones-only tail when a live ref survives: {:?}",
        stderr(&out)
    );
}

// ---------------------------------------------------------------------------
// refs --zone <label>
// ---------------------------------------------------------------------------

#[test]
fn refs_zone_keeps_only_in_zone_refs_text() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "target", "--zone", "archived"]);
    assert_eq!(out.status.code(), Some(0), "--zone exits 0: {out:?}");
    let text = stdout(&out);
    // The in-zone ref survives, the live ref does not.
    assert!(
        text.contains("attic/old.py"),
        "--zone archived keeps the in-zone ref: {text}"
    );
    assert!(
        !text
            .lines()
            .any(|l| l.starts_with("ref") && l.contains("src/live.py")),
        "--zone archived drops the live ref: {text}"
    );
}

#[test]
fn refs_zone_keeps_only_in_zone_refs_json() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "target", "--zone", "archived", "--json"]);
    assert_eq!(out.status.code(), Some(0), "--zone --json exits 0: {out:?}");
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();
    let refs = v["references"].as_array().unwrap();
    assert!(
        find_by(refs, "file", "attic/old.py").is_some(),
        "--zone archived keeps the in-zone reference object: {v}"
    );
    assert!(
        find_by(refs, "file", "src/live.py").is_none(),
        "--zone archived drops the live reference object: {v}"
    );
}

#[test]
fn refs_zone_unknown_label_exits_two_lists_declared() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "target", "--zone", "nosuchlabel"]);
    assert_eq!(
        out.status.code(),
        Some(2),
        "an undeclared --zone label exits 2: {out:?}"
    );
    let err = stderr(&out);
    assert!(
        err.contains("archived"),
        "the error lists the declared zone labels: {err:?}"
    );
}

// ---------------------------------------------------------------------------
// Regression: a genuinely missing symbol still hits the no_match seam
// ---------------------------------------------------------------------------

#[test]
fn refs_truly_missing_symbol_still_no_match_boundary() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["refs", "NoSuchSymbol", "--live-only"]);
    assert_eq!(
        out.status.code(),
        Some(1),
        "a truly missing symbol keeps EXIT_NO_MATCH even under a zone flag: {out:?}"
    );
    assert!(
        stderr(&out).contains("no symbol matches"),
        "a genuine no-match keeps the boundary output: {:?}",
        stderr(&out)
    );
}

// ---------------------------------------------------------------------------
// map --live-only / --zone
// ---------------------------------------------------------------------------

#[test]
fn map_live_only_drops_in_zone_symbols_text() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["map", "--live-only"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "map --live-only exits 0: {out:?}"
    );
    let text = stdout(&out);
    assert!(
        text.contains("caller_live"),
        "map --live-only keeps live symbols: {text}"
    );
    assert!(
        !text.contains("caller_dead"),
        "map --live-only drops the in-zone symbol: {text}"
    );
    assert!(
        !text.contains("[zone:"),
        "no zone markers remain once zoned symbols are excluded: {text}"
    );
}

#[test]
fn map_zone_keeps_only_in_zone_symbols_json() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["map", "--zone", "archived", "--json"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "map --zone --json exits 0: {out:?}"
    );
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();
    let syms = v["symbols"].as_array().unwrap();
    assert!(
        syms.iter().any(|s| s["qpath"]
            .as_str()
            .is_some_and(|q| q.contains("caller_dead"))),
        "map --zone archived keeps the in-zone symbol: {v}"
    );
    assert!(
        !syms.iter().any(|s| s["qpath"]
            .as_str()
            .is_some_and(|q| q.contains("caller_live"))),
        "map --zone archived drops the live symbol: {v}"
    );
    // Every surviving symbol carries the zone key.
    for s in syms {
        assert_eq!(
            s.get("zone").and_then(Value::as_str),
            Some("archived"),
            "every surviving --zone symbol is in that zone: {s}"
        );
    }
}

#[test]
fn map_zone_unknown_label_exits_two() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root);

    let out = ctx(root, &["map", "--zone", "nosuchlabel"]);
    assert_eq!(
        out.status.code(),
        Some(2),
        "map with an undeclared --zone label exits 2: {out:?}"
    );
    assert!(
        stderr(&out).contains("archived"),
        "the error lists the declared zone labels: {:?}",
        stderr(&out)
    );
}
