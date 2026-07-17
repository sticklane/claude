//! Mechanical guard for the full 12-language fixture layout (R1 coverage). A
//! future accidental deletion/rename of a language fixture directory fails here
//! loudly rather than silently dropping a language from the coverage set.

use std::collections::BTreeSet;

const FIXTURES: &str = "tests/fixtures/languages";

#[test]
fn all_twelve_language_fixture_dirs_present() {
    let mut dirs: BTreeSet<String> = BTreeSet::new();
    for entry in std::fs::read_dir(FIXTURES).expect("read fixtures dir") {
        let entry = entry.expect("dir entry");
        if entry.file_type().expect("file type").is_dir() {
            dirs.insert(entry.file_name().to_string_lossy().into_owned());
        }
    }
    let expected: BTreeSet<String> = [
        "bash",
        "c",
        "cpp",
        "go",
        "haskell",
        "java",
        "kotlin",
        "ocaml",
        "python",
        "rust",
        "typescript",
        "zig",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect();
    assert_eq!(
        dirs, expected,
        "exact 12-language fixture set must be present"
    );
}

#[test]
fn every_language_dir_holds_at_least_one_source_file() {
    for entry in std::fs::read_dir(FIXTURES).expect("read fixtures dir") {
        let dir = entry.expect("dir entry").path();
        if !dir.is_dir() {
            continue;
        }
        let files = std::fs::read_dir(&dir)
            .expect("read language dir")
            .filter(|e| e.as_ref().map(|e| e.path().is_file()).unwrap_or(false))
            .count();
        assert!(files >= 1, "{dir:?} must hold at least one source file");
    }
}

#[test]
fn typescript_dir_holds_ts_tsx_and_js() {
    let dir = format!("{FIXTURES}/typescript");
    let mut exts: BTreeSet<String> = BTreeSet::new();
    for entry in std::fs::read_dir(&dir).expect("read typescript dir") {
        let path = entry.expect("dir entry").path();
        if let Some(ext) = path.extension() {
            exts.insert(ext.to_string_lossy().into_owned());
        }
    }
    for want in ["ts", "tsx", "js"] {
        assert!(
            exts.contains(want),
            "typescript fixtures must include a .{want} file: {exts:?}"
        );
    }
}
