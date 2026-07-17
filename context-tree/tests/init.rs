use std::fs;
use std::path::Path;
use std::process::Command;
use tempfile::tempdir;

fn run_init(dir: &Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_ctx"))
        .arg("init")
        .current_dir(dir)
        .output()
        .expect("run ctx init")
}

#[test]
fn init_scaffolds_context_layout() {
    let tmp = tempdir().unwrap();
    let out = run_init(tmp.path());
    assert!(out.status.success(), "ctx init should exit 0");

    let ctx = tmp.path().join(".context");
    assert!(ctx.join("notes").is_dir(), "notes/ missing");
    assert!(ctx.join("cache").is_dir(), "cache/ missing");

    let gi = fs::read_to_string(ctx.join(".gitignore")).expect("managed .gitignore");
    assert!(
        gi.lines().any(|l| l.trim() == "cache/"),
        "managed .gitignore must ignore cache/: {gi:?}"
    );

    // notes/ and cache/ scaffold empty, ready for VCS tracking / derived state.
    assert_eq!(fs::read_dir(ctx.join("notes")).unwrap().count(), 0);
    assert_eq!(fs::read_dir(ctx.join("cache")).unwrap().count(), 0);
}

#[test]
fn init_is_idempotent_second_run_changes_nothing() {
    let tmp = tempdir().unwrap();
    assert!(run_init(tmp.path()).status.success());

    let ctx = tmp.path().join(".context");
    let gitignore = ctx.join(".gitignore");
    let gi_before = fs::read_to_string(&gitignore).unwrap();
    let mtime_before = fs::metadata(&gitignore).unwrap().modified().unwrap();

    let out = run_init(tmp.path());
    assert!(out.status.success(), "idempotent re-run should exit 0");

    let gi_after = fs::read_to_string(&gitignore).unwrap();
    assert_eq!(gi_before, gi_after, "gitignore content changed on re-run");
    let mtime_after = fs::metadata(&gitignore).unwrap().modified().unwrap();
    assert_eq!(
        mtime_before, mtime_after,
        "managed .gitignore was rewritten on an idempotent re-run"
    );
    assert!(ctx.join("notes").is_dir());
    assert!(ctx.join("cache").is_dir());
}
