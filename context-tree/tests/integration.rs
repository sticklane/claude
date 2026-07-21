//! Cross-subsystem integration tests (task 14). These exercise contracts that
//! genuinely span extraction + query + notes + re-anchoring together — flows no
//! single earlier task's unit tests could cover in isolation. They drive the
//! real `ctx` binary end to end.

use context_tree::sync;
use serde_json::Value;
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

fn ctx_ok(root: &Path, args: &[&str]) -> String {
    let out = ctx(root, args);
    assert!(out.status.success(), "ctx {args:?} failed: {out:?}");
    String::from_utf8(out.stdout).unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

/// `ctx notes list --json` as a vector of note objects (drives a sync first).
fn list_notes(root: &Path) -> Vec<Value> {
    serde_json::from_str(&ctx_ok(root, &["notes", "list", "--json"])).unwrap()
}

fn anchor(n: &Value) -> String {
    n["anchor"].as_str().unwrap().to_string()
}
fn fresh(n: &Value) -> bool {
    n["fresh"].as_bool().unwrap()
}

fn latest_journal(root: &Path) -> Value {
    let text = std::fs::read_to_string(sync::cache_dir(root).join("sync-journal.jsonl")).unwrap();
    let last = text.lines().rfind(|l| !l.trim().is_empty()).unwrap();
    serde_json::from_str(last).unwrap()
}

fn note_files(root: &Path) -> Vec<PathBuf> {
    let dir = root.join(".context/notes");
    let mut v: Vec<PathBuf> = std::fs::read_dir(&dir)
        .unwrap()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("md"))
        .collect();
    v.sort();
    v
}

/// The `anchor_hash:` frontmatter field of the note file whose `anchor_path`
/// contains `symbol`.
fn anchor_hash_for(root: &Path, symbol: &str) -> String {
    for f in note_files(root) {
        let text = std::fs::read_to_string(&f).unwrap();
        let anchors_symbol = text
            .lines()
            .any(|l| l.starts_with("anchor_path:") && l.contains(symbol));
        if anchors_symbol {
            for l in text.lines() {
                if let Some(rest) = l.strip_prefix("anchor_hash:") {
                    return rest.trim().to_string();
                }
            }
        }
    }
    panic!("no note file anchored to {symbol}");
}

// A file with three sibling functions where `middle` carries a mid-function
// syntax error in the BROKEN variant (`x = = =`) while `good_one`/`good_two`
// stay recoverable (R1 best-effort). Byte-identical GOOD form so a repair
// restores the exact C2 body hash and re-derives freshness.
const PF_GOOD: &str = "def good_one():\n    return 1\n\ndef middle():\n    x = 5\n    return x\n\ndef good_two():\n    return 3\n";
const PF_BROKEN: &str = "def good_one():\n    return 1\n\ndef middle():\n    x = = =\n    return 2\n\ndef good_two():\n    return 3\n";

/// Task 14 Step 1: one integration test covering all six mid-edit-robustness
/// sub-assertions across extraction + query + notes + re-anchoring, driven
/// through the full sync+query+notes flow (task 10 unit-tests re-anchoring
/// exclusion in isolation; this test exercises it inside the whole pipeline).
#[test]
fn mid_edit_robustness() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "m.py", PF_GOOD);
    sleep(PAST);

    // Notes on the soon-to-break symbol and on an untouched sibling.
    ctx_ok(root, &["notes", "add", "middle", "broken-symbol note"]);
    ctx_ok(root, &["notes", "add", "good_one", "sibling note"]);
    assert!(
        list_notes(root).iter().all(fresh),
        "both notes fresh at creation"
    );
    let hash_before = anchor_hash_for(root, "middle");

    // Introduce a mid-function syntax error inside `middle`.
    sleep(PAST);
    write(root, "m.py", PF_BROKEN);
    sleep(PAST);

    // (a) sibling symbols in the same file still list via `ctx tree`.
    let tree = ctx_ok(root, &["tree", "m.py"]);
    assert!(
        tree.contains("good_one") && tree.contains("good_two"),
        "recoverable siblings still list under a parse failure: {tree}"
    );

    // (b) `ctx at` on the broken span resolves to the module fallback, no error.
    let at = ctx(root, &["at", "m.py:5", "--json"]);
    assert!(at.status.success(), "at on broken span exits 0: {at:?}");
    let at_v: Value = serde_json::from_str(&stdout(&at)).unwrap();
    let chain = at_v["chain"].as_array().expect("at --json has .chain");
    assert_eq!(
        chain.first().and_then(|e| e["kind"].as_str()),
        Some("module"),
        "broken span falls back to the module surface: {at_v}"
    );

    let broken = list_notes(root);
    // (c) the note anchored to the untouched sibling keeps its freshness.
    let sibling = broken
        .iter()
        .find(|n| anchor(n).contains("good_one"))
        .unwrap();
    assert!(fresh(sibling), "untouched sibling stays fresh: {sibling:?}");

    // (d) no re-anchoring fires for the parse-failed file.
    assert_eq!(
        latest_journal(root)["pending_reanchors"].as_u64(),
        Some(0),
        "no re-anchor attempt against a parse-failed file"
    );

    // (e) the note on the BROKEN symbol reads stale while broken, its anchor
    // binding untouched, and re-derives fresh after repair.
    let broken_note = broken
        .iter()
        .find(|n| anchor(n).contains("middle"))
        .unwrap();
    assert!(
        !fresh(broken_note),
        "broken-symbol note reads stale: {broken_note:?}"
    );
    assert_eq!(
        anchor_hash_for(root, "middle"),
        hash_before,
        "anchor hash binding is never system-rewritten (R13)"
    );

    // (f) repairing the error restores full facts on the next sync.
    sleep(PAST);
    write(root, "m.py", PF_GOOD);
    sleep(PAST);
    let repaired = list_notes(root);
    assert!(
        repaired.iter().all(fresh),
        "both notes re-derive fresh after repair: {repaired:?}"
    );
    let tree2 = ctx_ok(root, &["tree", "m.py"]);
    assert!(
        tree2.contains("good_one") && tree2.contains("middle") && tree2.contains("good_two"),
        "all three symbols list again after repair: {tree2}"
    );
    assert!(
        ctx(root, &["sig", "middle"]).status.success(),
        "the repaired symbol resolves for full facts again"
    );
}

/// Pipe `json` through `jq .`; assert jq exits 0 (parses as JSON).
fn pipe_through_jq(json: &str) {
    let mut child = Command::new("jq")
        .arg(".")
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .expect("jq must be installed for the --json aggregate test");
    child
        .stdin
        .take()
        .unwrap()
        .write_all(json.as_bytes())
        .unwrap();
    assert!(
        child.wait().unwrap().success(),
        "jq rejected the payload: {json}"
    );
}

// A fixture exercising every query verb: `solo` carries a docstring and is
// referenced by `caller`, so tree/sig/map/deps/refs/at all have real payloads.
const JSON_FIXTURE: &str = "def solo():\n    \"\"\"A solo function.\"\"\"\n    return 1\n\n\ndef caller():\n    return solo()\n";

/// Task 14 Step 2: cross-verb `--json` consistency — each of the six query
/// verbs pipes through `jq .` with exit 0 and carries its asserted payload key
/// (tasks 06/07 test this per-command; this is the aggregate consistency check).
#[test]
fn json_all_verbs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "app.py", JSON_FIXTURE);
    sleep(PAST);

    let cases: [(&[&str], &str); 6] = [
        (&["tree", "app.py", "--json"], "symbols"),
        (&["sig", "solo", "--json"], "signature"),
        (&["map", "--json"], "symbols"),
        (&["deps", "app.py", "--json"], "edges"),
        (&["refs", "solo", "--json"], "references"),
        (&["at", "app.py:2", "--json"], "chain"),
    ];
    for (args, key) in cases {
        let out = ctx(root, args);
        assert!(out.status.success(), "ctx {args:?} exits 0: {out:?}");
        let text = stdout(&out);
        pipe_through_jq(&text);
        let v: Value = serde_json::from_str(&text).unwrap();
        assert!(v.get(key).is_some(), "ctx {args:?} carries .{key}: {v}");
    }
}

fn stderr(out: &Output) -> String {
    String::from_utf8(out.stderr.clone()).unwrap()
}

/// specs/ctx-absence-check R1 (task 01): a `sig` no-match prints a three-part
/// boundary output on stderr — the no-match line, the boundary note stating the
/// symbol/text distinction, and a bounded `grep` — with stdout empty and the
/// exit code unchanged (1). A symbol containing `$`/`'` is shell-escaped in the
/// suggested command.
#[test]
fn no_match_text_mode_emits_boundary_note_and_bounded_grep() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "app.py", "def solo():\n    return 1\n");
    sleep(PAST);

    let out = ctx(root, &["sig", "a$b'c"]);
    assert_eq!(
        out.status.code(),
        Some(1),
        "no-match exit code is unchanged: {out:?}"
    );
    assert!(
        stdout(&out).is_empty(),
        "stdout stays empty on a no-match: {:?}",
        stdout(&out)
    );

    let parts: Vec<String> = stderr(&out)
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(str::to_string)
        .collect();
    assert_eq!(
        parts.len(),
        3,
        "exactly three parts on stderr (no-match line, note, grep): {parts:?}"
    );

    assert!(
        parts[0].contains("no symbol matches") && parts[0].contains("a$b'c"),
        "part 1 is the no-match line naming the symbol: {}",
        parts[0]
    );
    let note = parts[1].to_lowercase();
    assert!(
        note.contains("object field")
            && note.contains("json key")
            && note.contains("string literal"),
        "part 2 states that fields/keys/literals are not indexed: {}",
        parts[1]
    );
    let grep = parts[2].trim();
    assert!(
        grep.starts_with("grep -rl"),
        "part 3 is a bounded grep command: {grep}"
    );
    assert!(
        grep.contains("| head -20"),
        "part 3 is bounded by `head -20`: {grep}"
    );
    // POSIX single-quote escaping: wrap in '', inner ' becomes '\'' , and $ is
    // literal inside single quotes — so `a$b'c` renders as `'a$b'\''c'`.
    assert!(
        grep.contains("'a$b'\\''c'"),
        "the `$`/`'` symbol is shell-escaped in the suggested command: {grep}"
    );
}

/// The non-empty stderr lines of a `ctx` invocation, in order.
fn stderr_parts(out: &Output) -> Vec<String> {
    stderr(out)
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(str::to_string)
        .collect()
}

/// Index of the first stderr part that is task 01's boundary note (the
/// fields/keys/literals-not-indexed line), or a panic naming the parts seen.
fn boundary_note_index(parts: &[String]) -> usize {
    parts
        .iter()
        .position(|l| {
            let l = l.to_lowercase();
            l.contains("object field") && l.contains("json key") && l.contains("string literal")
        })
        .unwrap_or_else(|| panic!("boundary note present on stderr: {parts:?}"))
}

/// specs/ctx-absence-check R4 (task 02): a `sig` no-match whose query is a case
/// variant of an indexed symbol lists that near-miss as a "did you mean"
/// candidate BEFORE task 01's boundary note (text mode, on stderr).
#[test]
fn sig_no_match_lists_did_you_mean_before_boundary_note() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    // Only the camelCase `figureBboxes` is indexed; the query is a case variant.
    write(root, "app.py", "def figureBboxes():\n    return 1\n");
    sleep(PAST);

    let out = ctx(root, &["sig", "FigureBboxes"]);
    assert_eq!(
        out.status.code(),
        Some(1),
        "case-variant miss still exits 1: {out:?}"
    );

    let parts = stderr_parts(&out);
    let dym_idx = parts
        .iter()
        .position(|l| l.to_lowercase().contains("did you mean"))
        .unwrap_or_else(|| panic!("a `did you mean` line is present: {parts:?}"));
    let note_idx = boundary_note_index(&parts);
    assert!(
        dym_idx < note_idx,
        "the did-you-mean list precedes the boundary note: {parts:?}"
    );
    // Parse the did-you-mean region (between its header and the note) rather
    // than substring-matching the whole blob.
    let region = parts[dym_idx..note_idx].join(" ");
    assert!(
        region.contains("figureBboxes"),
        "the case-variant candidate is listed: {region}"
    );
}

/// specs/ctx-absence-check R4 (task 02): a `refs` no-match also lists near-miss
/// candidates — the listing lives in the shared no-match path, so both commands
/// get it.
#[test]
fn refs_no_match_lists_did_you_mean_candidates() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "app.py", "def figureBboxes():\n    return 1\n");
    sleep(PAST);

    let out = ctx(root, &["refs", "FigureBboxes"]);
    assert_eq!(
        out.status.code(),
        Some(1),
        "case-variant miss exits 1: {out:?}"
    );

    let parts = stderr_parts(&out);
    let dym_idx = parts
        .iter()
        .position(|l| l.to_lowercase().contains("did you mean"))
        .unwrap_or_else(|| panic!("a `did you mean` line is present: {parts:?}"));
    let note_idx = boundary_note_index(&parts);
    assert!(
        dym_idx < note_idx,
        "did-you-mean precedes the note: {parts:?}"
    );
    assert!(
        parts[dym_idx..note_idx].join(" ").contains("figureBboxes"),
        "the case-variant candidate is listed: {parts:?}"
    );
}

/// specs/ctx-absence-check R4 (task 02): a no-match with no near-miss candidate
/// emits output identical to task 01's baseline — exactly the three parts
/// (no-match line, note, grep) and no "did you mean" line.
#[test]
fn no_match_without_near_miss_omits_did_you_mean() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    ctx_ok(root, &["init"]);
    write(root, "app.py", "def solo():\n    return 1\n");
    sleep(PAST);

    let out = ctx(root, &["sig", "Zzzznonexistent"]);
    assert_eq!(out.status.code(), Some(1), "no-match exits 1: {out:?}");

    let parts = stderr_parts(&out);
    assert!(
        !parts
            .iter()
            .any(|l| l.to_lowercase().contains("did you mean")),
        "no `did you mean` line when nothing is close: {parts:?}"
    );
    assert_eq!(
        parts.len(),
        3,
        "exactly task 01's three parts when there is no near-miss: {parts:?}"
    );
}
