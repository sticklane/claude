use std::process::Command;

/// `ctx --version` exits 0 and prints a version string (a token beginning with
/// a digit and containing a dot). Asserts structure, not an exact string.
#[test]
fn version_flag_exits_zero_and_prints_version() {
    let out = Command::new(env!("CARGO_BIN_EXE_ctx"))
        .arg("--version")
        .output()
        .expect("run ctx --version");
    assert!(out.status.success(), "exit status was {:?}", out.status);
    let stdout = String::from_utf8(out.stdout).expect("utf8 stdout");
    let has_version_token = stdout
        .split_whitespace()
        .any(|tok| tok.chars().next().is_some_and(|c| c.is_ascii_digit()) && tok.contains('.'));
    assert!(has_version_token, "no version-looking token in {stdout:?}");
}
