//! `.ctxzones` config-layer tests (spec `ctx-dead-code-zones`, task 01). This
//! task ships the resolver core only — no CLI/renderer wiring yet, so these
//! tests exercise `context_tree::zones::ZoneConfig` directly against a
//! fixture directory rather than through the `ctx` binary.

use context_tree::zones::ZoneConfig;
use std::path::Path;

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

// ---------------------------------------------------------------------------
// Line grammar: `<label>: <glob>` per line; blank and `#` comment lines
// skipped.
// ---------------------------------------------------------------------------

#[test]
fn zone_of_matches_a_declared_label_glob() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        ".ctxzones",
        "# a comment line, and a blank line below\n\narchived: attic/\n",
    );

    let cfg = ZoneConfig::load(root);
    assert_eq!(cfg.zone_of("attic/go-cmd/mloverlay.go"), Some("archived"));
}

#[test]
fn declared_labels_lists_every_label_in_declaration_order_deduped() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        ".ctxzones",
        "archived: attic/\ngenerated: dist/\narchived: legacy/\n",
    );

    let cfg = ZoneConfig::load(root);
    assert_eq!(cfg.declared_labels(), vec!["archived", "generated"]);
}

// ---------------------------------------------------------------------------
// The same label on multiple lines unions its globs.
// ---------------------------------------------------------------------------

#[test]
fn same_label_on_multiple_lines_unions_its_globs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, ".ctxzones", "archived: attic/\narchived: legacy/\n");

    let cfg = ZoneConfig::load(root);
    assert_eq!(cfg.zone_of("attic/x.go"), Some("archived"));
    assert_eq!(cfg.zone_of("legacy/y.go"), Some("archived"));
}

// ---------------------------------------------------------------------------
// When two different labels both match one path, the first line in file
// order wins (a path carries a single tag).
// ---------------------------------------------------------------------------

#[test]
fn first_matching_line_wins_when_two_labels_match_one_path() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    // Both globs match the same path; "archived" is declared first.
    write(
        root,
        ".ctxzones",
        "archived: attic/**\ngenerated: attic/**\n",
    );

    let cfg = ZoneConfig::load(root);
    assert_eq!(cfg.zone_of("attic/gen/out.go"), Some("archived"));
}

// ---------------------------------------------------------------------------
// zone_of on a path matching no glob returns None.
// ---------------------------------------------------------------------------

#[test]
fn zone_of_returns_none_for_a_path_matching_no_glob() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, ".ctxzones", "archived: attic/\n");

    let cfg = ZoneConfig::load(root);
    assert_eq!(cfg.zone_of("src/live.go"), None);
}

// ---------------------------------------------------------------------------
// Zero `.ctxzones` file -> declared_labels() empty, all zone_of None.
// ---------------------------------------------------------------------------

#[test]
fn absent_ctxzones_file_yields_zero_zones() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();

    let cfg = ZoneConfig::load(root);
    assert!(cfg.declared_labels().is_empty());
    assert_eq!(cfg.zone_of("attic/anything.go"), None);
    assert_eq!(cfg.zone_of("src/live.go"), None);
}

// ---------------------------------------------------------------------------
// A malformed line (no `:` separator, or an out-of-charset label) is skipped
// rather than aborting the load. Defined behavior: the load never errors —
// bad lines are dropped and every well-formed line still loads.
// ---------------------------------------------------------------------------

#[test]
fn malformed_lines_are_skipped_not_fatal() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        ".ctxzones",
        "this line has no colon\nArchived_Caps: attic/\narchived: attic/\n",
    );

    let cfg = ZoneConfig::load(root);
    // The out-of-charset label ("Archived_Caps", uppercase + underscore) and
    // the no-separator line are both dropped; the well-formed line after them
    // still loads.
    assert_eq!(cfg.declared_labels(), vec!["archived"]);
    assert_eq!(cfg.zone_of("attic/x.go"), Some("archived"));
}

// ---------------------------------------------------------------------------
// Basename-vs-full-path semantics match `.ctxignore`'s: a glob without `/`
// matches the basename; a directory glob (trailing `/`) matches a path
// prefix.
// ---------------------------------------------------------------------------

#[test]
fn basename_glob_matches_files_anywhere_by_name() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, ".ctxzones", "generated: *.pb.go\n");

    let cfg = ZoneConfig::load(root);
    assert_eq!(cfg.zone_of("pkg/api/thing.pb.go"), Some("generated"));
    assert_eq!(cfg.zone_of("pkg/api/thing.go"), None);
}
