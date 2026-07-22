//! Zone-tagging integration goldens (spec `ctx-dead-code-zones`, task 02 / R1).
//! `refs`, `tree`, and `map` annotate any result whose defining file path
//! matches a `.ctxzones` glob: text output appends `[zone:<label>]` to that
//! result's line, and `--json` adds a `zone` field. Results not in any zone are
//! untouched, and with zero `.ctxzones` the output is byte-identical to today
//! (no `[zone:` marker in text, no `zone` key in JSON).

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

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

/// A fixture whose symbol `target` is defined in a live file and referenced from
/// both a live file and an in-zone (`attic/`) file, with a `.ctxzones` mapping
/// `archived: attic/`. `with_zones=false` omits the config for the zero-config
/// control.
fn fixture(root: &Path, with_zones: bool) {
    write(
        root,
        "src/live.py",
        "def target():\n    return 1\n\n\ndef caller_live():\n    return target()\n",
    );
    write(
        root,
        "attic/old.py",
        "def caller_dead():\n    return target()\n",
    );
    if with_zones {
        write(root, ".ctxzones", "archived: attic/\n");
    }
    sleep(PAST);
    init(root);
}

/// Find the array-element object whose `key` field equals `val`.
fn find_by<'a>(arr: &'a [Value], key: &str, val: &str) -> &'a Value {
    arr.iter()
        .find(|o| o.get(key).and_then(Value::as_str) == Some(val))
        .unwrap_or_else(|| panic!("no element with {key}={val} in {arr:?}"))
}

// ---------------------------------------------------------------------------
// refs
// ---------------------------------------------------------------------------

#[test]
fn refs_text_tags_in_zone_ref_leaves_live_untagged() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, true);

    let out = ctx(root, &["refs", "target"]);
    assert_eq!(out.status.code(), Some(0), "refs exits 0: {out:?}");
    let text = stdout(&out);

    // The reference from the in-zone attic/ file ends with the zone marker.
    let dead_line = text
        .lines()
        .find(|l| l.starts_with("ref") && l.contains("attic/old.py"))
        .unwrap_or_else(|| panic!("no in-zone ref line: {text}"));
    assert!(
        dead_line.trim_end().ends_with("[zone:archived]"),
        "in-zone ref line ends with the zone marker: {dead_line}"
    );

    // The live definition line carries no zone marker.
    let def_line = text
        .lines()
        .find(|l| l.starts_with("def") && l.contains("src/live.py"))
        .unwrap_or_else(|| panic!("no def line: {text}"));
    assert!(
        !def_line.contains("[zone:"),
        "live def line has no zone marker: {def_line}"
    );
}

#[test]
fn refs_json_adds_zone_field_only_to_in_zone_results() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, true);

    let out = ctx(root, &["refs", "target", "--json"]);
    assert_eq!(out.status.code(), Some(0), "refs --json exits 0: {out:?}");
    let v: Value = serde_json::from_str(&stdout(&out)).unwrap();

    let refs = v["references"].as_array().unwrap();
    let dead = find_by(refs, "file", "attic/old.py");
    assert_eq!(
        dead.get("zone").and_then(Value::as_str),
        Some("archived"),
        "in-zone reference object has zone=archived: {dead}"
    );
    let live = find_by(refs, "file", "src/live.py");
    assert!(
        live.get("zone").is_none(),
        "live reference object has no zone key: {live}"
    );

    let defs = v["definitions"].as_array().unwrap();
    let def = find_by(defs, "file", "src/live.py");
    assert!(
        def.get("zone").is_none(),
        "live definition object has no zone key: {def}"
    );
}

// ---------------------------------------------------------------------------
// tree
// ---------------------------------------------------------------------------

#[test]
fn tree_text_tags_in_zone_file_header_leaves_live_untagged() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, true);

    let dead = stdout(&ctx(root, &["tree", "attic"]));
    let header = dead
        .lines()
        .find(|l| l.contains("attic/old.py"))
        .unwrap_or_else(|| panic!("no attic file header: {dead}"));
    assert!(
        header.trim_end().ends_with("[zone:archived]"),
        "in-zone file header ends with the zone marker: {header}"
    );

    let live = stdout(&ctx(root, &["tree", "src"]));
    assert!(
        !live.contains("[zone:"),
        "live tree carries no zone marker: {live}"
    );
}

#[test]
fn tree_json_adds_zone_field_to_in_zone_symbols() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, true);

    let dead: Value =
        serde_json::from_str(&stdout(&ctx(root, &["tree", "attic", "--json"]))).unwrap();
    let syms = dead["symbols"].as_array().unwrap();
    assert!(!syms.is_empty(), "attic tree has symbols: {dead}");
    for s in syms {
        assert_eq!(
            s.get("zone").and_then(Value::as_str),
            Some("archived"),
            "each in-zone symbol object has zone=archived: {s}"
        );
    }

    let live: Value =
        serde_json::from_str(&stdout(&ctx(root, &["tree", "src", "--json"]))).unwrap();
    for s in live["symbols"].as_array().unwrap() {
        assert!(
            s.get("zone").is_none(),
            "live symbol object has no zone key: {s}"
        );
    }
}

// ---------------------------------------------------------------------------
// map
// ---------------------------------------------------------------------------

#[test]
fn map_text_tags_in_zone_symbol_leaves_live_untagged() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, true);

    let text = stdout(&ctx(root, &["map"]));
    let dead_line = text
        .lines()
        .find(|l| l.contains("caller_dead"))
        .unwrap_or_else(|| panic!("no caller_dead line: {text}"));
    assert!(
        dead_line.trim_end().ends_with("[zone:archived]"),
        "in-zone map line ends with the zone marker: {dead_line}"
    );
    let live_line = text
        .lines()
        .find(|l| l.contains("caller_live"))
        .unwrap_or_else(|| panic!("no caller_live line: {text}"));
    assert!(
        !live_line.contains("[zone:"),
        "live map line has no zone marker: {live_line}"
    );
}

#[test]
fn map_json_adds_zone_field_only_to_in_zone_symbols() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, true);

    let v: Value = serde_json::from_str(&stdout(&ctx(root, &["map", "--json"]))).unwrap();
    let syms = v["symbols"].as_array().unwrap();
    let dead = syms
        .iter()
        .find(|s| {
            s["qpath"]
                .as_str()
                .is_some_and(|q| q.contains("caller_dead"))
        })
        .unwrap_or_else(|| panic!("no caller_dead symbol: {v}"));
    assert_eq!(
        dead.get("zone").and_then(Value::as_str),
        Some("archived"),
        "in-zone symbol object has zone=archived: {dead}"
    );
    let live = syms
        .iter()
        .find(|s| {
            s["qpath"]
                .as_str()
                .is_some_and(|q| q.contains("caller_live"))
        })
        .unwrap_or_else(|| panic!("no caller_live symbol: {v}"));
    assert!(
        live.get("zone").is_none(),
        "live symbol object has no zone key: {live}"
    );
}

// ---------------------------------------------------------------------------
// zero-config control: no `.ctxzones` => no tagging anywhere
// ---------------------------------------------------------------------------

#[test]
fn zero_config_leaves_text_and_json_untagged() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    fixture(root, false);

    for args in [
        &["refs", "target"][..],
        &["tree", "attic"][..],
        &["map"][..],
    ] {
        let text = stdout(&ctx(root, args));
        assert!(
            !text.contains("[zone:"),
            "no .ctxzones => no text zone marker for {args:?}: {text}"
        );
    }
    for args in [
        &["refs", "target", "--json"][..],
        &["tree", "attic", "--json"][..],
        &["map", "--json"][..],
    ] {
        let text = stdout(&ctx(root, args));
        assert!(
            !text.contains("\"zone\""),
            "no .ctxzones => no JSON zone key for {args:?}: {text}"
        );
    }
}
