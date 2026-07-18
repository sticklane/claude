//! R11 / task 08 integration tests for optional, additive LSP enrichment.
//!
//! `refs_no_lsp` is the regression guard: with no enrichment cache, `ctx refs`
//! still returns `heuristic` results and exits 0 (task 07's baseline). It always
//! runs.
//!
//! `refs_lsp_precise` drives the full enrich -> cache -> `ctx refs` pipeline
//! through a test double for "a configured language server available" and asserts
//! a `precise` result appears. It is deterministic and always runs.
//!
//! `refs_lsp_precise_live` exercises the same pipeline against a real
//! `rust-analyzer`. rust-analyzer is a slow external dependency, so — per the
//! project's TDD rules ("mock only slow/external dependencies") — it is
//! `#[ignore]`d out of the default suite and run explicitly with
//! `cargo test refs_lsp_precise_live -- --ignored`.

use context_tree::lsp::client::RustAnalyzerResolver;
use context_tree::lsp::{ReferenceResolver, ResolveTarget, Resolved, enrich};
use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

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

/// A test double for "a configured language server available": it confirms every
/// heuristic candidate as precise and attaches a signature — the deterministic
/// stand-in the enrichment trait was designed to admit.
struct FakeServer;

impl ReferenceResolver for FakeServer {
    fn resolve(&self, _root: &Path, target: &ResolveTarget) -> std::io::Result<Resolved> {
        Ok(Resolved {
            refs: target.candidates.clone(),
            signature: Some(format!("resolved:{}", target.name)),
        })
    }
}

#[test]
fn refs_no_lsp() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    // No enrichment cache exists: results are heuristic and the command exits 0.
    let out = ctx(root, &["refs", "target"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "refs exits 0 with no LSP: {out:?}"
    );
    let text = stdout(&out);
    assert!(
        text.contains("heuristic"),
        "results stay heuristic with no server configured: {text}"
    );
    assert!(
        !text.contains("precise"),
        "nothing is precise without enrichment: {text}"
    );
}

#[test]
fn refs_lsp_precise() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    // Run the enrichment pass with a configured server (the test double).
    let cache = enrich(root, &FakeServer).expect("enrichment writes a cache");
    assert!(!cache.is_empty(), "the pass recorded precise data");

    // ctx refs now consults the cache and upgrades a result to precise.
    let out = ctx(root, &["refs", "target"]);
    assert_eq!(out.status.code(), Some(0), "refs still exits 0: {out:?}");
    let text = stdout(&out);
    assert!(
        text.contains("precise"),
        "with a configured server, at least one result is precise: {text}"
    );
    assert!(
        text.lines()
            .any(|l| l.starts_with("ref") && l.contains("precise")),
        "the reference is upgraded to precise: {text}"
    );
}

#[test]
fn enrich_load_roundtrips_precise_refs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    enrich(root, &FakeServer).unwrap();
    let loaded = context_tree::lsp::EnrichmentCache::load(root).expect("cache loads back");
    assert!(
        loaded.is_precise("target", "app.py", 6),
        "the call-site reference (app.py:6) is recorded precise: {loaded:?}"
    );
    assert_eq!(
        loaded.signature("app.target"),
        Some("resolved:target"),
        "the resolved signature is stored under the symbol's qpath: {loaded:?}"
    );
}

/// Live end-to-end against a real rust-analyzer. `#[ignore]`d out of the default
/// suite (slow external dependency); run with `-- --ignored`.
#[test]
#[ignore]
fn refs_lsp_precise_live() {
    if !RustAnalyzerResolver::available() {
        eprintln!(
            "SKIP refs_lsp_precise_live: no language server ({}) on PATH",
            RustAnalyzerResolver::server_binary()
        );
        return;
    }
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "Cargo.toml",
        "[package]\nname = \"fixture\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[[bin]]\nname = \"fixture\"\npath = \"src/main.rs\"\n",
    );
    write(
        root,
        "src/main.rs",
        "fn target() -> i32 {\n    1\n}\n\nfn main() {\n    let _ = target();\n    let _ = target();\n}\n",
    );
    sleep(PAST);
    init(root);

    let cache = enrich(root, &RustAnalyzerResolver).expect("enrichment runs");
    assert!(
        !cache.is_empty(),
        "rust-analyzer confirmed at least one precise reference"
    );

    let out = ctx(root, &["refs", "target"]);
    assert_eq!(out.status.code(), Some(0), "refs exits 0: {out:?}");
    let text = stdout(&out);
    assert!(
        text.contains("precise"),
        "with rust-analyzer available, a result is precise: {text}"
    );
}
